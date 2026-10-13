"""Experimental first installation and reversible removal, without touching firmware."""
import argparse,json,os,re,shutil
from pathlib import Path
from installer import BASE,MANIFEST,Installer,SETTINGS,SKIN,q,sha,save
from boot_common import PACKAGE,SERVICE,validate_bundle,stage_generation
from boot_update import helper_hash,set_services

POLICY='/data/local/xgimi_gmui_manager/sys_pkg_adj.json'
DEFAULT_POLICY='/vendor/etc/xgimisys/sys_pkg_adj.json'
RULE={'pkg':PACKAGE,'start':200,'min':500,'max':800}
PAYLOAD=BASE/'payload'

def services(installer):
    value=installer.shell('settings get secure enabled_accessibility_services')
    return [] if value in ('','null') else value.split(':')

def merge_policy(raw,package=PACKAGE,rule=RULE):
    data=json.loads(raw)
    if not isinstance(data,dict) or not isinstance(data.get('oomadjLimit'),list):
        raise RuntimeError('Неизвестный формат OEM-политики памяти')
    entries=data['oomadjLimit']
    if any(not isinstance(x,dict) or not isinstance(x.get('pkg'),str) for x in entries):
        raise RuntimeError('Некорректные записи OEM-политики памяти')
    ours=[x for x in entries if x['pkg']==package]
    if ours and ours!=[rule]: raise RuntimeError('Правило пакета уже изменено другим способом')
    if not ours: entries.append(dict(rule))
    return (json.dumps(data,ensure_ascii=False,indent=2)+'\n').encode('utf-8')

def snapshot_policy(installer,package=PACKAGE,rule=RULE):
    directory=installer.logs/'setup-before';directory.mkdir()
    remote=installer.remote+'/oem-before.json'
    script='mkdir -p '+q(installer.remote)+'\nchown root:shell '+q(installer.remote)+'\nchmod 770 '+q(installer.remote)+'\n'
    script+='test -d '+q(POLICY.rsplit('/',1)[0])+'\n'
    script+='test ! -L '+q(POLICY)+'\n'
    script+='if [ -e '+q(POLICY)+' ]; then\n  test -f '+q(POLICY)+'\n'
    script+='  echo exists=1\n  stat -c "metadata=%u:%g:%a" '+q(POLICY)+'\n'
    script+='  ls -Zd '+q(POLICY)+' | awk \'{print "context=" $1}\'\n'
    script+='  cp '+q(POLICY)+' '+q(remote)+'\nelse\n  echo exists=0\n'
    script+='  cp '+q(DEFAULT_POLICY)+' '+q(remote)+'\nfi\nchmod 644 '+q(remote)+'\n'
    values=dict(line.split('=',1) for line in installer.root(script,'snapshot-oem-policy').splitlines() if '=' in line)
    existed=values.get('exists')=='1'
    if values.get('exists') not in ('0','1'): raise RuntimeError('Не удалось прочитать OEM-политику')
    metadata=values.get('metadata','1000:1000:600')
    context=values.get('context','')
    if not re.fullmatch(r'[0-9]+:[0-9]+:[0-7]{3,4}',metadata): raise RuntimeError('Неизвестные права OEM-политики')
    if context and not re.fullmatch(r'[a-zA-Z0-9_:,.-]+',context): raise RuntimeError('Неизвестный SELinux context')
    backup=directory/'oem-before.json';installer.command('pull',remote,backup)
    if backup.stat().st_size>1024*1024: raise RuntimeError('Неожиданный размер OEM-политики')
    after=installer.logs/'oem-after.json';after.write_bytes(merge_policy(backup.read_text(encoding='utf-8'),package,rule))
    return {'existed':existed,'beforeSha256':sha(backup),'afterSha256':sha(after),
            'metadata':metadata,'context':context,'package':package,'rule':rule}

def policy_guard(policy):
    if policy['existed']:
        return 'test -f '+q(POLICY)+'\ntest "$(sha256sum '+q(POLICY)+' | cut -d " " -f 1)" = '+q(policy['beforeSha256'])+'\n'
    return 'test ! -e '+q(POLICY)+'\n'

