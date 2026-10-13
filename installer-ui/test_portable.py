"""Exercise the shipped update entry point in an isolated extracted ZIP, without ADB."""
from pathlib import Path
import subprocess,sys,tempfile,zipfile

def check(archive):
    with tempfile.TemporaryDirectory(prefix='xgimi-portable-') as directory:
        root=Path(directory)
        with zipfile.ZipFile(archive) as source:source.extractall(root)
        kit=next(root.glob('*/kit'))
        code='''
import sys,runpy
from pathlib import Path
from unittest.mock import patch
kit=Path(sys.argv[1]);sys.path.insert(0,str(kit))
import boot_update,boot_common,remote_setup
calls=[]
def validate_update(installer,bundle):
    assert Path(bundle)==kit/'boot-helper',bundle
    info,sources,helper=boot_common.validate_bundle(bundle,kit/'payload')
    assert helper.is_file() and sources
    calls.append(info['directory'])
sys.argv=[str(kit/'launch.py'),'update-boot','--device','127.0.0.1:5555']
with patch.object(boot_update,'Installer'),patch.object(boot_update,'update',validate_update):
    try:runpy.run_path(str(kit/'launch.py'),run_name='__main__')
    except SystemExit as exc:assert exc.code==0,exc.code
assert len(calls)==1
module,apk=remote_setup.validate_module(kit)
assert apk.is_file() and module['versionCode'] > 0
def validate_remote(installer):
    remote_setup.validate_module(kit)
    calls.append('remote')
sys.argv=[str(kit/'launch.py'),'install-remote','--device','127.0.0.1:5555']
with patch.object(remote_setup,'Installer') as fake,patch.object(remote_setup,'install',validate_remote):
    fake.return_value.logs=kit/'runs/test'
    try:runpy.run_path(str(kit/'launch.py'),run_name='__main__')
    except SystemExit as exc:assert exc.code==0,exc.code
assert calls[-1]=='remote'
print('Portable update/remote entry points and all bundle hashes verified')
'''
        subprocess.run([str(kit/'runtime/python.exe'),'-I','-c',code,str(kit)],cwd=root,check=True)

if __name__=='__main__':check(Path(sys.argv[1]).resolve())
