"""Execute generated policy and unmount scripts, with Android-only tools stubbed."""
import os,subprocess,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import boot_setup
from installer import MANIFEST,SETTINGS,q,sha

BASH=Path(r'C:\Program Files\Git\bin\bash.exe')

class ShellDevice:
    def __init__(self,directory):
        self.logs=directory;self.remote=(directory/'stage-0123456789').as_posix();self.fail_copy=False
        (directory/'stage-0123456789').mkdir();(directory/'bin').mkdir()
        for name in ('chown','chcon','restorecon'):
            (directory/'bin'/name).write_text('#!/bin/sh\nexit 0\n',newline='\n')
    def shell(self,script):
        return self.root(script,'shell')
    def command(self,*args):
        if args[0]!='push': raise AssertionError(args)
        Path(args[2]).write_bytes(Path(args[1]).read_bytes())
    def root(self,script,tag):
        local=self.logs/(tag+'.sh')
        local.write_text('set -e\nPATH="./bin:$PATH"\n'+script,encoding='utf-8',newline='\n')
        proc=subprocess.run([str(BASH),local.name],cwd=self.logs,capture_output=True,text=True)
        if proc.returncode: raise RuntimeError('shell failed '+tag+': '+proc.stderr)
        return proc.stdout.strip()

class DeliveryShellTests(unittest.TestCase):
    def setUp(self):
        if not BASH.exists(): self.skipTest('Git Bash required')
    def policy_fixture(self,directory,existed):
        device=ShellDevice(directory);policy=directory/'policy.json'
        before=directory/'setup-before';before.mkdir()
        raw=b'{"oomadjLimit":[],"retain":"original"}\n'
        (before/'oem-before.json').write_bytes(raw)
        after=directory/'oem-after.json';after.write_bytes(boot_setup.merge_policy(raw.decode()))
        if existed: policy.write_bytes(raw)
        record={'existed':existed,'beforeSha256':sha(before/'oem-before.json'),'afterSha256':sha(after),
                'metadata':'1000:1000:600','context':'u:object_r:system_data_file:s0'}
        return device,policy,record,raw
    def test_actual_policy_apply_and_restore_for_existing_and_absent_file(self):
        for existed in (False,True):
            with self.subTest(existed=existed),tempfile.TemporaryDirectory() as temporary:
                directory=Path(temporary);device,policy,record,raw=self.policy_fixture(directory,existed)
                with patch.object(boot_setup,'POLICY',policy.as_posix()):
                    boot_setup.apply_policy(device,record)
                    self.assertEqual(sha(policy),record['afterSha256'])
                    boot_setup.restore_policy(device,record)
                    if existed: self.assertEqual(policy.read_bytes(),raw)
                    else: self.assertFalse(policy.exists())
    def test_copy_failure_does_not_replace_original_policy(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory=Path(temporary);device,policy,record,raw=self.policy_fixture(directory,True)
            (directory/'bin/cp').write_text('#!/bin/sh\nexit 1\n',newline='\n')
            with patch.object(boot_setup,'POLICY',policy.as_posix()),self.assertRaises(RuntimeError):
                boot_setup.apply_policy(device,record)
            self.assertEqual(policy.read_bytes(),raw)
    def test_independent_policy_change_blocks_apply_and_restore(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory=Path(temporary);device,policy,record,raw=self.policy_fixture(directory,True)
            policy.write_bytes(b'changed by someone else')
            with patch.object(boot_setup,'POLICY',policy.as_posix()):
                with self.assertRaises(RuntimeError): boot_setup.apply_policy(device,record)
                with self.assertRaisesRegex(RuntimeError,'независимо'): boot_setup.restore_policy(device,record)
            self.assertEqual(policy.read_bytes(),b'changed by someone else')
    def test_detach_stacked_owned_apks_and_stop_on_unknown_layer(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory=Path(temporary);device=ShellDevice(directory)
            (directory/'bin/pidof').write_text('#!/bin/sh\necho 1\n',newline='\n')
            native=[{'target':SETTINGS,'file':'panel.apk'}]+MANIFEST['runtimePatches']
            script='#!/bin/sh\nshift 4\ncase "$2" in\n'
            for index,item in enumerate(native):
                path=MANIFEST['originals'][item['target']]['path']
                script+=q(path)+') stack=stack'+str(index)+';;\n'
                original=MANIFEST['originals'][item['target']]['sha256'];digest=MANIFEST['files'][item['file']]
                (directory/('stack'+str(index))).write_text(digest+'\n'+digest+'\n'+original+'\n')
            script+='*) exit 2;;\nesac\ncase "$1" in\nsha256sum) head -1 "$stack";;\numount) tail -n +2 "$stack" > "$stack.new"; mv "$stack.new" "$stack";;\n*) exit 2;;\nesac\n'
            (directory/'bin/nsenter').write_text(script,newline='\n')
            boot_setup.detach_native(device)
            for index,item in enumerate(native):
                self.assertEqual((directory/('stack'+str(index))).read_text().strip(),MANIFEST['originals'][item['target']]['sha256'])
            unknown='0'*64+'\n'+MANIFEST['originals'][SETTINGS]['sha256']+'\n'
            (directory/'stack0').write_text(unknown)
            with self.assertRaises(RuntimeError): boot_setup.detach_native(device)
            self.assertEqual((directory/'stack0').read_text(),unknown)

if __name__=='__main__': unittest.main()
