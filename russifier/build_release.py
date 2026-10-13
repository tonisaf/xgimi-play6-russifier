"""Build a verified archive without replacing an existing release."""
from pathlib import Path
import hashlib,json,os,tempfile,zipfile

BASE=Path(__file__).resolve().parent

def build(base=BASE, dist=None, bundle=None):
    dist=Path(dist) if dist is not None else base.parent/'dist'
    manifest=json.loads((base/'manifest.json').read_text(encoding='utf-8'))
    name=f'beam-russifier-play6-v{manifest["version"]}.zip'
    destination=dist/name
    if destination.exists() or (dist/(name+'.sha256')).exists():
        raise RuntimeError('Релиз уже существует; назначьте новую версию: '+name)
    for filename,digest in manifest['files'].items():
        if hashlib.sha256((base/'payload'/filename).read_bytes()).hexdigest()!=digest:
            raise RuntimeError('Повреждён payload: '+filename)
    files=['INSTALL.cmd','CHECK.cmd','ROLLBACK.cmd','UPDATE_BOOT.cmd','INSTALL_AUTOSTART.cmd','REMOVE_AUTOSTART.cmd','RECOVER_AUTOSTART.cmd','README.md','TRANSLATION.md','installer.py','boot_update.py','boot_common.py','boot_setup.py','transforms.py','catalog_metadata.py','launch.py','manifest.json','preparation.py','beam_setup.py','finish_setup.py']
    files.extend(['remote_setup.py','REMOTE-BUTTONS.md','MANUAL-OTHER-OS.md','manual-adb.sh'])
    if manifest.get('remoteModule'):
        from remote_setup import validate_module
        validate_module(base,manifest)
    members=[base/p for p in files]
    for folder in ['payload','tools','runtime','vendor','LICENSES']:
        members += [p for p in (base/folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc']
    boot_members=[]
    if bundle is not None:
        from boot_common import validate_bundle
        bundle=Path(bundle);info,_,_=validate_bundle(bundle,base/'payload',manifest)
        expected={'boot-helper.apk':info['helperSha256'],**{k:v for k,v in info['files'].items() if k.endswith('.sh')}}
        for filename,digest in expected.items():
            if hashlib.sha256((bundle/filename).read_bytes()).hexdigest()!=digest: raise RuntimeError('Повреждён boot bundle: '+filename)
        boot_members=[bundle/name for name in ['boot-helper.apk','apply.sh','skin.sh','build-info.json']]
    elif any(p.name=='INSTALL_AUTOSTART.cmd' for p in members):
        raise RuntimeError('Релиз с первичной установкой автозапуска требует --boot-bundle')
    dist.mkdir(exist_ok=True,parents=True)
    fd,temporary=tempfile.mkstemp(prefix='.russifier-',suffix='.zip',dir=dist)
    os.close(fd)
    try:
        with zipfile.ZipFile(temporary,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as output:
            for p in sorted(members):
                member_name='Beam-Russifier-Play6/'+p.relative_to(base).as_posix()
                if p.suffix=='.cmd':
                    # Windows cmd needs ordinary CRLF, not duplicated CR from old copies.
                    content=p.read_text(encoding='utf-8').replace('\r','').replace('\n','\r\n')
                    output.writestr(member_name,content.encode('utf-8'))
                else: output.write(p,member_name)
            for p in boot_members: output.write(p,'Beam-Russifier-Play6/boot-helper/'+p.name)
        with zipfile.ZipFile(temporary) as output:
            if output.testzip() is not None: raise RuntimeError('Повреждён ZIP')
            if any('/runs/' in p or '/tests/' in p or p.endswith(('.db','.ser')) for p in output.namelist()):
                raise RuntimeError('Пользовательские данные попали в ZIP')
        digest=hashlib.sha256(Path(temporary).read_bytes()).hexdigest()
        # Exclusive publication on the same filesystem also guards concurrent builds.
        os.link(temporary,destination)
        with (dist/(name+'.sha256')).open('x',encoding='ascii') as stream: stream.write(digest+'  '+name+'\n')
        report={'file':name,'bytes':destination.stat().st_size,'sha256':digest,'members':len(members)+len(boot_members),
                'containsBootUpdate':bool(boot_members),
                'containsUserBackups':False,'containsTestFixtures':False}
        (dist/'release.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
        return report
    finally:
        Path(temporary).unlink(missing_ok=True)

if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('--boot-bundle',type=Path)
    print(json.dumps(build(bundle=parser.parse_args().boot_bundle),indent=2))
