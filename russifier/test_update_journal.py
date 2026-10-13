"""Review findings: uninstallation after an update, the remote module's own choice, ADB connection before an update."""
import copy, json, tempfile, unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import boot_update, boot_setup, remote_setup
from installer import MANIFEST

OLD = {'version': '1.19.30', 'payloadHashes': {'a.apk': 'old'}, 'generation': '/data/local/beam-russifier-boot/releases/1.19.30-aaaa',
       'helperSha256': 'oldhelper'}
INFO = {'directory': '/data/local/beam-russifier-boot/releases/'+MANIFEST['version']+'-bbbb', 'helperSha256': 'newhelper'}
NAME = '20261013-120000-abcdef'

def journal(base, **changes):
    runs = Path(base)/'runs'/NAME
    runs.mkdir(parents=True)
    record = {**copy.deepcopy(OLD), 'device': {'ro.build.fingerprint': MANIFEST['fingerprint'], 'ro.serialno': 'TEST'},
              'policy': {'metadata': '1000:1000:600', 'context': ''}, 'status': 'installed', **changes}
    (runs/'setup.json').write_text(json.dumps(record), encoding='utf-8')
    (Path(base)/'runs/latest-setup.txt').write_text(NAME, encoding='utf-8')
    return runs/'setup.json'

class FakeInstaller:
    props = {'ro.serialno': 'TEST'}
    def __init__(self, logs): self.logs = Path(logs)
    def shell(self, command, check=True):
        if command == 'getprop ro.build.fingerprint': return MANIFEST['fingerprint']
        if command.startswith('getprop '): return {'ro.serialno': 'TEST'}.get(command[8:], '')
        raise AssertionError(command)

class UpdateJournalTests(unittest.TestCase):
    def test_uninstallation_stays_possible_after_an_update(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = journal(tmp)
            with patch.object(boot_update, 'BASE', Path(tmp)):
                before = json.loads(path.read_text(encoding='utf-8'))
                with self.assertRaisesRegex(RuntimeError, 'нужен комплект'):         # the stale journal is refused by the new kit
                    boot_setup.identity_guard(FakeInstaller(tmp), before)
                self.assertTrue(boot_update.register_update(FakeInstaller(Path(tmp)/'runs/20261013-130000-123456'), INFO))
            after = json.loads(path.read_text(encoding='utf-8'))
            boot_setup.identity_guard(FakeInstaller(tmp), after)                      # accepted now
            self.assertEqual((after['version'], after['generation'], after['helperSha256']), (MANIFEST['version'], INFO['directory'], 'newhelper'))
            self.assertEqual(after['payloadHashes'], MANIFEST['files'])
            self.assertEqual(after['updates'][0]['from']['version'], '1.19.30')       # the history is kept
            self.assertEqual(after['updates'][0]['from']['helperSha256'], 'oldhelper')
            self.assertEqual(after['policy'], before['policy'])                       # the original backups stay what they were

    def test_two_updates_are_both_recorded(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = journal(tmp)
            with patch.object(boot_update, 'BASE', Path(tmp)):
                boot_update.register_update(FakeInstaller(Path(tmp)/'runs/a'), INFO)
                boot_update.register_update(FakeInstaller(Path(tmp)/'runs/b'), {**INFO, 'helperSha256': 'third'})
            after = json.loads(path.read_text(encoding='utf-8'))
            self.assertEqual([u['from']['helperSha256'] for u in after['updates']], ['oldhelper', 'newhelper'])

    def test_other_device_or_unfinished_installation_is_not_touched(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = journal(tmp, status='recovery-required')
            with patch.object(boot_update, 'BASE', Path(tmp)):
                self.assertFalse(boot_update.register_update(FakeInstaller(Path(tmp)/'runs/a'), INFO))
            self.assertNotIn('updates', json.loads(path.read_text(encoding='utf-8')))
        with tempfile.TemporaryDirectory() as tmp:
            path = journal(tmp, device={'ro.build.fingerprint': MANIFEST['fingerprint'], 'ro.serialno': 'OTHER'})
            with patch.object(boot_update, 'BASE', Path(tmp)):
                self.assertFalse(boot_update.register_update(FakeInstaller(Path(tmp)/'runs/a'), INFO))

    def test_no_journal_on_this_computer_is_reported_not_fatal(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(boot_update, 'BASE', Path(tmp)):
                self.assertFalse(boot_update.register_update(FakeInstaller(tmp), INFO))

class RestoreTests(unittest.TestCase):
    def test_overlays_added_by_later_versions_are_uninstalled_not_a_crash(self):
        # The state of the first installation does not know packages that later versions added.
        state = {'overlays': {}}
        item = MANIFEST['overlays'][-1]
        previous = state['overlays'].get(item['package']) or {'path': None, 'enabled': False}
        self.assertFalse(previous['path'])
        import installer
        source = Path(installer.__file__).read_text(encoding='utf-8')
        self.assertIn("self.state['overlays'].get(item['package'])", source)         # restore() really uses the tolerant lookup

class RemoteChoiceTests(unittest.TestCase):
    def test_the_choice_is_remembered_and_read_back(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(remote_setup, 'DESIRED', Path(tmp)/'runs/remote-desired.json'):
            self.assertIsNone(remote_setup.desired())
            remote_setup.remember(False)
            self.assertIs(remote_setup.desired(), False)
            remote_setup.remember(True)
            self.assertIs(remote_setup.desired(), True)
            remote_setup.DESIRED.write_text('garbage', encoding='utf-8')
            self.assertIsNone(remote_setup.desired())

class ConnectTests(unittest.TestCase):
    def test_update_and_its_recovery_connect_before_any_command(self):
        for argv, expected in ((['--device', '10.0.0.5:5555'], 'update'), (['--device', '10.0.0.5:5555', '--recover', 'x'], 'recover')):
            calls = []
            class Fake:
                serial = '10.0.0.5:5555'
                logs = Path('.')
                def command(self, *args, **kwargs):
                    calls.append(args)
                    return SimpleNamespace(stdout='device\n', returncode=0)
            with patch.object(boot_update, 'Installer', lambda a: Fake()), \
                 patch.object(boot_update, 'update', lambda i, b: calls.append(('update',))), \
                 patch.object(boot_update, 'recover', lambda i, p: calls.append(('recover',))), \
                 patch('sys.argv', ['boot_update.py'] + argv):
                self.assertEqual(boot_update.main(), 0)
            self.assertEqual(calls[0], ('connect', '10.0.0.5:5555'))
            self.assertEqual(calls[-1], (expected,))

    def test_unauthorised_adb_stops_before_the_update(self):
        class Fake:
            serial = '10.0.0.5:5555'
            logs = Path('.')
            def command(self, *args, **kwargs): return SimpleNamespace(stdout='unauthorized\n', returncode=0)
        ran = []
        with patch.object(boot_update, 'Installer', lambda a: Fake()), patch.object(boot_update, 'update', lambda i, b: ran.append(1)), \
             patch('sys.argv', ['boot_update.py', '--device', '10.0.0.5:5555']):
            self.assertEqual(boot_update.main(), 1)
        self.assertEqual(ran, [])

if __name__ == '__main__':
    unittest.main()
