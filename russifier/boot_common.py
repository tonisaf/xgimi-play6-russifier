"""Validate and stage one immutable boot generation before activating its APK."""
import json,re
from pathlib import Path
from installer import MANIFEST,q,sha

PACKAGE='com.beam.russifier.boot'
SERVICE=PACKAGE+'/'+PACKAGE+'.StartupBridge'

def validate_bundle(bundle,payload,manifest=MANIFEST):
    bundle,payload=Path(bundle),Path(payload)
    info=json.loads((bundle/'build-info.json').read_text(encoding='utf-8'))
    directory=info['directory']
    if not re.fullmatch(r'/data/local/beam-russifier-boot/releases/[0-9A-Za-z.-]+',directory):
        raise RuntimeError('Недопустимый каталог поколения')
    if not directory.rsplit('/',1)[1].startswith(manifest['version']+'-'):
        raise RuntimeError('Поколение относится к другой версии комплекта')
    required={'apply.sh','skin.sh','skin.apk','panel.apk',*[x['file'] for x in manifest.get('runtimePatches',[])]}
    if set(info['files'])!=required:
        raise RuntimeError('Неполный или неизвестный состав поколения')
    sources={}
    for name,digest in info['files'].items():
        if not re.fullmatch(r'[a-z0-9-]+\.(sh|apk)',name) or not re.fullmatch(r'[a-f0-9]{64}',digest):
            raise RuntimeError('Недопустимое имя или SHA256 файла поколения')
        source=bundle/name if name.endswith('.sh') else payload/name
        if name.endswith('.apk') and digest!=manifest['files'][name]:
            raise RuntimeError('Поколение не соответствует manifest: '+name)
        if sha(source)!=digest: raise RuntimeError('Повреждён файл поколения: '+name)
        if name.endswith('.sh') and 'D='+q(directory) not in source.read_text(encoding='utf-8').splitlines():
            raise RuntimeError('Скрипт относится к другому каталогу поколения: '+name)
        sources[name]=source
    helper=bundle/'boot-helper.apk'
    if sha(helper)!=info['helperSha256']: raise RuntimeError('Повреждён helper')
    return info,sources,helper

def stage_generation(installer,info,sources):
    directory=info['directory'];staging=installer.remote+'/generation'
    installer.shell('mkdir -p '+q(staging))
    for name,path in sources.items(): installer.command('push',path,staging+'/'+name)
    checks=''.join('test "$(sha256sum '+q(directory+'/'+name)+' | cut -d " " -f 1)" = '+q(digest)+'\n'
                   for name,digest in info['files'].items())
    script='if [ -d '+q(directory)+' ]; then\n'+checks+'else\n'
    script+='  mkdir -p '+q(directory.rsplit('/',1)[0])+'\n'
    new=directory+'.new-'+installer.remote.rsplit('-',1)[-1]
    script+='  test ! -e '+q(new)+'\n  mkdir '+q(new)+'\n'
    for name,digest in info['files'].items():
        script+='  cp '+q(staging+'/'+name)+' '+q(new+'/'+name)+'\n'
        script+='  test "$(sha256sum '+q(new+'/'+name)+' | cut -d " " -f 1)" = '+q(digest)+'\n'
        script+='  chown root:root '+q(new+'/'+name)+'\n  chmod 644 '+q(new+'/'+name)+'\n'
        if name.endswith('.apk'): script+='  chcon u:object_r:system_file:s0 '+q(new+'/'+name)+'\n'
    script+='  chmod 755 '+q(new)+'\n  mv '+q(new)+' '+q(directory)+'\nfi\n'
    installer.root(script,'stage-boot-generation')
