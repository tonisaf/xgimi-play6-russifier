"""Install/update the independent remote module, preserving accessibility choices."""
from pathlib import Path
import argparse, json, os, re, time
from installer import BASE, MANIFEST, Installer, q, sha, save
from boot_setup import snapshot_policy,apply_policy,restore_policy

PACKAGE = 'com.beam.remote'
SERVICE = PACKAGE+'/'+PACKAGE+'.KeyBridge'
RULE = {'pkg':PACKAGE,'start':200,'min':500,'max':800}

DESIRED = BASE/'runs'/'remote-desired.json'

def desired():
    """True / False: what the user last chose for the module's service; None: nothing recorded."""
    try: value = json.loads(DESIRED.read_text(encoding='utf-8')).get('enabled')
    except (OSError, ValueError): return None
    return value if isinstance(value, bool) else None

def remember(enabled):
    DESIRED.parent.mkdir(parents=True, exist_ok=True)
    DESIRED.write_text(json.dumps({'enabled': bool(enabled)})+'\n', encoding='utf-8')

def own(component):
    return component in (SERVICE, PACKAGE+'/.KeyBridge')

def services(installer):
    value = installer.shell('settings get secure enabled_accessibility_services')
    return [] if value in ('', 'null') else value.split(':')

def set_enabled(installer, enabled, previous_global=None):
    # Re-read immediately before writing, so unrelated services are preserved.
    components = [c for c in services(installer) if not own(c)]
    if enabled: components.append(SERVICE)
    if components:
        installer.shell('settings put secure enabled_accessibility_services '+q(':'.join(components)))
    else: installer.shell('settings delete secure enabled_accessibility_services')
    if enabled: installer.shell('settings put secure accessibility_enabled 1')
    elif not components and previous_global is not None:
        if previous_global in ('', 'null'): installer.shell('settings delete secure accessibility_enabled')
        else: installer.shell('settings put secure accessibility_enabled '+q(previous_global))
    if any(own(c) for c in services(installer)) != enabled:
        raise RuntimeError('Не удалось применить состояние службы кнопок')

def check_device(installer):
    if ':' in installer.serial: installer.command('connect', installer.serial)
    if installer.command('get-state').stdout.strip() != 'device':
        raise RuntimeError('ADB не авторизован или устройство недоступно')
    props = {k:installer.shell('getprop '+k) for k in ('ro.build.fingerprint','ro.build.version.sdk','ro.serialno')}
    if props['ro.build.fingerprint'] != MANIFEST['fingerprint'] or props['ro.build.version.sdk'] != MANIFEST['sdk']:
        raise RuntimeError('Модуль кнопок проверен только на Play 6 / v1.7.116')
    if not props['ro.serialno']: raise RuntimeError('Не удалось определить устройство для журнала')
    return props

def installed(installer):
    result = installer.command('shell', 'pm path '+PACKAGE, check=False)
    value = result.stdout.strip()
    if not value:
        # Android 11 returns 1 for a package that is not installed. An ADB
        # transport failure also returns 1, but has an error on stderr.
        if result.returncode in (0,1) and not result.stderr.strip(): return None
        raise RuntimeError('Не удалось проверить установленный модуль: '+result.stderr.strip())
    if result.returncode: raise RuntimeError('Ошибка PackageManager: '+value)
    paths = value.splitlines()
    if len(paths) != 1 or not paths[0].startswith('package:'):
        raise RuntimeError('Неожиданный split APK модуля кнопок')
    return paths[0][8:]

def installed_hash(installer):
    path = installed(installer)
    return installer.shell('sha256sum '+q(path)).split()[0] if path else None

def validate_module(base=BASE, manifest=MANIFEST):
    info = manifest.get('remoteModule')
    if not info or info['package'] != PACKAGE or info['file'] != 'remote-buttons.apk':
        raise RuntimeError('Этот комплект не содержит модуль кнопок')
    if not re.fullmatch(r'[a-f0-9]{64}', info['sha256']): raise RuntimeError('Некорректный SHA256 модуля')
    apk = Path(base)/'payload'/info['file']
    if sha(apk) != info['sha256']: raise RuntimeError('APK модуля кнопок повреждён')
    return info, apk

