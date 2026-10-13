import hashlib,json,shlex,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from installer import MANIFEST
from remote_setup import PACKAGE,SERVICE,install,recover,set_enabled,validate_module

class Device:
    def __init__(self,logs,mode='ok',old=True,enabled=True):
        self.logs=logs;self.serial='127.0.0.1:5555';self.mode=mode
        self.digest='old' if old else None
        self.components=['other/.Service']+([PACKAGE+'/.KeyBridge'] if enabled else [])
        self.global_value='1';self.installs=[]
    def shell(self,script):
        args=shlex.split(script)
        if args[:2]==['getprop','ro.build.fingerprint']:return MANIFEST['fingerprint']
        if args[:2]==['getprop','ro.build.version.sdk']:return MANIFEST['sdk']
        if args[:2]==['getprop','ro.serialno']:return 'TEST'
        if args[:2]==['pm','path']:return 'package:/data/app/remote/base.apk' if self.digest else ''
        if args[0]=='sha256sum':return self.digest+'  base.apk'
        if args[:3]==['settings','get','secure']:
            return ':'.join(self.components) if args[3]=='enabled_accessibility_services' else self.global_value
        if args[:3]==['settings','put','secure']:
            if args[3]=='enabled_accessibility_services':self.components=args[4].split(':')
            else:self.global_value=args[4]
        if args[:3]==['settings','delete','secure']:
            if args[3]=='enabled_accessibility_services':self.components=[]
            else:self.global_value='null'
        return ''
    def command(self,*args,**kwargs):
        if args[:2]==('shell','pm path '+PACKAGE):
            return SimpleNamespace(stdout=self.shell(args[1]),returncode=0 if self.digest else 1,stderr='')
        if args[0]=='get-state':return SimpleNamespace(stdout='device')
        if args[0]=='pull':Path(args[2]).write_bytes(b'old')
        if args[0]=='install':
            self.installs.append(args)
            # Simulate Android dropping our component while replacing the APK.
            self.components=['other/.Service','new/.Service']
            if self.mode=='reject':raise RuntimeError('rejected')
            self.digest=hashlib.sha256(Path(args[-1]).read_bytes()).hexdigest()
            if self.mode=='lost':raise RuntimeError('reply lost')
        return SimpleNamespace(stdout='')

class RemoteTests(unittest.TestCase):
    def setUp(self):
        for name in ('snapshot_policy','apply_policy','restore_policy'):
            item=patch('remote_setup.'+name,return_value={'package':PACKAGE})
            item.start();self.addCleanup(item.stop)
        # The remembered choice must never leak into the real kit's runs folder.
        self.desired_dir=tempfile.TemporaryDirectory();self.addCleanup(self.desired_dir.cleanup)
        item=patch('remote_setup.DESIRED',Path(self.desired_dir.name)/'remote-desired.json');item.start();self.addCleanup(item.stop)
    def fixture(self,directory,**kwargs):
        root=Path(directory);(root/'payload').mkdir();(root/'logs').mkdir()
        apk=root/'payload/remote-buttons.apk';apk.write_bytes(b'new')
        manifest={'remoteModule':{'package':PACKAGE,'file':apk.name,'sha256':hashlib.sha256(b'new').hexdigest()}}
        return Device(root/'logs',**kwargs),root,manifest
    def test_update_restores_enabled_component_and_preserves_new_unrelated_service(self):
        with tempfile.TemporaryDirectory() as directory,patch('remote_setup.verify_started') as verify:
            device,base,manifest=self.fixture(directory)
            install(device,base,manifest)
            self.assertEqual(device.components,['other/.Service','new/.Service',SERVICE]);verify.assert_called_once()
            self.assertEqual(device.installs[0][1],'-r')
    def test_update_does_not_reenable_deliberately_disabled_module(self):
        with tempfile.TemporaryDirectory() as directory,patch('remote_setup.verify_started') as verify:
            device,base,manifest=self.fixture(directory,enabled=False)
            install(device,base,manifest)
            self.assertNotIn(SERVICE,device.components);verify.assert_not_called()
    def test_new_install_enables_autostart(self):
        with tempfile.TemporaryDirectory() as directory,patch('remote_setup.verify_started'):
            device,base,manifest=self.fixture(directory,old=False,enabled=False)
            install(device,base,manifest);self.assertIn(SERVICE,device.components)
    def test_rejected_update_restores_old_enabled_state(self):
        with tempfile.TemporaryDirectory() as directory:
            device,base,manifest=self.fixture(directory,mode='reject')
            with self.assertRaisesRegex(RuntimeError,'rejected'):install(device,base,manifest)
            self.assertIn(SERVICE,device.components);self.assertEqual(device.digest,'old')
            self.assertEqual(json.loads((device.logs/'remote-setup.json').read_text())['status'],'not-committed')
    def test_lost_reply_committed_update_recovers_from_actual_apk(self):
        with tempfile.TemporaryDirectory() as directory,patch('remote_setup.verify_started'):
            device,base,manifest=self.fixture(directory,mode='lost')
            with self.assertRaisesRegex(RuntimeError,'reply lost'):install(device,base,manifest)
            device.components=['other/.Service'];recover(device,device.logs)
            self.assertIn(SERVICE,device.components)
    def test_corrupt_payload_is_rejected_before_device_changes(self):
        with tempfile.TemporaryDirectory() as directory:
            device,base,manifest=self.fixture(directory)
            (base/'payload/remote-buttons.apk').write_bytes(b'corrupt')
            with self.assertRaisesRegex(RuntimeError,'повреждён'):install(device,base,manifest)
            self.assertEqual(device.installs,[]);self.assertEqual(device.digest,'old')
    def test_disable_preserves_other_services(self):
        with tempfile.TemporaryDirectory() as directory:
            device,_,_=self.fixture(directory);set_enabled(device,False)
            self.assertEqual(device.components,['other/.Service'])
    def test_missing_package_transport_failure_is_not_a_new_install(self):
        with tempfile.TemporaryDirectory() as directory:
            device,base,manifest=self.fixture(directory,old=False,enabled=False)
            original=device.command
            def offline(*args,**kwargs):
                if args[:2]==('shell','pm path '+PACKAGE):return SimpleNamespace(stdout='',returncode=1,stderr='error: device offline')
                return original(*args,**kwargs)
            device.command=offline
            with self.assertRaisesRegex(RuntimeError,'device offline'):install(device,base,manifest)
            self.assertEqual(device.installs,[])
    def test_recovery_rejects_different_device_or_changed_apk(self):
        with tempfile.TemporaryDirectory() as directory,patch('remote_setup.verify_started'):
            device,base,manifest=self.fixture(directory);install(device,base,manifest)
            device.digest='other'
            with self.assertRaisesRegex(RuntimeError,'изменён'):recover(device,device.logs)
            path=device.logs/'remote-setup.json';record=json.loads(path.read_text());record['device']['ro.serialno']='OTHER';path.write_text(json.dumps(record))
            with self.assertRaisesRegex(RuntimeError,'другому'):recover(device,device.logs)