def apply_policy(installer,policy):
    if policy['existed'] and policy['beforeSha256']==policy['afterSha256']: return
    staged=installer.remote+'/oem-after.json';installer.shell('mkdir -p '+q(installer.remote))
    installer.command('push',installer.logs/'oem-after.json',staged)
    uid,gid,mode=policy['metadata'].split(':')
    temporary=POLICY+'.beam-'+installer.remote.rsplit('-',1)[-1]
    script='test ! -L '+q(POLICY)+'\n'+policy_guard(policy)
    script+='test "$(sha256sum '+q(staged)+' | cut -d " " -f 1)" = '+q(policy['afterSha256'])+'\n'
    script+='test -d '+q(POLICY.rsplit('/',1)[0])+'\ntest ! -e '+q(temporary)+'\n'
    script+='cp '+q(staged)+' '+q(temporary)+'\nchown '+uid+':'+gid+' '+q(temporary)+'\nchmod '+mode+' '+q(temporary)+'\n'
    script+=('chcon '+q(policy['context'])+' '+q(temporary)+'\n' if policy['context'] else 'restorecon '+q(temporary)+'\n')
    script+=policy_guard(policy)+'mv '+q(temporary)+' '+q(POLICY)+'\n'
    script+='test "$(sha256sum '+q(POLICY)+' | cut -d " " -f 1)" = '+q(policy['afterSha256'])+'\n'
    installer.root(script,'apply-oem-policy')

def policy_current(installer):
    output=installer.root('test ! -L '+q(POLICY)+'\nif [ -e '+q(POLICY)+' ]; then test -f '+q(POLICY)+'; sha256sum '+q(POLICY)+'; else echo absent; fi\n','read-oem-policy')
    return output.split()[0]

def policy_restore_plan(installer,policy):
    """Restore only our owned rule; independent packages and fields survive."""
    current=policy_current(installer)
    before=policy['beforeSha256'] if policy['existed'] else 'absent'
    if current==before: return None
    backup=installer.logs/'setup-before/oem-before.json'
    if sha(backup)!=policy['beforeSha256']: raise RuntimeError('Повреждена резервная копия OEM-политики')
    if current==policy['afterSha256']:
        return current,backup if policy['existed'] else None
    try:
        if current=='absent': raise ValueError('missing policy')
        raw=installer.root('test ! -L '+q(POLICY)+'\ntest "$(sha256sum '+q(POLICY)+' | cut -d " " -f 1)" = '+q(current)+'\ncat '+q(POLICY)+'\n','read-oem-policy-json')
        data=json.loads(raw);prior=json.loads(backup.read_text(encoding='utf-8'))
        if not isinstance(data,dict) or not isinstance(data.get('oomadjLimit'),list): raise ValueError('format')
        entries=data['oomadjLimit']
        if any(not isinstance(x,dict) or not isinstance(x.get('pkg'),str) for x in entries): raise ValueError('entries')
        package=policy.get('package',PACKAGE);rule=policy.get('rule',RULE)
        previous=[x for x in prior['oomadjLimit'] if x['pkg']==package]
        ours=[x for x in entries if x['pkg']==package]
        if ours==previous: return None
        if ours!=[rule]: raise ValueError('owned rule modified')
        data['oomadjLimit']=[x for x in entries if x['pkg']!=package]+previous
        if not policy['existed'] and data==prior: return current,None
        desired=installer.logs/'oem-scoped-restore.json'
        desired.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        return current,desired
    except (ValueError,KeyError,TypeError) as error:
        raise RuntimeError('OEM-политика изменена независимо в нашем правиле; восстановление остановлено') from error

