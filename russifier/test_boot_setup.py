"""Fault injection at delivery boundaries; no projector connection."""
import hashlib,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from types import SimpleNamespace
import boot_setup
from installer import MANIFEST,save,sha,SKIN
from boot_common import PACKAGE,SERVICE,validate_bundle

DEFAULT={'oomadjLimit':[{'pkg':'vendor.keep','start':10,'min':20,'max':30}], 'unrelated':{'value':42}}

class Device:
    def __init__(self,logs,existed,mode):
        self.logs=logs;self.remote='/data/local/tmp/beam-ru-0123456789';self.mode=mode;self.offline=False
        self.props={'ro.build.fingerprint':MANIFEST['fingerprint'],'ro.serialno':'TEST','persist.sys.locale':'ru-RU'}
        self.runtime_hash=MANIFEST['originals']['com.android.newsettings']['sha256']
        self.native_runtime={x['target']:MANIFEST['originals'][x['target']]['sha256'] for x in MANIFEST['runtimePatches']}
        self.raw=(json.dumps(DEFAULT)+'\n').encode();self.policy=self.raw if existed else None
        self.initial_policy=self.policy;self.helper=None;self.services='other/.Service';self.enabled='1'
        self.overlays={x['package']:False for x in MANIFEST['overlays']};self.staged={};self.events=[]
        self.skin='stock.apk';self.mutated=False;self.state=None;self.staging_writable=False
    def preflight(self): self.events.append('preflight')
    def overlay_states(self): return {k:{'path':'/data/app/'+k+'/base.apk' if v else None,'enabled':v} for k,v in self.overlays.items()}
    def shell(self,script,**kwargs):
        import shlex
        if self.offline: raise RuntimeError('offline')
        self.events.append(('shell',script));a=shlex.split(script)
        if a[:2]==['mkdir','-p'] and a[-1]==self.remote+'/generation' and not self.staging_writable:
            raise RuntimeError('mkdir: Permission denied')
        if a[0]=='getprop':
            if a[1]=='persist.sys.xgimi.themeV2.url': return self.skin
            return self.props.get(a[1],'')
        if a[0]=='getenforce': return 'Permissive'
        if a[0]=='df': return '999999999'
        if a[:2]==['pm','path']:
            if a[2]==PACKAGE: return 'package:/data/app/helper.apk' if self.helper else ''
            return 'package:/data/app/'+a[2]+'/base.apk' if self.overlays.get(a[2]) else ''
        if a[0]=='sha256sum':
            if a[1]=='/data/app/helper.apk': return self.helper+' helper.apk'
            pkg=a[1].split('/')[3]
            item=next(x for x in MANIFEST['overlays'] if x['package']==pkg)
            return MANIFEST['files'][item['file']]+' base.apk'
        if a[:3]==['settings','get','secure']: return self.services if a[3]=='enabled_accessibility_services' else self.enabled
        if a[:3]==['settings','put','secure']:
            if a[3]=='enabled_accessibility_services':
                self.services=a[4]
                if self.mode=='service-lost' and PACKAGE in self.services: self.offline=True;raise RuntimeError('lost activation')
            else: self.enabled=a[4]
        if a[:3]==['settings','delete','secure']:
            if a[3]=='enabled_accessibility_services': self.services=''
            else: self.enabled='null'
        return ''
    def command(self,*args,**kwargs):
        if self.offline: raise RuntimeError('offline')
        self.events.append(args)
        if args[0]=='pull': Path(args[2]).write_bytes(self.raw)
        if args[0]=='push': self.staged[args[2]]=Path(args[1]).read_bytes()
        if args[0]=='install':
            if self.mode=='helper-reject': raise RuntimeError('PackageManager rejected')
            self.helper=sha(args[-1])
            if self.mode=='helper-lost': self.offline=True;raise RuntimeError('lost after commit')
        if args[0]=='uninstall': self.helper=None
        return SimpleNamespace(stdout='',returncode=0)
    def root(self,script,tag):
        if self.offline: raise RuntimeError('offline')
        self.events.append(('root',tag,script))
        if tag=='snapshot-oem-policy':
            self.staging_writable=('chown root:shell '+self.remote in script and 'chmod 770 '+self.remote in script)
            return 'exists='+('1' if self.policy is not None else '0')+'\nmetadata=1000:1000:600\ncontext=u:object_r:system_data_file:s0'
        if tag=='apply-oem-policy':
            self.policy=(self.logs/'oem-after.json').read_bytes()
            if self.mode=='policy-lost': self.offline=True;raise RuntimeError('lost policy reply')
        if tag=='read-oem-policy': return hashlib.sha256(self.policy).hexdigest()+' policy' if self.policy is not None else 'absent'
        if tag=='read-oem-policy-json': return self.policy.decode('utf-8')
        if tag=='restore-oem-policy':
            self.policy=self.staged.get(self.remote+'/restore-oem.json') if 'mv ' in script else None
        return ''
    def install(self):
        self.events.append('translation-install')
        self.state={'status':'installed','skinProperty':'stock.apk','mountChanged':True,'nativeMountsChanged':list(self.native_runtime)}
        for pkg in self.overlays: self.overlays[pkg]=True
        self.skin=SKIN;save(self.logs/'state.json',self.state)
        if self.mode=='translation-lost': self.offline=True;raise RuntimeError('lost translation reply')
    def restore(self,immediate=False):
        self.events.append(('restore',immediate));self.state['status']='restored';save(self.logs/'state.json',self.state)
        self.skin='stock.apk'
        for pkg in self.overlays: self.overlays[pkg]=False

