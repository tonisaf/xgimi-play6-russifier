import hashlib,json,shlex,tempfile,unittest
from pathlib import Path
from installer import MANIFEST
from boot_update import update,recover,PACKAGE

class FakeDevice:
    def __init__(self,logs,helper_digest,mode='reject'):
        self.logs=logs;self.remote='/data/local/tmp/beam-ru-0123456789'
        self.props={'ro.build.fingerprint':MANIFEST['fingerprint'],'ro.serialno':'TEST'}
        self.helper_digest='old-helper';self.new_digest=helper_digest;self.mode=mode
        self.services='other/.Service:'+PACKAGE+'/.StartupBridge';self.events=[];self.offline=False
        self.changed=MANIFEST['overlays'][0];self.overlay_digest='old-overlay'
    def preflight(self): pass
    def overlay_states(self): return {i['package']:{'path':'/data/app/'+i['file'],'enabled':True,'state':'STATE_ENABLED'} for i in MANIFEST['overlays']}
    def shell(self,script,**kwargs):
        if self.offline: raise RuntimeError('offline')
        a=shlex.split(script)
        if a[:2]==['getprop','ro.build.fingerprint']: return MANIFEST['fingerprint']
        if a[:2]==['getprop','ro.serialno']: return 'TEST'
        if a[:2]==['pm','path']: return 'package:/data/app/boot/base.apk'
        if a[0]=='sha256sum':
            if a[1]=='/data/app/boot/base.apk': return self.helper_digest+'  base.apk'
            name=Path(a[1]).name
            return (self.overlay_digest if name==self.changed['file'] else MANIFEST['files'][name])+'  apk'
        if a[:3]==['settings','get','secure']: return self.services
        if a[:3]==['settings','put','secure']: self.services=a[4];return ''
        if a[:3]==['settings','delete','secure']: self.services='';return ''
        return ''
    def root(self,script,tag): self.events.append(('root',script));return ''
    def enable_overlay(self,item,enabled): self.events.append(('enable',item['package'],enabled))
    def command(self,*args,**kwargs):
        self.events.append(args)
        if args[0]=='pull': Path(args[2]).write_bytes(b'old-overlay')
        if args[0]=='install':
            if str(args[-1]).endswith('boot-helper.apk'):
                if self.mode=='lost-success': self.helper_digest=self.new_digest;raise RuntimeError('connection lost after commit')
                if self.mode=='offline': self.offline=True;raise RuntimeError('offline')
                if self.mode=='reject': raise RuntimeError('PackageManager rejected update')
                self.helper_digest=self.new_digest
            elif '-d' in args: self.overlay_digest='old-overlay'
            else: self.overlay_digest=MANIFEST['files'][self.changed['file']]

class BootUpdateTests(unittest.TestCase):
    def fixture(self,directory,mode):
        base=Path(directory);bundle=base/'bundle';bundle.mkdir();logs=base/'logs';logs.mkdir()
        helper=bundle/'boot-helper.apk';helper.write_bytes(b'new-helper');digest=hashlib.sha256(helper.read_bytes()).hexdigest()
        files={}
        for name in ('apply.sh','skin.sh'):
            (bundle/name).write_text('D=/data/local/beam-russifier-boot/releases/'+MANIFEST['version']+'-test\n');files[name]=hashlib.sha256((bundle/name).read_bytes()).hexdigest()
        for name in ('skin.apk','panel.apk',*[x['file'] for x in MANIFEST['runtimePatches']]): files[name]=MANIFEST['files'][name]
        (bundle/'build-info.json').write_text(json.dumps({'directory':'/data/local/beam-russifier-boot/releases/'+MANIFEST['version']+'-test','files':files,'helperSha256':digest}))
        return FakeDevice(logs,digest,mode),bundle
    def test_failed_apk_update_restores_overlay_and_old_service(self):
        with tempfile.TemporaryDirectory() as directory:
            device,bundle=self.fixture(directory,'reject')
            with self.assertRaisesRegex(RuntimeError,'rejected'): update(device,bundle)
            self.assertEqual(device.overlay_digest,'old-overlay');self.assertEqual(device.helper_digest,'old-helper')
            self.assertIn(PACKAGE+'/.StartupBridge',device.services)
            scripts=[e[1] for e in device.events if e[0]=='root']
            self.assertTrue(scripts);self.assertNotIn('/apply.before-battery.sh',''.join(scripts))
            self.assertNotIn('cp /data/local/tmp/beam-battery-apply.sh',''.join(scripts))
            self.assertEqual(json.loads((device.logs/'boot-update.json').read_text())['status'],'rolled-back')
    def test_lost_reply_after_success_does_not_restore_old_overlays(self):
        with tempfile.TemporaryDirectory() as directory:
            device,bundle=self.fixture(directory,'lost-success')
            with self.assertRaisesRegex(RuntimeError,'connection lost'): update(device,bundle)
            self.assertEqual(device.overlay_digest,MANIFEST['files'][device.changed['file']])
            self.assertFalse(any(e[0]=='install' and '-d' in e for e in device.events))
            self.assertEqual(json.loads((device.logs/'boot-update.json').read_text())['status'],'committed')
    def test_disconnection_preserves_journal_and_can_be_recovered(self):
        with tempfile.TemporaryDirectory() as directory:
            device,bundle=self.fixture(directory,'offline')
            with self.assertRaisesRegex(RuntimeError,'offline'): update(device,bundle)
            self.assertNotIn(PACKAGE,device.services)
            self.assertEqual(json.loads((device.logs/'boot-update.json').read_text())['status'],'activation-uncertain')
            device.offline=False;recover(device,device.logs)
            self.assertEqual(device.overlay_digest,'old-overlay');self.assertIn(PACKAGE,device.services)
    def test_recovery_refuses_other_device(self):
        with tempfile.TemporaryDirectory() as directory:
            device,bundle=self.fixture(directory,'reject')
            with self.assertRaises(RuntimeError): update(device,bundle)
            path=device.logs/'boot-update.json';record=json.loads(path.read_text());record['device']['ro.serialno']='OTHER';path.write_text(json.dumps(record))
            events=len(device.events)
            with self.assertRaisesRegex(RuntimeError,'другому устройству'): recover(device,device.logs)
            self.assertEqual(len(device.events),events)
