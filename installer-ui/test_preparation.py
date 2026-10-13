"""Failure and ownership tests; no ADB commands or device writes."""
from pathlib import Path
import io,json,shlex,sys,tempfile,unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'russifier'))
import preparation as p
import beam_setup as beam

class Fake:
    def __init__(self,base,lean=False):
        self.logs=base/'runs/20261010-010000-aaaaaa';self.logs.mkdir(parents=True)
        self.values={'locale':'zh-CN','timezone':'Asia/Shanghai','autoZone':'1','ime':'sogou/.Ime','enabledImes':'sogou/.Ime'}
        self.packages={'com.xgimi.adservice':0,'com.xgimi.home':0,'com.spocky.projengmenu':0,'com.sohu.inputmethod.sogou.tv':0}
        self.lean=lean;self.config='config: zh-rCN-television';self.commands=[];self.fail_zone=False
    def shell(self,command,check=True):
        self.commands.append(command);a=shlex.split(command)
        if a[0]=='getprop':return self.values[next(k for k,v in p.SETTINGS.items() if v[1]==a[1])]
        if a[:2]==['settings','get']:return self.values[next(k for k,v in p.SETTINGS.items() if v[1]==a[3])]
        if a[0]=='setprop':self.values['locale']=a[2];return ''
        if a[:2]==['settings','put']:self.values[next(k for k,v in p.SETTINGS.items() if v[1]==a[3])]=a[4];return ''
        if a[:2]==['settings','delete']:self.values[next(k for k,v in p.SETTINGS.items() if v[1]==a[3])]='null';return ''
        if a[:2]==['service','call'] or a[:3]==['cmd','alarm','set-timezone']:
            if not self.fail_zone:self.values['timezone']=a[-1]
            return ''
        if a[:2]==['pm','path']:return 'package:/keyboard.apk' if self.lean else ''
        if a[:2]==['ime','list']:return p.IME if self.lean else ''
        if a[:2]==['ime','enable']:self.values['enabledImes']+=':'+p.IME;return ''
        if a[:2]==['ime','set']:self.values['ime']=a[2];return ''
        if a[0]=='pm':
            self.packages[a[-1]]={'disable-user':3,'enable':1,'default-state':0}[a[1]];return ''
        if a[:2]==['am','get-config']:return self.config
        if command==beam.HOME_QUERY:
            return '\n'.join(['com.home.tiles/.MainActivity','com.xgimi.home/.HomeActivity','com.android.newsettings/com.xgimi.newsettings.base.FallbackHome']+[k+'/.Home' for k in ('com.spocky.projengmenu','com.atv.launcher') if self.packages.get(k) in (0,1)])
        if a[:3]==['cmd','package','resolve-activity']:return 'com.home.tiles/.MainActivity'
        raise AssertionError(command)