class SetupTests(unittest.TestCase):
    def fixture(self,directory,existed=False,mode='success'):
        base=Path(directory);logs=base/'logs';logs.mkdir();bundle=base/'bundle';bundle.mkdir()
        directory='/data/local/beam-russifier-boot/releases/'+MANIFEST['version']+'-test'
        files={}
        for name in ('apply.sh','skin.sh'):
            (bundle/name).write_text('D='+directory+'\n');files[name]=sha(bundle/name)
        for name in ('skin.apk','panel.apk',*[x['file'] for x in MANIFEST['runtimePatches']]): files[name]=MANIFEST['files'][name]
        (bundle/'boot-helper.apk').write_bytes(b'helper');helper=sha(bundle/'boot-helper.apk')
        save(bundle/'build-info.json',{'directory':directory,'files':files,'helperSha256':helper})
        return Device(logs,existed,mode),bundle
    def run_setup(self,device,bundle):
        # Real orchestration and journal, actual bundle validation; only Android is simulated.
        with patch.object(boot_setup,'BASE',device.logs.parent):
            (device.logs.parent/'runs').mkdir(exist_ok=True)
            boot_setup.install(device,bundle)
    def test_policy_merge_preserves_all_existing_content(self):
        result=json.loads(boot_setup.merge_policy(json.dumps(DEFAULT)))
        self.assertEqual(result['unrelated'],DEFAULT['unrelated']);self.assertEqual(result['oomadjLimit'][:-1],DEFAULT['oomadjLimit'])
        self.assertEqual(result['oomadjLimit'][-1],boot_setup.RULE)
        self.assertEqual(json.loads(boot_setup.merge_policy(json.dumps(result))),result)
    def test_unknown_or_duplicate_own_rule_rejected(self):
        for rule in ({'pkg':PACKAGE,'start':999},boot_setup.RULE):
            data={'oomadjLimit':[rule,boot_setup.RULE]}
            with self.assertRaisesRegex(RuntimeError,'изменено'): boot_setup.merge_policy(json.dumps(data))
    def test_independent_module_rule_survives_helper_removal(self):
        with tempfile.TemporaryDirectory() as directory:
            device,bundle=self.fixture(directory);self.run_setup(device,bundle)
            remote={'pkg':'com.beam.remote','start':200,'min':500,'max':800}
            data=json.loads(device.policy);data['oomadjLimit'].append(remote);data['newField']='keep'
            device.policy=json.dumps(data).encode()
            boot_setup.remove(device,device.logs)
            result=json.loads(device.policy)
            self.assertIn(remote,result['oomadjLimit']);self.assertEqual(result['newField'],'keep')
            self.assertFalse(any(x['pkg']==PACKAGE for x in result['oomadjLimit']))
    def test_modified_owned_rule_still_refused_before_removal(self):
        with tempfile.TemporaryDirectory() as directory:
            device,bundle=self.fixture(directory);self.run_setup(device,bundle)
            data=json.loads(device.policy);data['oomadjLimit'][-1]['max']=999;device.policy=json.dumps(data).encode()
            with self.assertRaisesRegex(RuntimeError,'независимо'):boot_setup.remove(device,device.logs)
            self.assertTrue(device.helper)
    def test_success_then_remove_preserves_other_services_and_policy(self):
        for existed in (False,True):
            with self.subTest(existed=existed),tempfile.TemporaryDirectory() as directory:
                device,bundle=self.fixture(directory,existed);self.run_setup(device,bundle)
                self.assertIn(SERVICE,device.services);self.assertTrue(device.helper)
                # Changes by other apps after installation must survive removal.
                device.services+=':new/.Service'
                boot_setup.remove(device,device.logs)
                self.assertEqual(device.services,'other/.Service:new/.Service')
                self.assertEqual(device.policy,device.initial_policy);self.assertIsNone(device.helper)
                self.assertEqual(json.loads((device.logs/'setup.json').read_text())['status'],'removed')
                self.assertIn(('restore',False),device.events)
    def test_disconnection_at_each_boundary_has_recoverable_journal(self):
        for mode in ('translation-lost','policy-lost','helper-reject','helper-lost','service-lost'):
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as directory:
                device,bundle=self.fixture(directory,True,mode)
                with self.assertRaises(RuntimeError): self.run_setup(device,bundle)
                self.assertEqual(json.loads((device.logs/'setup.json').read_text())['status'],'recovery-required')
                device.offline=False;boot_setup.remove(device,device.logs,immediate=True)
                self.assertEqual(device.policy,device.initial_policy);self.assertIsNone(device.helper)
                self.assertEqual(device.services,'other/.Service')
                self.assertIn(('restore',True),device.events)
    def test_changed_policy_refused_before_disabling_services(self):
        with tempfile.TemporaryDirectory() as directory:
            device,bundle=self.fixture(directory);self.run_setup(device,bundle)
            device.policy=b'independent change';old_services=device.services;events=len(device.events)
            with self.assertRaisesRegex(RuntimeError,'независимо'): boot_setup.remove(device,device.logs)
            self.assertEqual(device.services,old_services);self.assertTrue(device.helper)
            self.assertFalse(any(e[0]=='uninstall' for e in device.events[events:] if isinstance(e,tuple)))
    def test_recovery_other_projector_refused_before_root(self):
        with tempfile.TemporaryDirectory() as directory:
            device,bundle=self.fixture(directory);self.run_setup(device,bundle)
            device.props['ro.serialno']='OTHER';events=len(device.events)
            with self.assertRaisesRegex(RuntimeError,'другому'): boot_setup.remove(device,device.logs)
            self.assertFalse(any(e[:1]==('root',) for e in device.events[events:] if isinstance(e,tuple)))
    def test_no_space_refuses_before_install_or_policy_change(self):
        with tempfile.TemporaryDirectory() as directory:
            device,bundle=self.fixture(directory);original=device.shell
            device.shell=lambda script,**kw: '1' if script.startswith('df ') else original(script,**kw)
            with self.assertRaisesRegex(RuntimeError,'места'): self.run_setup(device,bundle)
            self.assertNotIn('translation-install',device.events);self.assertIsNone(device.policy)
    def test_unknown_mounted_apk_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            device,bundle=self.fixture(directory);device.runtime_hash='0'*64
            with self.assertRaisesRegex(RuntimeError,'исходных APK'): self.run_setup(device,bundle)
            self.assertNotIn('translation-install',device.events)
    def test_incomplete_bundle_refused_before_device_access(self):
        with tempfile.TemporaryDirectory() as directory:
            device,bundle=self.fixture(directory)
            info=json.loads((bundle/'build-info.json').read_text());del info['files']['panel.apk'];save(bundle/'build-info.json',info)
            with self.assertRaisesRegex(RuntimeError,'состав'): self.run_setup(device,bundle)
            self.assertFalse(device.events)
    def test_accessibility_flag_restored_when_we_are_last_service(self):
        with tempfile.TemporaryDirectory() as directory:
            device,bundle=self.fixture(directory);device.services='';device.enabled='0';self.run_setup(device,bundle)
            boot_setup.remove(device,device.logs)
            self.assertEqual(device.services,'');self.assertEqual(device.enabled,'0')

if __name__=='__main__': unittest.main()
