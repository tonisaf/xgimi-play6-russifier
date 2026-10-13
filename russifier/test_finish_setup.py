import unittest
from unittest.mock import patch
import finish_setup as f
from installer import MANIFEST

class FakeDevice:
    """A projector that behaves like the real one: a reboot drops the helper and module entries, as the system does."""
    def __init__(self, helper=True, module=True, stubborn=False, remove_once=False, never_boots=False, restore_ok=True):
        self.serial = '127.0.0.1:5555'
        self.helper, self.module = helper, module
        self.boot, self.booted = 'boot-1', True
        self.entries = ['com.xgimi.duertts/.MonitorService']
        self.stubborn, self.remove_once, self.never_boots, self.restore_ok = stubborn, remove_once, never_boots, restore_ok
        self.reboots = 0
        self.puts = 0
        self.after_boot_reads = 0
        self.wish = True          # what the user chose for the module (remote_setup.desired()); None: nothing recorded
    def command(self, *args, **kwargs):
        if args[0] == 'reboot':
            self.reboots += 1
            self.boot = 'boot-%d' % (self.reboots+1)
            self.booted = not self.never_boots
            self.entries = ['com.xgimi.duertts/.MonitorService']
        return type('P', (), {'stdout': ''})()
    def shell(self, command, check=True):
        if command == 'pm path com.beam.russifier.boot': return 'package:/x' if self.helper else ''
        if command == 'pm path com.beam.remote': return 'package:/y' if self.module else ''
        if command == 'cat /proc/sys/kernel/random/boot_id': return self.boot
        if command == 'getprop sys.boot_completed': return '1' if self.booted else ''
        if command == 'cat /proc/uptime': return '120.50 99.0'
        if command == 'settings get secure enabled_accessibility_services': return ':'.join(self.entries)
        if command.startswith('settings put secure enabled_accessibility_services '):
            self.puts += 1
            self.entries = command.split(' ', 4)[4].strip("'").split(':')
            return ''
        if command.startswith('settings put secure accessibility_enabled'): return ''
        if command.startswith('logcat -d -s BeamStartup:I'):
            return 'I/BeamStartup: restore complete uptime=1' if (self.restore_ok and f.HELPER_SERVICE in self.entries) else ''
        if command.startswith('cmd overlay list'):
            return str(len(MANIFEST['overlays'])) if (self.restore_ok and f.HELPER_SERVICE in self.entries) else '0'
        raise AssertionError('unexpected command: '+command)

class Clock:
    def __init__(self, device=None):
        self.now = 1000.0
        self.device = device
    def sleep(self, seconds):
        self.now += seconds
        d = self.device
        if d is None: return
        if d.stubborn:                                       # the system removes the services again and again
            d.entries = [e for e in d.entries if e not in (f.HELPER_SERVICE, f.MODULE_SERVICE)]
        elif d.remove_once and d.reboots and f.HELPER_SERVICE in d.entries:
            d.remove_once = False                            # ... or once, a moment after they were switched on
            d.entries = [e for e in d.entries if e != f.HELPER_SERVICE]
    def time(self):
        return self.now

def run(device, fn=f.finish):
    clock = Clock(device)
    with patch('finish_setup.time.sleep', clock.sleep), patch('finish_setup.time.time', clock.time),          patch('finish_setup.remote_setup.desired', lambda: device.wish):
        return fn(device)

class FinishTests(unittest.TestCase):
    def test_reboots_once_then_switches_both_services_on_and_waits_for_the_restore(self):
        d = FakeDevice()
        run(d)
        self.assertEqual(d.reboots, 1)
        self.assertIn(f.HELPER_SERVICE, d.entries)
        self.assertIn(f.MODULE_SERVICE, d.entries)
        self.assertIn('com.xgimi.duertts/.MonitorService', d.entries)       # other services are kept

    def test_a_service_removed_after_the_reboot_is_switched_on_again(self):
        d = FakeDevice(remove_once=True)
        run(d)
        self.assertIn(f.HELPER_SERVICE, d.entries)
        self.assertGreaterEqual(d.puts, 2)

    def test_services_that_keep_disappearing_are_reported(self):
        d = FakeDevice(stubborn=True)
        with self.assertRaisesRegex(RuntimeError, 'снова отключает службы'):
            run(d)

    def test_nothing_installed_means_no_reboot(self):
        d = FakeDevice(helper=False, module=False)
        run(d)
        self.assertEqual(d.reboots, 0)

    def test_module_only_is_finished_too_and_does_not_wait_for_a_helper(self):
        d = FakeDevice(helper=False, module=True)
        run(d)
        self.assertEqual(d.reboots, 1)
        self.assertIn(f.MODULE_SERVICE, d.entries)
        self.assertNotIn(f.HELPER_SERVICE, d.entries)

    def test_projector_that_stays_dark_gives_clear_advice(self):
        d = FakeDevice(never_boots=True)
        with self.assertRaisesRegex(RuntimeError, 'Включите его с пульта'):
            run(d)

    def test_helper_that_does_not_restore_is_reported(self):
        d = FakeDevice(restore_ok=False)
        with self.assertRaisesRegex(RuntimeError, 'не применил перевод'):
            run(d)

    def test_a_module_the_user_switched_off_stays_off(self):
        d = FakeDevice(helper=True, module=True)
        d.wish = False
        run(d)
        self.assertIn(f.HELPER_SERVICE, d.entries)
        self.assertNotIn(f.MODULE_SERVICE, d.entries)

    def test_without_a_recorded_choice_the_current_state_of_the_module_is_kept(self):
        off = FakeDevice(helper=True, module=True)
        off.wish = None                                     # installed earlier, service off now: stays off
        run(off)
        self.assertNotIn(f.MODULE_SERVICE, off.entries)
        on = FakeDevice(helper=True, module=True)
        on.wish = None
        on.entries.append(f.MODULE_SERVICE)                 # on now: switched on again after the reboot
        run(on)
        self.assertIn(f.MODULE_SERVICE, on.entries)

    def test_only_a_disabled_module_means_nothing_to_do_and_no_reboot(self):
        d = FakeDevice(helper=False, module=True)
        d.wish = False
        run(d)
        self.assertEqual(d.reboots, 0)

if __name__ == '__main__':
    unittest.main()