class PreparationTests(unittest.TestCase):
    def test_prepare_install_passes_keep_child_default_and_option(self):
        import boot_setup
        from types import SimpleNamespace
        for option in ([],['--keep-child']):
            with self.subTest(option=option):
                device=SimpleNamespace(shell=lambda *args,**kwargs:'',logs=Path('test-log'))
                def create(args):
                    device.args=args
                    return device
                with patch.object(sys,'argv',['launch.py','prepare-install','--device','192.168.1.100:5555']+option),patch.object(p,'Installer',side_effect=create),patch.object(p,'identity'),patch.object(p,'prepare',return_value=0),patch.object(p,'initialize'),patch.object(boot_setup,'install') as install:
                    self.assertEqual(p.main(),0)
                    install.assert_called_once()
                    self.assertEqual(device.args.keep_child,bool(option))
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.base=Path(self.temp.name);self.r=Fake(self.base)
        self.patchers=[patch.object(p,'BASE',self.base),patch.object(p,'identity',lambda r:{'fingerprint':'test','serial':'test'}),patch.object(p,'package_state',lambda r,k:r.packages.get(k))]
        for x in self.patchers:x.start()
    def tearDown(self):
        for x in reversed(self.patchers):x.stop()
        self.temp.cleanup()
    def test_debloat_does_not_touch_home_or_remove_keyboard_without_replacement(self):
        self.assertEqual(p.prepare(self.r,'Europe/Moscow',True),10)
        self.assertEqual(self.r.packages['com.xgimi.adservice'],3)
        for k in p.GUARDED:self.assertEqual(self.r.packages[k],0)
        self.assertEqual(self.r.values['timezone'],'Europe/Moscow')
        self.assertEqual(self.r.values['autoZone'],'0')
    def test_locale_reboot_resume_keeps_first_snapshot(self):
        p.prepare(self.r,'Europe/Moscow',False);original=self.r.logs/'preparation.json'
        self.r.config='config: ru-rRU-television';self.r.logs=self.base/'runs/20261010-010001-bbbbbb';self.r.logs.mkdir()
        self.assertEqual(p.prepare(self.r,'Europe/Moscow',False),0)
        record=json.loads(original.read_text());self.assertEqual(record['status'],'complete')
        self.assertEqual(next(c for c in record['changes'] if c['key']=='locale')['before'],'zh-CN')
        self.assertEqual(len(record['changes']),3)
    def test_failed_timezone_can_be_undone(self):
        self.r.fail_zone=True
        with self.assertRaises(RuntimeError):p.prepare(self.r,'Europe/Moscow',False)
        self.r.fail_zone=False;p.undo(self.r,self.r.logs)
        self.assertEqual(self.r.values['locale'],'zh-CN');self.assertEqual(self.r.values['autoZone'],'1')
    def test_undo_does_not_overwrite_independent_change(self):
        p.prepare(self.r,'Europe/Moscow',False);self.r.values['timezone']='UTC'
        with self.assertRaisesRegex(RuntimeError,'Независимое'):p.undo(self.r,self.r.logs)
        self.assertEqual(self.r.values['timezone'],'UTC')
    def test_working_keyboard_is_selected_before_sogou_disabled(self):
        self.r.lean=True;p.prepare(self.r,None,True)
        self.assertLess(self.r.commands.index('ime set '+p.IME),self.r.commands.index('pm disable-user --user 0 com.sohu.inputmethod.sogou.tv'))
        p.undo(self.r,self.r.logs);self.assertEqual(self.r.values['ime'],'sogou/.Ime');self.assertEqual(self.r.packages['com.sohu.inputmethod.sogou.tv'],0)
    def test_no_service_selection_means_no_disabled_packages(self):
        p.prepare(self.r,None,False)
        self.assertTrue(all(x==0 for x in self.r.packages.values()))