def restore_policy(installer,policy):
    plan=policy_restore_plan(installer,policy)
    if plan is None: return
    current,backup=plan
    script='test ! -L '+q(POLICY)+'\ntest "$(sha256sum '+q(POLICY)+' | cut -d " " -f 1)" = '+q(current)+'\n'
    if backup is not None:
        digest=sha(backup)
        staged=installer.remote+'/restore-oem.json';installer.shell('mkdir -p '+q(installer.remote))
        installer.command('push',backup,staged)
        uid,gid,mode=policy['metadata'].split(':')
        temporary=POLICY+'.beam-restore-'+installer.remote.rsplit('-',1)[-1]
        script+='test "$(sha256sum '+q(staged)+' | cut -d " " -f 1)" = '+q(digest)+'\n'
        script+='test ! -e '+q(temporary)+'\ncp '+q(staged)+' '+q(temporary)+'\n'
        script+='chown '+uid+':'+gid+' '+q(temporary)+'\nchmod '+mode+' '+q(temporary)+'\n'
        if policy['context']: script+='chcon '+q(policy['context'])+' '+q(temporary)+'\n'
        else: script+='restorecon '+q(temporary)+'\n'
        script+='test "$(sha256sum '+q(POLICY)+' | cut -d " " -f 1)" = '+q(current)+'\n'
        script+='mv '+q(temporary)+' '+q(POLICY)+'\n'
    else: script+='rm -f '+q(POLICY)+'\n'
    installer.root(script,'restore-oem-policy')

def disable_own_service(installer,record):
    remaining=[c for c in services(installer) if not c.startswith(PACKAGE+'/')]
    set_services(installer,remaining)
    if not remaining and installer.shell('settings get secure accessibility_enabled')=='1':
        old=record['accessibilityEnabled']
        if old in ('','null'): installer.shell('settings delete secure accessibility_enabled')
        else: installer.shell('settings put secure accessibility_enabled '+q(old))
    if installer.shell('pm path '+PACKAGE,check=False).startswith('package:'):
        installer.shell('am force-stop '+PACKAGE)

def detach_native(installer):
    script='zyg=$(pidof zygote)\ntest -n "$zyg"\ntest "${zyg#* }" = "$zyg"\n'
    for item in [{'target':SETTINGS,'file':'panel.apk'}]+MANIFEST['runtimePatches']:
        original=MANIFEST['originals'][item['target']];path=original['path'];patched=MANIFEST['files'][item['file']]
        script+='n=0\nwhile :; do\ncurrent=$(nsenter -t "$zyg" -m -- sha256sum '+q(path)+' | cut -d " " -f 1)\n'
        script+='case "$current" in\n'+original['sha256']+') break;;\n'+patched+') :;;\n*) echo "APK changed independently"; exit 12;;\nesac\n'
        script+='test "$n" -lt 8\nnsenter -t "$zyg" -m -- umount '+q(path)+'\nn=$((n+1))\ndone\n'
    installer.root(script,'detach-setup-native')

def check_space(installer,info,sources):
    needed=sum(p.stat().st_size for p in sources.values())+sum((PAYLOAD/x['file']).stat().st_size for x in MANIFEST['overlays'])+64*1024*1024
    if shutil.disk_usage(installer.logs).free<needed*2: raise RuntimeError('Недостаточно свободного места на компьютере для резервных копий')
    output=installer.shell('df -Pk /data | tail -1 | awk \'{print $4}\'')
    if not output.isdigit() or int(output)*1024<needed*2:
        raise RuntimeError('Недостаточно места в /data или невозможно определить свободное место')

def identity_guard(installer,record):
    if record.get('version')!=MANIFEST['version'] or record.get('payloadHashes')!=MANIFEST['files']:
        raise RuntimeError('Для удаления нужен комплект той версии, которая сейчас стоит на проекторе (после обновления это комплект последнего обновления)')
    if installer.shell('getprop ro.build.fingerprint')!=MANIFEST['fingerprint']:
        raise RuntimeError('Прошивка не поддерживается этим комплектом')
    policy=record['policy']
    if not re.fullmatch(r'[0-9]+:[0-9]+:[0-7]{3,4}',policy['metadata']):
        raise RuntimeError('Некорректные права в журнале OEM-политики')
    if policy['context'] and not re.fullmatch(r'[a-zA-Z0-9_:,.-]+',policy['context']):
        raise RuntimeError('Некорректный SELinux context в журнале')
    for prop,value in record['device'].items():
        if installer.shell('getprop '+prop)!=value:
            raise RuntimeError('Резервная копия относится к другому устройству/прошивке')

