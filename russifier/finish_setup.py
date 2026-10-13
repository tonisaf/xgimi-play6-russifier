"""Finish a first installation: reboot, then switch the autostart services on again and wait for the first restore.

Why a reboot is part of the installation: XGIMI's memory manager force-stops background applications ("low ram restrict
background"), and Android removes the accessibility service of a force-stopped package from the enabled list. The
protecting rules for the helper and the remote module (sys_pkg_adj.json) are read only at boot, so right after a first
installation both services are switched off by the system within seconds and would never start after the next boot.
After a reboot the rules are loaded; the services are switched on again and stay on."""
import argparse, os, time
from pathlib import Path
from installer import Installer, MANIFEST, q
import boot_common
import remote_setup

HELPER = boot_common.PACKAGE
HELPER_SERVICE = boot_common.SERVICE
MODULE = remote_setup.PACKAGE
MODULE_SERVICE = remote_setup.SERVICE
SETTLE = 60          # seconds of uptime to wait for before touching the settings after a boot

def installed(r, package):
    return r.shell('pm path '+package, check=False).startswith('package:')

def services(r):
    return remote_setup.services(r)

def boot_id(r):
    return r.shell('cat /proc/sys/kernel/random/boot_id').strip()

def wait_boot(r, previous, timeout=600):
    """Wait for a boot different from `previous` to finish and settle. Survives a projector that stays dark for a while."""
    end = time.time()+timeout
    announced = 0.0
    while time.time() < end:
        try:
            if ':' in r.serial: r.command('connect', r.serial, check=False)
            if r.shell('getprop sys.boot_completed', check=False).strip() == '1' and boot_id(r) != previous:
                uptime = float(r.shell('cat /proc/uptime').split()[0])
                if uptime >= SETTLE: return
                time.sleep(max(1.0, SETTLE-uptime))
                continue
        except (RuntimeError, ValueError, IndexError):
            pass
        if time.time()-announced > 30:
            announced = time.time()
            print('Ожидание проектора после перезагрузки… Если экран остался тёмным, включите проектор с пульта.', flush=True)
        time.sleep(5)
    raise RuntimeError('Проектор не вернулся после перезагрузки за 10 минут. Включите его с пульта и запустите «Дополнительно → Завершить настройку».')

def reboot(r):
    previous = boot_id(r)
    r.command('reboot', check=False)
    time.sleep(15)
    wait_boot(r, previous)

def enable(r, components):
    current = services(r)
    merged = current+[c for c in components if c not in current]
    r.shell('settings put secure enabled_accessibility_services '+q(':'.join(merged)))
    r.shell('settings put secure accessibility_enabled 1')

def hold(r, components, seconds=30):
    """Services must stay in the list; switch them on again if the system removes them (at most three times)."""
    end = time.time()+seconds
    repairs = 0
    while time.time() < end:
        time.sleep(3)
        if [c for c in components if c not in services(r)]:
            repairs += 1
            if repairs > 3:
                raise RuntimeError('Система снова отключает службы автозапуска; правила памяти XGIMI не загрузились. Перезагрузите проектор и запустите «Дополнительно → Завершить настройку».')
            enable(r, components)
            end = time.time()+seconds

def wait_first_restore(r, timeout=120):
    """The helper must report its restore and every translation package must be enabled."""
    expected = len(MANIFEST['overlays'])
    end = time.time()+timeout
    while time.time() < end:
        done = 'restore complete' in r.shell('logcat -d -s BeamStartup:I', check=False)
        enabled = r.shell("cmd overlay list | grep -c '\\[x\\] com.beam.translation'", check=False).strip()
        if done and enabled.isdigit() and int(enabled) >= expected: return
        time.sleep(3)
    raise RuntimeError('Helper не применил перевод после перезагрузки. Запустите «Дополнительно → Завершить настройку» ещё раз.')

def module_wanted(r):
    """The module's service is switched on only if the user wants it: the recorded choice (install / enable / disable
    of the module) wins; with no record the current state is kept, so a module that was switched off stays off."""
    choice = remote_setup.desired()
    if choice is not None: return choice
    return MODULE_SERVICE in services(r)

def finish(r):
    helper, module = installed(r, HELPER), installed(r, MODULE)
    if not helper and not module:
        print('Ничего завершать: helper и модуль кнопок не установлены.')
        return
    module = module and module_wanted(r)       # asked before the reboot: afterwards the system may have dropped the entry
    components = ([HELPER_SERVICE] if helper else [])+([MODULE_SERVICE] if module else [])
    if not components:
        print('Ничего включать: служба кнопок выключена вашим выбором, helper не установлен.')
        return
    print('Перезагрузка проектора: после неё вступают в силу правила памяти XGIMI для установленных служб…', flush=True)
    reboot(r)
    print('Проектор загрузился. Включение служб автозапуска…', flush=True)
    enable(r, components)
    hold(r, components)
    if helper:
        print('Ожидание, пока helper применит перевод…', flush=True)
        wait_first_restore(r)
    done = (['перевод применён'] if helper else [])+(['модуль кнопок активен'] if module else [])
    print('Готово: службы включены и держатся ('+', '.join(done)+'). Дальнейшие перезагрузки не требуют действий.', flush=True)

def main():
    parser = argparse.ArgumentParser(description='Перезагрузка и включение служб после первой установки')
    parser.add_argument('--device', default=os.environ.get('beamDevice', '192.168.1.100:5555'))
    args = parser.parse_args()
    r = Installer(args)
    try:
        if ':' in r.serial: r.command('connect', r.serial)
        finish(r)
        return 0
    except Exception as error:
        print('ОШИБКА:', error)
        return 1
    finally:
        print('Журнал:', r.logs)

if __name__ == '__main__':
    raise SystemExit(main())