class BeamTests(unittest.TestCase):
    def setUp(self):
        self.identity=patch.object(p,'identity',return_value={'fingerprint':'test','serial':'test'});self.identity.start()
    def tearDown(self):self.identity.stop()
    class Device(Fake):
        def __init__(self,base,home_ok=True):
            super().__init__(base,lean=True);self.home_ok=home_ok;self.home='com.xgimi.home/.HomeActivity';self.services='com.beam.russifier.boot/.StartupBridge';self.installs=[]
            self.packages['com.atv.launcher']=1;self.offers_service=True      # older BEAM releases offer the PanelOverlay accessibility service
        def command(self,*args,**kwargs):
            self.installs.append(args)
            if args[0]=='pull':Path(args[2]).write_bytes(b'test-backup')
        def shell(self,command,check=True):
            if command.startswith('pm path '):return 'package:/data/app/'+command.split()[-1]+'/base.apk'
            if command.startswith('dumpsys package '):return 'User 0: enabled=0'
            if command=='cmd package resolve-activity --brief -a android.intent.action.MAIN -c android.intent.category.HOME':
                if self.home_ok and self.packages['com.xgimi.home']==3:return 'com.home.tiles/.MainActivity'
                return self.home
            if command=='cmd package set-home-activity com.home.tiles/.MainActivity':
                self.commands.append(command)
                self.home='com.xgimi.xgimiframeworkui/.resolver.ResolverActivity'
                return 'Success'
            if command=='settings get secure enabled_accessibility_services':return self.services
            if command.startswith('settings put secure enabled_accessibility_services '):self.services=shlex.split(command)[4];return ''
            if command.startswith('settings get secure ') and command.split()[-1] not in [v[1] for v in p.SETTINGS.values()]:return '1'
            if command.startswith(('appops ','cmd notification ','pm grant ','settings put secure accessibility_enabled ')):
                self.commands.append(command);return ''
            if command.startswith('cmd package query-services '):return 'com.home.tiles/com.home.tiles.PanelOverlay' if self.offers_service else ''
            if command.startswith('am broadcast '):
                self.commands.append(command);return 'Broadcast completed: result=0'      # BEAM 0.4.x no longer answers the old bt_name hook
            return super().shell(command,check)
    def test_beam_profile_sets_rights_home_without_button_stubs_and_preserves_russifier_service(self):
        with tempfile.TemporaryDirectory() as directory:
            r=self.Device(Path(directory));cache=Path(directory)/'cache'
            with patch.object(beam,'download_release',return_value=(cache,'test')),patch.object(beam,'package_state',lambda r,k:r.packages.get(k,0)):
                beam.install_beam(r,None)
            installed=[x for x in r.installs if x[0]=='install']
            self.assertEqual(len(installed),1)           # the launcher only: remote keys belong to the independent module
            self.assertEqual(beam.NAMES,['app-release.apk'])
            self.assertEqual(beam.PACKAGES,['com.home.tiles'])
            self.assertIn('pm grant com.home.tiles android.permission.RECORD_AUDIO',r.commands)
            self.assertIn('com.beam.russifier.boot/.StartupBridge',r.services)
            self.assertIn('com.home.tiles/com.home.tiles.PanelOverlay',r.services)
            self.assertLess(r.commands.index('cmd package set-home-activity com.home.tiles/.MainActivity'),r.commands.index('pm disable-user --user 0 com.xgimi.home'))
    def test_release_without_accessibility_service_leaves_no_dangling_entry_and_no_bluetooth_hook(self):
        with tempfile.TemporaryDirectory() as directory:
            r=self.Device(Path(directory));r.offers_service=False
            with patch.object(beam,'download_release',return_value=(Path(directory),'test')),patch.object(beam,'package_state',lambda r,k:r.packages.get(k,0)):
                beam.install_beam(r,None)                      # must finish even though BEAM ignores the old bt_name hook
            self.assertNotIn('com.home.tiles/com.home.tiles.PanelOverlay',r.services)
            self.assertIn('com.beam.russifier.boot/.StartupBridge',r.services)     # other services are untouched
            self.assertFalse([c for c in r.commands if c.startswith('am broadcast')])
    def test_rights_the_app_does_not_request_are_skipped_but_other_failures_stop(self):
        missing=('WRITE_SECURE_SETTINGS','RECORD_AUDIO')
        class Release0411(self.Device):   # BEAM 0.4.11 no longer requests these two rights
            def shell(self,command,check=True):
                if command.startswith('pm grant ') and command.split()[-1].rsplit('.',1)[-1] in missing:
                    raise RuntimeError("ADB: Exception occurred while executing 'grant': java.lang.SecurityException: Package com.home.tiles has not requested permission "+command.split()[-1])
                return super().shell(command,check)
        with tempfile.TemporaryDirectory() as directory:
            r=Release0411(Path(directory))
            with patch.object(beam,'download_release',return_value=(Path(directory),'test')),patch.object(beam,'package_state',lambda r,k:r.packages.get(k,0)):
                beam.install_beam(r,None)
            self.assertIn('pm grant com.home.tiles android.permission.READ_TV_LISTINGS',r.commands)
            self.assertIn('pm grant com.home.tiles android.permission.ACCESS_FINE_LOCATION',r.commands)
            self.assertNotIn('pm grant com.home.tiles android.permission.RECORD_AUDIO',r.commands)
            self.assertIn('cmd package set-home-activity com.home.tiles/.MainActivity',r.commands)   # the installation went on
        class Broken(self.Device):
            def shell(self,command,check=True):
                if command=='pm grant com.home.tiles android.permission.READ_TV_LISTINGS':raise RuntimeError('ADB: device offline')
                return super().shell(command,check)
        with tempfile.TemporaryDirectory() as directory:
            r=Broken(Path(directory))
            with patch.object(beam,'download_release',return_value=(Path(directory),'test')),patch.object(beam,'package_state',lambda r,k:r.packages.get(k,0)):
                with self.assertRaisesRegex(RuntimeError,'device offline'):beam.install_beam(r,None)
    def test_failed_home_assignment_keeps_stock_launcher_enabled(self):
        with tempfile.TemporaryDirectory() as directory:
            r=self.Device(Path(directory),home_ok=False)
            with patch.object(beam,'download_release',return_value=(Path(directory),'test')),patch.object(beam,'package_state',lambda r,k:r.packages.get(k,0)):
                with self.assertRaisesRegex(RuntimeError,'не назначен'):beam.install_beam(r,None)
            self.assertEqual(r.packages['com.xgimi.home'],0)
            self.assertIn('pm disable-user --user 0 com.xgimi.home',r.commands)
            self.assertIn('pm default-state --user 0 com.xgimi.home',r.commands)
    def test_candidates_exclude_beam_stock_and_fallback(self):
        with tempfile.TemporaryDirectory() as directory:
            r=self.Device(Path(directory))
            self.assertEqual(beam.competing_launchers(r),['com.atv.launcher','com.spocky.projengmenu'])
    def test_failed_home_restores_explicitly_enabled_stock_state(self):
        with tempfile.TemporaryDirectory() as directory:
            r=self.Device(Path(directory),home_ok=False);r.packages['com.xgimi.home']=1
            with patch.object(beam,'download_release',return_value=(Path(directory),'test')),patch.object(beam,'package_state',lambda r,k:r.packages.get(k,0)):
                with self.assertRaises(RuntimeError):beam.install_beam(r,None)
            self.assertEqual(r.packages['com.xgimi.home'],1)
            self.assertIn('pm enable --user 0 com.xgimi.home',r.commands)
    def test_selected_launcher_disabled_before_home_unselected_projectivy_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            r=self.Device(Path(directory))
            with patch.object(beam,'download_release',return_value=(Path(directory),'test')),patch.object(beam,'package_state',lambda r,k:r.packages.get(k,0)):
                beam.install_beam(r,None,['com.atv.launcher'])
                self.assertEqual(r.packages['com.atv.launcher'],3);self.assertEqual(r.packages['com.spocky.projengmenu'],0)
                self.assertLess(r.commands.index('pm disable-user --user 0 com.atv.launcher'),r.commands.index('cmd package set-home-activity com.home.tiles/.MainActivity'))
                journal=r.logs/'beam-setup.json';record=json.loads(journal.read_text())
                beam.restore_launcher_changes(r,record,journal)
                self.assertEqual(r.packages['com.atv.launcher'],1)
    def test_failure_restores_selected_launcher(self):
        with tempfile.TemporaryDirectory() as directory:
            r=self.Device(Path(directory),home_ok=False)
            with patch.object(beam,'download_release',return_value=(Path(directory),'test')),patch.object(beam,'package_state',lambda r,k:r.packages.get(k,0)):
                with self.assertRaises(RuntimeError):beam.install_beam(r,None,['com.atv.launcher'])
            self.assertEqual(r.packages['com.atv.launcher'],1);self.assertEqual(r.packages['com.xgimi.home'],0)
    def test_stale_or_protected_selection_aborts_before_download(self):
        with tempfile.TemporaryDirectory() as directory:
            r=self.Device(Path(directory))
            with patch.object(beam,'download_release') as download:
                for package in ['com.android.newsettings','com.home.tiles','unknown.launcher']:
                    with self.assertRaises(RuntimeError):beam.install_beam(r,None,[package])
                download.assert_not_called()
    def test_return_does_not_overwrite_independent_state(self):
        with tempfile.TemporaryDirectory() as directory:
            r=self.Device(Path(directory));r.packages['com.atv.launcher']=2
            record={'launcherChanges':[{'package':'com.atv.launcher','before':1,'after':3}]}
            with patch.object(beam,'package_state',lambda r,k:r.packages.get(k)):
                with self.assertRaisesRegex(RuntimeError,'независимо'):beam.restore_launcher_changes(r,record,r.logs/'beam-setup.json')
            self.assertEqual(r.packages['com.atv.launcher'],2)
    def test_wrong_keyboard_aborts_before_download_or_device_changes(self):
        with tempfile.TemporaryDirectory() as directory:
            r=Fake(Path(directory))
            with patch.object(beam,'download_release') as download:
                with self.assertRaises(RuntimeError):beam.install_beam(r,Path(directory)/"missing.apk")
                download.assert_not_called()
                self.assertFalse(any('install' in x for x in r.commands))
    def test_checksum_failure_aborts_download(self):
        assets=[{'name':n,'browser_download_url':'https://github.com/tonisaf/beam-launcher/releases/download/test/'+n} for n in ['SHA256SUMS.txt']+beam.NAMES]
        release=json.dumps({'tag_name':'test','assets':assets}).encode()
        sums=('0'*64+'  app-release.apk\n').encode()
        def request(url):return io.BytesIO(release if url.endswith('latest') else sums if url.endswith('SHA256SUMS.txt') else b'bad apk')
        with tempfile.TemporaryDirectory() as directory,patch.object(beam,'BASE',Path(directory)),patch.object(beam,'request',request):
            with self.assertRaisesRegex(RuntimeError,'SHA256'):beam.download_release()
            self.assertFalse((Path(directory)/'beam-downloads/app-release.apk').exists())