def remove(installer,directory,immediate=False):
    directory=Path(directory).resolve()
    record=json.loads((directory/'setup.json').read_text(encoding='utf-8'))
    identity_guard(installer,record)
    installer.logs=directory
    if record['status']=='removed': print('Эта установка уже удалена.');return
    path=installer.shell('pm path '+PACKAGE,check=False)
    if path.startswith('package:') and helper_hash(installer)!=record['helperSha256']:
        raise RuntimeError('Helper изменён независимо; используйте процедуру для установленной версии')
    # Preserve unrelated changes: refuse before disabling the helper or touching app data.
    policy_restore_plan(installer,record['policy'])
    state_path=directory/'state.json'
    state=json.loads(state_path.read_text(encoding='utf-8')) if state_path.exists() else None
    if state and state['status']!='restored':
        for item in MANIFEST['overlays']:
            paths=installer.shell('pm path '+item['package'],check=False).splitlines()
            if len(paths)>1: raise RuntimeError('Неожиданный split APK перевода')
            if paths and installer.shell('sha256sum '+q(paths[0][8:])).split()[0]!=MANIFEST['files'][item['file']]:
                raise RuntimeError('Пакеты перевода изменены независимо; восстановление остановлено')
        skin=installer.shell('getprop persist.sys.xgimi.themeV2.url')
        if skin not in (SKIN,record['generation']+'/skin.apk',state['skinProperty']):
            raise RuntimeError('Скин изменён независимо; восстановление остановлено')
    record['status']='removing';save(directory/'setup.json',record)
    try:
        disable_own_service(installer,record)
        # A root restore may still be running after force-stop. Never race it.
        busy=installer.shell('getprop vendor.xgimi.system.debug.cmd')
        if busy: raise RuntimeError('Восстановление helper ещё выполняется; повторите удаление после его завершения')
        restore_policy(installer,record['policy'])
        if path.startswith('package:'):
            installer.command('uninstall',PACKAGE)
            if installer.shell('pm path '+PACKAGE,check=False).startswith('package:'): raise RuntimeError('Helper не удалён')
        if state and state['status']!='restored':
            installer.state=state
            detach_native(installer)
            # Discard our stacked mounts only; the clean-install guard recorded originals.
            installer.state['mountChanged']=False;installer.state['nativeMountsChanged']=[]
            installer.restore(immediate=immediate or state['status']!='installed')
        record['status']='removed';save(directory/'setup.json',record)
    except BaseException:
        record['status']='removal-pending';save(directory/'setup.json',record)
        raise
    print('Перевод и helper отменены. OEM-политика перечитается при следующей перезагрузке.')
    print('Неиспользуемое поколение APK оставлено на устройстве: активные процессы могут ещё ссылаться на него.')

