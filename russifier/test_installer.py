import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from installer import Installer, MANIFEST

class InstallFailureTests(unittest.TestCase):
    def test_root_cleanup_retries_failed_readback_and_clears_both_properties(self):
        with tempfile.TemporaryDirectory() as tmp:
            i=Installer.__new__(Installer);i.logs=Path(tmp)
            props={'vendor.xgimi.system.debug.cmd':'','vendor.xgimi.system.debugserver':''};failed=False
            i.shell=lambda cmd: props[cmd[8:]] if cmd.startswith('getprop ') else '0' if cmd.endswith('.done') else 'ok'
            def command(*args,**kwargs):
                nonlocal failed
                if args[0]=='shell':
                    import shlex
                    a=shlex.split(args[1])
                    if a[0]=='setprop':props[a[1]]=a[2]
                    if a[0]=='getprop':
                        if a[1].endswith('debugserver') and not failed:
                            failed=True
                            return SimpleNamespace(returncode=1,stdout='')
                        return SimpleNamespace(returncode=0,stdout=props[a[1]]+'\n')
                return SimpleNamespace(returncode=0,stdout='')
            i.command=command
            self.assertEqual(i.root('true','test'),'ok')
            self.assertTrue(failed);self.assertTrue(all(value=='' for value in props.values()))
    def test_unknown_native_mount_rejected_before_install(self):
        props={'ro.build.fingerprint':MANIFEST['fingerprint'],'ro.product.name':MANIFEST['product'],
            'ro.product.device':MANIFEST['device'],'ro.build.version.sdk':MANIFEST['sdk'],
            'persist.sys.locale':'ru-RU','ro.serialno':'TEST'}
        paths={v['path']:v['sha256'] for v in MANIFEST['originals'].values()}
        i=Installer.__new__(Installer);i.serial='192.168.1.100:5555'
        i.command=lambda *args,**kwargs: SimpleNamespace(stdout='device\n',returncode=0)
        i.shell=lambda cmd: props[cmd[8:]] if cmd.startswith('getprop ') else paths[cmd.split(' ',1)[1]]+'  file.apk'
        native=MANIFEST['runtimePatches'][0]
        i.root=lambda *args: '/system/bin/idmap2\n/system/bin/nsenter\n'+MANIFEST['files']['panel.apk']+'  settings.apk\n'+'0'*64+'  '+MANIFEST['originals'][native['target']]['path']
        with self.assertRaisesRegex(RuntimeError,'другая подмена APK'):
            i.preflight()

    def test_native_mount_original_and_our_hash_accepted(self):
        props={'ro.build.fingerprint':MANIFEST['fingerprint'],'ro.product.name':MANIFEST['product'],
            'ro.product.device':MANIFEST['device'],'ro.build.version.sdk':MANIFEST['sdk'],
            'persist.sys.locale':'ru-RU','ro.serialno':'TEST'}
        paths={v['path']:v['sha256'] for v in MANIFEST['originals'].values()}
        from itertools import product
        patches=MANIFEST['runtimePatches']
        options=[[MANIFEST['originals'][n['target']]['sha256'],MANIFEST['files'][n['file']],
                  *n.get('previousHashes',[])] for n in patches]
        for digests in product(*options):
            with self.subTest(digests=digests),tempfile.TemporaryDirectory() as tmp:
                expected={n['target']:d for n,d in zip(patches,digests)}
                i=Installer.__new__(Installer);i.serial='192.168.1.100:5555';i.logs=Path(tmp)
                i.command=lambda *args,**kwargs: SimpleNamespace(stdout='device\n',returncode=0)
                i.shell=lambda cmd: props[cmd[8:]] if cmd.startswith('getprop ') else paths[cmd.split(' ',1)[1]]+'  file.apk'
                output='/system/bin/idmap2\n/system/bin/nsenter\n'+MANIFEST['files']['panel.apk']+'  settings.apk\n'
                output+='\n'.join(d+'  '+MANIFEST['originals'][n['target']]['path'] for n,d in zip(patches,digests))
                i.root=lambda *args: output
                i.preflight()
                self.assertEqual(i.native_runtime,expected)
    def test_wrong_firmware_rejected_before_root_or_installs(self):
        i=Installer.__new__(Installer)
        i.serial='192.168.1.100:5555'
        i.command=lambda *args,**kwargs: SimpleNamespace(stdout='device\n',returncode=0)
        i.shell=lambda cmd: 'different-firmware'
        i.root=lambda *args: self.fail('Must not enter root on an unsupported device')
        with self.assertRaisesRegex(RuntimeError,'Неподдерживаемая'):
            i.preflight()

    def test_changed_system_apk_rejected_before_root(self):
        props={'ro.build.fingerprint':MANIFEST['fingerprint'],'ro.product.name':MANIFEST['product'],
            'ro.product.device':MANIFEST['device'],'ro.build.version.sdk':MANIFEST['sdk'],
            'persist.sys.locale':'ru-RU','ro.serialno':'TEST'}
        i=Installer.__new__(Installer);i.serial='192.168.1.100:5555'
        i.command=lambda *args,**kwargs: SimpleNamespace(stdout='device\n',returncode=0)
        i.shell=lambda cmd: props[cmd[8:]] if cmd.startswith('getprop ') else 'unexpected-hash file.apk'
        i.root=lambda *args: self.fail('Must not enter root for mismatched APKs')
        with self.assertRaisesRegex(RuntimeError,'Системный APK отличается'):
            i.preflight()

    def test_partial_install_triggers_recovery_and_cleanup(self):
        events=[]
        i=Installer.__new__(Installer);i.mutated=False
        i.snapshot=lambda: events.append('backup')
        i.prepare_data=lambda: events.append('prepare')
        def fail():
            i.mutated=True
            raise RuntimeError('simulated install failure')
        i.install_overlays=fail
        i.restore=lambda immediate=False: events.append(('restore',immediate))
        i.cleanup=lambda: events.append('cleanup')
        with self.assertRaisesRegex(RuntimeError,'simulated'):
            i.install()
        self.assertEqual(events,['backup','prepare',('restore',True),'cleanup'])

    def test_busy_diagnostic_service_is_not_overwritten(self):
        i=Installer.__new__(Installer)
        i.shell=lambda cmd: 'already-running'
        i.command=lambda *args,**kwargs: self.fail('Must not push or set props when diagnostic service is busy')
        clock=[0.0]
        def tick(seconds): clock[0]+=seconds
        with patch('installer.time.sleep',tick),patch('installer.time.time',lambda: clock[0]):
            with self.assertRaisesRegex(RuntimeError,'занят дольше 90 секунд'):
                i.root('id','test')
        self.assertGreaterEqual(clock[0],90)       # it waited the whole time and never wrote anything

    def test_root_waits_for_the_boot_helper_to_finish_its_restore(self):
        i=Installer.__new__(Installer)
        polls=[]
        # busy for the first three polls (the helper restoring right after the installation), then free
        def shell(cmd):
            if cmd.startswith('getprop vendor.xgimi.system.debug.cmd'):
                polls.append(cmd); return 'restoring' if len(polls)<=3 else ''
            if cmd.startswith('getprop vendor.xgimi.system.debugserver'): return ''
            raise AssertionError('stop after the wait: '+cmd)
        i.shell=shell
        def command(*args,**kwargs):
            if len(polls)<4: self.fail('written while the channel was busy')
            raise AssertionError('stop after the wait')
        i.command=command
        i.logs=Path(tempfile.mkdtemp())
        with patch('installer.time.sleep',lambda s: None):
            with self.assertRaisesRegex(AssertionError,'stop after the wait'):
                i.root('id','test')
        self.assertEqual(len(polls),4)             # three busy polls, the fourth found the channel free

    def test_a_briefly_unreachable_adb_server_is_retried_without_running_anything_twice(self):
        i=Installer.__new__(Installer)
        i.adb='adb.exe';i.serial='192.168.1.50:5555';i.logs=Path(tempfile.mkdtemp())
        calls=[]
        down=SimpleNamespace(returncode=1,stdout='',stderr='* daemon not running; starting now at tcp:5038\ncould not read ok from ADB Server\n* failed to start daemon')
        up=SimpleNamespace(returncode=0,stdout='ok',stderr='')
        results=[down,down,up]
        def run(cmd,**kwargs):
            calls.append(cmd)
            if 'start-server' in cmd or 'connect' in cmd: return SimpleNamespace(returncode=0,stdout='',stderr='')
            return results.pop(0)
        with patch('installer.subprocess.run',run),patch('installer.time.sleep',lambda s:None):
            proc=i.command('shell','echo ok')
        self.assertEqual(proc.stdout,'ok')
        self.assertEqual(len([c for c in calls if c[-2:]==['shell','echo ok']]),3)     # two failed attempts, then the real run
        self.assertEqual(len([c for c in calls if 'start-server' in c]),2)

    def test_other_adb_errors_are_not_retried(self):
        i=Installer.__new__(Installer)
        i.adb='adb.exe';i.serial='192.168.1.50:5555';i.logs=Path(tempfile.mkdtemp())
        calls=[]
        def run(cmd,**kwargs):
            calls.append(cmd)
            return SimpleNamespace(returncode=1,stdout='',stderr='error: device offline')
        with patch('installer.subprocess.run',run),patch('installer.time.sleep',lambda s:None):
            with self.assertRaisesRegex(RuntimeError,'device offline'):
                i.command('shell','echo ok')
        self.assertEqual(len(calls),1)

    def test_adb_is_chosen_by_environment_platform_and_path(self):
        import installer as inst
        with patch.dict('os.environ',{'XGIMI_ADB':'/opt/tools/adb'}):
            self.assertEqual(inst.find_adb(),'/opt/tools/adb')
        with patch.dict('os.environ',{},clear=False):
            import os
            os.environ.pop('XGIMI_ADB',None)
            with patch.object(inst.os,'name','posix'),patch.object(inst.shutil,'which',lambda name:'/usr/bin/adb'):
                self.assertEqual(inst.find_adb(),'/usr/bin/adb')                # Linux / macOS: adb from PATH
            with patch.object(inst.os,'name','posix'),patch.object(inst.shutil,'which',lambda name:None):
                with self.assertRaisesRegex(RuntimeError,'XGIMI_ADB'):
                    inst.find_adb()                                              # a clear message instead of a crash
            with patch.object(inst.os,'name','nt'):
                self.assertTrue(inst.find_adb().endswith('adb.exe') or inst.find_adb())   # Windows prefers the bundled adb when present

    def test_compatibility_check_does_not_require_russian_language_but_installation_does(self):
        props={'ro.build.fingerprint':MANIFEST['fingerprint'],'ro.product.name':MANIFEST['product'],
            'ro.product.device':MANIFEST['device'],'ro.build.version.sdk':MANIFEST['sdk'],
            'persist.sys.locale':'en-US','ro.serialno':'TEST'}
        def make():
            i=Installer.__new__(Installer);i.serial='192.168.1.100:5555'
            i.command=lambda *args,**kwargs: SimpleNamespace(stdout='device\n',returncode=0)
            i.shell=lambda cmd: props[cmd[8:]] if cmd.startswith('getprop ') else 'unexpected-hash file.apk'
            i.root=lambda *args: self.fail('Must not enter root for mismatched APKs')
            return i
        with self.assertRaisesRegex(RuntimeError,'русский язык'):
            make().preflight()
        with self.assertRaisesRegex(RuntimeError,'Системный APK отличается'):    # went past the language check
            make().preflight(strict=False)

    def test_overlay_values_are_read_with_one_adb_call(self):
        i=Installer.__new__(Installer);i.logs=Path(tempfile.mkdtemp())
        calls=[]
        replies=['@@@0\nПерезагрузить\n@@@1\nа\nб\n@@@2\n\n@@@end\n']
        def command(*args,**kwargs):
            calls.append(args)
            return SimpleNamespace(returncode=0,stdout=replies[0] if args[0]=='shell' and args[1].startswith('sh ') else '')
        i.command=command
        checks=[('t','string','a','x',''),('t','array','b','x',''),('t','string','c','x','')]
        self.assertEqual(i.lookups(checks),['Перезагрузить','а\nб',''])
        self.assertEqual([c[0] for c in calls],['push','shell','shell'])       # push, run, remove: three calls for any number of values
        self.assertIn('cmd overlay lookup t t:array/b',(i.logs/'lookups.sh').read_text(encoding='utf-8'))
        replies[0]='@@@0\nx\n'                                                  # a truncated answer must not pass as "all fine"
        with self.assertRaisesRegex(RuntimeError,'неполный'):
            i.lookups(checks)

if __name__=='__main__':
    unittest.main()