class KeyboardDownloadTests(unittest.TestCase):
    def test_hash_failure_keeps_cache_clean(self):
        with tempfile.TemporaryDirectory() as directory,patch.object(beam,'BASE',Path(directory)),patch.object(beam,'request',return_value=io.BytesIO(b'bad')):
            with self.assertRaisesRegex(RuntimeError,'SHA256'):beam.download_keyboard()
            self.assertEqual(list((Path(directory)/'keyboard-downloads').iterdir()),[])
    def test_verified_cache_skips_network(self):
        import hashlib
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);cache=root/'keyboard-downloads';cache.mkdir();apk=cache/'LeanKeyboard-6.1.31.apk';apk.write_bytes(b'verified')
            with patch.object(beam,'BASE',root),patch.object(beam,'KEYBOARD_SHA256',hashlib.sha256(b'verified').hexdigest()),patch.object(beam,'apk_package',return_value=beam.KEYBOARD),patch.object(beam,'request') as network:
                self.assertEqual(beam.download_keyboard(),apk);network.assert_not_called()
    def test_wrong_package_rejected(self):
        import hashlib
        with tempfile.TemporaryDirectory() as directory,patch.object(beam,'BASE',Path(directory)),patch.object(beam,'KEYBOARD_SHA256',hashlib.sha256(b'wrong').hexdigest()),patch.object(beam,'request',return_value=io.BytesIO(b'wrong')),patch.object(beam,'apk_package',return_value='wrong.package'):
            with self.assertRaisesRegex(RuntimeError,'пакет'):beam.download_keyboard()
            self.assertEqual(list((Path(directory)/'keyboard-downloads').iterdir()),[])

if __name__=='__main__':unittest.main()