def install(installer,bundle):
    info,sources,helper=validate_bundle(bundle,PAYLOAD)
    installer.preflight()
    if installer.shell('getenforce')!='Permissive': raise RuntimeError('Этот способ требует проверенного SELinux Permissive')
    if installer.props['persist.sys.locale']!='ru-RU': raise RuntimeError('Для автозапуска выберите именно ru-RU и перезапустите проектор')
    if installer.shell('pm path '+PACKAGE,check=False).startswith('package:'): raise RuntimeError('Helper уже установлен: используйте UPDATE_BOOT')
    native={SETTINGS:installer.runtime_hash,**installer.native_runtime}
    if any(value!=MANIFEST['originals'][pkg]['sha256'] for pkg,value in native.items()):
        raise RuntimeError('Первая установка требует исходных APK в текущей загрузке; существующий перевод сначала отмените')
    if any(s['path'] for s in installer.overlay_states().values()):
        raise RuntimeError('Ресурсные пакеты перевода уже установлены: первая установка требует чистого исходного состояния')
    original_services=services(installer)
    if any(c.startswith(PACKAGE+'/') for c in original_services): raise RuntimeError('Обнаружена оставшаяся запись helper в специальных возможностях')
    check_space(installer,info,sources)
    policy=snapshot_policy(installer)
    record={'version':MANIFEST['version'],'payloadHashes':MANIFEST['files'],
            'device':{key:installer.props[key] for key in ('ro.build.fingerprint','ro.serialno')},
            'generation':info['directory'],'helperSha256':info['helperSha256'],'policy':policy,
            'oldServices':original_services,'accessibilityEnabled':installer.shell('settings get secure accessibility_enabled'),
            'status':'prepared'}
    journal=installer.logs/'setup.json';save(journal,record)
    try:
        stage_generation(installer,info,sources)
        installer.install()
        record['status']='translation-installed';save(journal,record)
        record['status']='policy-installing';save(journal,record)
        apply_policy(installer,policy)
        record['status']='helper-installing';save(journal,record)
        installer.command('install',helper)
        if helper_hash(installer)!=info['helperSha256']: raise RuntimeError('Установленный helper не соответствует комплекту')
        record['status']='activating';save(journal,record)
        installer.shell('pm enable '+PACKAGE)
        # Merge at activation time, not the old snapshot: another service may have been added meanwhile.
        current=services(installer)
        set_services(installer,[c for c in current if not c.startswith(PACKAGE+'/')]+[SERVICE])
        installer.shell('settings put secure accessibility_enabled 1')
        if SERVICE not in services(installer): raise RuntimeError('Служба автозапуска не включена')
        record['status']='installed';save(journal,record)
        (BASE/'runs/latest-setup.txt').write_text(installer.logs.name,encoding='utf-8')
    except BaseException:
        record['status']='recovery-required';save(journal,record)
        print('Установка прервана. Журнал сохранён:',installer.logs)
        print('После восстановления связи запустите RECOVER_AUTOSTART.cmd и укажите этот каталог.')
        raise
    print('Перевод и автозапуск установлены. Осталось завершить настройку: перезагрузка проектора (правила памяти XGIMI читаются только при загрузке) и повторное включение служб — шаг «Завершить настройку».')

def main():
    parser=argparse.ArgumentParser(description='Экспериментальная первая установка с автозапуском и обратная процедура')
    parser.add_argument('mode',choices=['install-autostart','remove-autostart','recover-autostart'])
    parser.add_argument('--device',default=os.environ.get('beamDevice','192.168.1.100:5555'))
    parser.add_argument('--bundle',type=Path,default=BASE/'boot-helper')
    parser.add_argument('--backup',type=Path,default=os.environ.get('beamBackup') or None)
    parser.add_argument('--keep-child',action='store_true')
    args=parser.parse_args();installer=None
    try:
        installer=Installer(args)
        if args.mode=='install-autostart': install(installer,args.bundle)
        else:
            if ':' in installer.serial: installer.command('connect',installer.serial)
            if installer.command('get-state').stdout.strip()!='device': raise RuntimeError('ADB недоступен или не авторизован')
            directory=args.backup
            if directory is None:
                if args.mode=='recover-autostart': raise RuntimeError('Укажите каталог прерванной установки через --backup')
                name=(BASE/'runs/latest-setup.txt').read_text(encoding='utf-8').strip()
                if not re.fullmatch(r'[0-9]{8}-[0-9]{6}-[0-9a-f]{6}',name): raise RuntimeError('Некорректный указатель резервной копии')
                directory=BASE/'runs'/name
            remove(installer,directory,immediate=args.mode=='recover-autostart')
        return 0
    except (Exception,KeyboardInterrupt) as exc:
        print('ОШИБКА:',exc)
        if installer is not None: print('Журнал:',installer.logs)
        return 1

if __name__=='__main__': raise SystemExit(main())
