"""Update an existing boot prototype; retain its immutable generation on failure."""
from pathlib import Path
import argparse,json,re,os
from installer import BASE,Installer,MANIFEST,q,sha,save
from boot_common import PACKAGE,validate_bundle,stage_generation

def helper_hash(installer):
    paths=installer.shell('pm path '+PACKAGE).splitlines()
    if len(paths)!=1 or not paths[0].startswith('package:'): raise RuntimeError('Неожиданный APK helper')
    return installer.shell('sha256sum '+q(paths[0][8:])).split()[0]

def restore_overlays(installer,changes):
    for item,old,backup in reversed(changes):
        if old['path']:
            installer.command('install','-r','-d',backup)
            installer.enable_overlay(item,old['enabled'])
        else: installer.command('uninstall',item['package'])

def restore_own_services(installer,ours):
    if not ours: return
    current=installer.shell('settings get secure enabled_accessibility_services')
    current=[] if current in ('','null') else current.split(':')
    set_services(installer,[c for c in current if not c.startswith(PACKAGE+'/')]+ours)

def recover(installer,log_directory):
    """Resolve an interrupted activation by reading PackageManager's actual result."""
    log_directory=Path(log_directory)
    record=json.loads((log_directory/'boot-update.json').read_text(encoding='utf-8'))
    for prop,expected in record['device'].items():
        if installer.shell('getprop '+prop)!=expected: raise RuntimeError('Резервная копия относится к другому устройству/прошивке')
    actual=helper_hash(installer)
    if actual==record['newHelperSha256']:
        record['status']='committed'
    elif actual==record['oldHelperSha256']:
        changes=[(x['item'],x['old'],log_directory/'boot-update-before'/x['item']['file']) for x in record['changes']]
        restore_overlays(installer,changes)
        record['status']='rolled-back'
    else: raise RuntimeError('Helper изменён другим способом; восстановление остановлено')
    restore_own_services(installer,[c for c in record['oldServices'] if c.startswith(PACKAGE+'/')])
    save(log_directory/'boot-update.json',record)
    print('Незавершённое обновление обработано:',record['status'])

def set_services(installer,components):
    if components: installer.shell('settings put secure enabled_accessibility_services '+q(':'.join(components)))
    else: installer.shell('settings delete secure enabled_accessibility_services')

def update(installer, bundle):
    bundle=Path(bundle)
    payload=Path(__file__).resolve().parent/'payload'
    info,sources,helper=validate_bundle(bundle,payload)
    directory=info['directory']
    if not installer.shell('pm path '+PACKAGE).startswith('package:'):
        raise RuntimeError('Этот сценарий обновляет только уже установленный прототип')
    installer.preflight()
    states=installer.overlay_states()
    backups=installer.logs/'boot-update-before';backups.mkdir()
    changed=[]
    for item in MANIFEST['overlays']:
        old=states[item['package']]
        if old['path'] and installer.shell('sha256sum '+q(old['path'])).split()[0]==MANIFEST['files'][item['file']]: continue
        backup=backups/item['file']
        if old['path']: installer.command('pull',old['path'],backup)
        changed.append((item,old,backup))
    original=installer.shell('settings get secure enabled_accessibility_services')
    services=[] if original in ('','null') else original.split(':')
    ours=[c for c in services if c.startswith(PACKAGE+'/')]
    disabled=[c for c in services if c not in ours]
    committed=False;changed_applied=[];restore_services=True;attempted=False
    record={'generation':directory,'status':'prepared','oldServices':services,
            'oldHelperSha256':helper_hash(installer),'newHelperSha256':info['helperSha256'],
            'device':{key:installer.props[key] for key in ('ro.build.fingerprint','ro.serialno')},
            'changes':[{'item':item,'old':old} for item,old,backup in changed]}
    save(installer.logs/'boot-update.json',record)
    try:
        if ours: set_services(installer,disabled)
        installer.shell('am force-stop '+PACKAGE)
        stage_generation(installer,info,sources)
        for item,old,backup in changed:
            changed_applied.append((item,old,backup))
            installer.command('install','-r',payload/item['file'])
            installer.enable_overlay(item,True)
        # PackageManager commits the new APK atomically. No live script is overwritten.
        record['status']='activating';save(installer.logs/'boot-update.json',record)
        attempted=True
        installer.command('install','-r',helper)
        committed=True
        record['status']='committed';save(installer.logs/'boot-update.json',record)
    except BaseException:
        if attempted and not committed:
            try:
                actual=helper_hash(installer)
                if actual==record['newHelperSha256']: committed=True
                elif actual!=record['oldHelperSha256']: raise RuntimeError('Неизвестный результат установки helper')
            except BaseException:
                restore_services=False
                record['status']='activation-uncertain';save(installer.logs/'boot-update.json',record)
                raise
        if not committed:
            try:
                restore_overlays(installer,changed_applied)
                record['status']='rolled-back';save(installer.logs/'boot-update.json',record)
            except BaseException:
                restore_services=False
                record['status']='overlay-rollback-failed';save(installer.logs/'boot-update.json',record)
                raise
        else:
            record['status']='committed';save(installer.logs/'boot-update.json',record)
        raise
    finally:
        if re.fullmatch(r'/data/local/tmp/beam-ru-[0-9a-f]{10}',installer.remote):
            installer.command('shell','rm -rf '+q(installer.remote),check=False)
        if restore_services: restore_own_services(installer,ours)
    print('Helper обновлён; старое поколение сохранено. Журнал:',installer.logs)

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--device',default=os.environ.get('beamDevice','192.168.1.100:5555'))
    parser.add_argument('--bundle',type=Path,default=BASE/'boot-helper')
    parser.add_argument('--recover',type=Path,help='Каталог runs незавершённого обновления')
    args=parser.parse_args()
    installer=None
    try:
        installer=Installer(args)
        if args.recover: recover(installer,args.recover)
        else: update(installer,args.bundle)
        return 0
    except (Exception,KeyboardInterrupt) as exc:
        print('ОШИБКА:',exc)
        if installer is not None: print('Журнал:',installer.logs)
        return 1

if __name__=='__main__': raise SystemExit(main())