def verify_started(installer, timeout=20):
    deadline = time.monotonic()+timeout
    while time.monotonic() < deadline:
        dump = installer.shell('dumpsys accessibility')
        bound = re.search(r'Bound services:(.*?)Enabled services:', dump, re.S)
        service = installer.shell('dumpsys activity services '+PACKAGE+'/.KeyService')
        if bound and 'label=Кнопки пульта' in bound[1] and 'ServiceRecord{' in service and 'KeyService' in service:
            return
        time.sleep(.5)
    raise RuntimeError('APK установлен, но автозапуск кнопок не подтверждён; см. remote-setup.json и журнал')

def install(installer, base=BASE, manifest=MANIFEST):
    info, apk = validate_module(base, manifest)
    identity = check_device(installer)
    old = installed(installer)
    was_enabled = any(own(c) for c in services(installer))
    old_global = installer.shell('settings get secure accessibility_enabled')
    record = {'device':identity, 'status':'prepared', 'oldHash':installed_hash(installer),
              'newHash':info['sha256'], 'enabledBefore':was_enabled,
              'enabledAfter':True if old is None else (was_enabled if desired() is None else desired()), 'globalBefore':old_global}
    if old: installer.command('pull', old, installer.logs/'remote-before.apk')
    record['policy']=snapshot_policy(installer,PACKAGE,RULE)
    save(installer.logs/'remote-setup.json', record)
    try:
        # This per-package OEM rule is loaded at the next system_server start.
        # Global memory optimisation and other package rules are unchanged.
        apply_policy(installer,record['policy'])
        set_enabled(installer, False)
        installer.shell('am force-stop '+PACKAGE)
        record['status']='activating'; save(installer.logs/'remote-setup.json', record)
        # Never uninstall to resolve a signature error: install -r preserves assignments.
        installer.command('install', '-r', apk)
        if installed_hash(installer) != info['sha256']: raise RuntimeError('Не подтверждён установленный APK кнопок')
    finally:
        # If ADB disappears, keep the prepared journal for explicit recovery.
        actual = installed_hash(installer)
        if actual == record['newHash']:
            record['status']='committed'
            enabled = record['enabledAfter']
            remember(enabled)
        elif actual == record['oldHash']:
            record['status']='not-committed'
            enabled = record['enabledBefore']
            restore_policy(installer,record['policy'])
        else:
            raise RuntimeError('Неопределённый результат установки кнопок; используйте recover-remote с этим журналом')
        set_enabled(installer, enabled, old_global)
        save(installer.logs/'remote-setup.json', record)
    if record['enabledAfter']: verify_started(installer)
    print('Модуль кнопок установлен/обновлён. Назначения сохранены. Автозапуск:', record['enabledAfter'])
    print('Правило памяти XGIMI читается только при загрузке: после установки выполните шаг «Завершить настройку» (перезагрузка и повторное включение службы кнопок).')

def recover(installer, backup):
    record = json.loads((Path(backup)/'remote-setup.json').read_text(encoding='utf-8'))
    if check_device(installer) != record['device']: raise RuntimeError('Журнал относится к другому устройству')
    actual = installed_hash(installer)
    if actual == record['newHash']:
        enabled = record['enabledAfter']
        remember(enabled)
    elif actual == record['oldHash']:
        enabled = record['enabledBefore']
        previous_logs=installer.logs
        try:
            installer.logs=Path(backup)
            if record.get('policy'): restore_policy(installer,record['policy'])
        finally: installer.logs=previous_logs
    else: raise RuntimeError('APK изменён другим способом; восстановление остановлено')
    set_enabled(installer, enabled, record['globalBefore'])
    if enabled: verify_started(installer)
    record['status']='recovered'; save(Path(backup)/'remote-setup.json', record)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=('install-remote','enable-remote','disable-remote','recover-remote'))
    parser.add_argument('--device', default=os.environ.get('beamDevice','192.168.1.100:5555'))
    parser.add_argument('--backup', type=Path)
    args = parser.parse_args(); installer = Installer(args)
    try:
        if args.action == 'install-remote': install(installer)
        elif args.action == 'recover-remote':
            if not args.backup: raise RuntimeError('Выберите журнал remote-setup.json')
            recover(installer, args.backup)
        else:
            check_device(installer)
            if args.action == 'enable-remote' and not installed(installer): raise RuntimeError('Сначала установите модуль кнопок')
            set_enabled(installer, args.action == 'enable-remote')
            remember(args.action == 'enable-remote')
            if args.action == 'disable-remote': installer.shell('am force-stop '+PACKAGE)
            else: verify_started(installer)
        return 0
    except Exception as error:
        print('ОШИБКА:', error); return 1
    finally: print('Журнал:', installer.logs)

if __name__ == '__main__': raise SystemExit(main())
