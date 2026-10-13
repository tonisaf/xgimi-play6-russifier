"""Smoke-test a ZIP with its embedded runtime, offline and with restricted PATH."""
import argparse,hashlib,json,os,subprocess,zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def verify(archive,directory):
    archive,directory=Path(archive).resolve(),Path(directory).resolve()
    if directory.exists(): raise RuntimeError('Каталог проверки уже существует; укажите новый')
    directory.mkdir(parents=True)
    with zipfile.ZipFile(archive) as source:
        if source.testzip(): raise RuntimeError('Повреждён архив')
        for name in source.namelist():
            relative=Path(name)
            if relative.is_absolute() or '..' in relative.parts or '\\' in name:
                raise RuntimeError('Недопустимый путь в ZIP')
            if '/runs/' in name or '/tests/' in name or name.endswith(('.db','.ser')):
                raise RuntimeError('Личные данные/фикстуры в ZIP')
        source.extractall(directory)
    base=directory/'Beam-Russifier-Play6'
    manifest=json.loads((base/'manifest.json').read_text(encoding='utf-8'))
    for name,digest in manifest['files'].items():
        if hashlib.sha256((base/'payload'/name).read_bytes()).hexdigest()!=digest:
            raise RuntimeError('Payload повреждён: '+name)
    env={**os.environ,'PATH':str(Path(os.environ['SystemRoot'])/'System32'),'PYTHONUTF8':'1'}
    env.pop('PYTHONHOME',None);env.pop('PYTHONPATH',None)
    python=base/'runtime/python.exe';launch=base/'launch.py'
    commands=[]
    def run(args,expected=0,input=None):
        command=args if isinstance(args,str) else list(map(str,args))
        process=subprocess.run(command,cwd=base,env=env,input=input,capture_output=True,encoding='utf-8',errors='replace',timeout=30)
        commands.append({'args':command,'exit':process.returncode,'stdout':process.stdout[-3000:],'stderr':process.stderr[-3000:]})
        (directory/'smoke-progress.json').write_text(json.dumps(commands,ensure_ascii=False,indent=2),encoding='utf-8')
        if process.returncode!=expected: raise RuntimeError('Ошибка smoke: '+repr(args)+' '+process.stdout+' '+process.stderr)
        return process
    for mode in ('check','install','rollback','update-boot','install-autostart','remove-autostart','recover-autostart'):
        run([python,'-I',launch,mode,'--help'])
    probe=base/'offline_probe.py'
    probe.write_text('import sys\nfrom pathlib import Path\nsys.path.insert(0,str(Path(__file__).resolve().parent))\nfrom boot_common import validate_bundle\nvalidate_bundle(Path(__file__).resolve().parent/"boot-helper",Path(__file__).resolve().parent/"payload")\nprint("generation_verified=1")\n',encoding='utf-8')
    run([python,'-I',probe]);probe.unlink()
    for name in ('CHECK.cmd','INSTALL.cmd','ROLLBACK.cmd','UPDATE_BOOT.cmd','INSTALL_AUTOSTART.cmd','REMOVE_AUTOSTART.cmd','RECOVER_AUTOSTART.cmd'):
        raw=(base/name).read_bytes()
        if b'\r\r\n' in raw or b'\n' in raw.replace(b'\r\n',b''): raise RuntimeError('Некорректный CRLF: '+name)
        # Malformed input is rejected before any ADB command, even through CMD wrappers.
        # CMD does not use the usual Windows argv escaping for its /c command tail.
        cmd=Path(os.environ['SystemRoot'])/'System32/cmd.exe'
        command='"'+str(cmd)+'" /d /s /c ""'+str(base/name)+'""'
        process=run(command,1,input='invalid;address\nunused-backup\n\n')
        if 'Недопустимый адрес' not in process.stdout+process.stderr: raise RuntimeError('Непонятный отказ: '+name)
    run([base/'tools/adb.exe','version'])  # Prints a version; no ADB server or device connection.
    if (base/'runs').exists(): raise RuntimeError('Отрицательные проверки неожиданно создали журнал устройства')
    report={'version':manifest['version'],'archiveSha256':hashlib.sha256(archive.read_bytes()).hexdigest(),
            'payloadFiles':len(manifest['files']),'embeddedRuntime':True,'restrictedPath':True,
            'unicodeAndSpacesPath':True,'cliHelpModes':7,'cmdNegativeChecks':7,'generationVerified':True,
            'adbVersionOnly':True,'deviceConnected':False,'cleanWindowsVm':False,'commands':commands}
    (directory/'smoke.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k!='commands'},ensure_ascii=False))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('archive',type=Path)
    parser.add_argument('--directory',type=Path,default=ROOT/'.local/проверка поставки с пробелами')
    args=parser.parse_args();verify(args.archive,args.directory)
