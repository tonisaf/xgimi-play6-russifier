import hashlib,json,tempfile,unittest,zipfile
from pathlib import Path
from unittest.mock import patch
from build_release import build

class ReleaseTests(unittest.TestCase):
    def fixture(self,directory):
        base=Path(directory)/'source';base.mkdir();(base/'payload').mkdir()
        data=b'payload';files={}
        for name in ('test.apk','skin.apk','panel.apk'):
            (base/'payload'/name).write_bytes(data);files[name]=hashlib.sha256(data).hexdigest()
        (base/'manifest.json').write_text(json.dumps({'version':'9.0.0','files':files}))
        for name in ['INSTALL.cmd','CHECK.cmd','ROLLBACK.cmd','UPDATE_BOOT.cmd','INSTALL_AUTOSTART.cmd','REMOVE_AUTOSTART.cmd','RECOVER_AUTOSTART.cmd','README.md','TRANSLATION.md','REVIEW-FIXES.md','DELIVERY-REVIEW.md','installer.py','boot_update.py','boot_common.py','boot_setup.py','transforms.py','catalog_metadata.py','launch.py']:
            (base/name).write_text('test')
        for name in ('preparation.py','beam_setup.py','remote_setup.py','REMOTE-BUTTONS.md','finish_setup.py','MANUAL-OTHER-OS.md','manual-adb.sh'):
            (base/name).write_text('test')
        bundle=base/'test-bundle';bundle.mkdir()
        (bundle/'boot-helper.apk').write_bytes(b'test')
        digest=hashlib.sha256(b'test').hexdigest()
        generation_directory='/data/local/beam-russifier-boot/releases/9.0.0-test'
        bundle_files={name:files[name] for name in ('skin.apk','panel.apk')}
        for name in ('apply.sh','skin.sh'):
            (bundle/name).write_text('D='+generation_directory+'\n');bundle_files[name]=hashlib.sha256((bundle/name).read_bytes()).hexdigest()
        (bundle/'build-info.json').write_text(json.dumps({'directory':generation_directory,'helperSha256':digest,'files':bundle_files}))
        return base,Path(directory)/'dist'
    def test_existing_release_is_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            base,dist=self.fixture(directory);dist.mkdir();archive=dist/'beam-russifier-play6-v9.0.0.zip'
            archive.write_bytes(b'previous-release')
            with self.assertRaisesRegex(RuntimeError,'уже существует'): build(base,dist)
            self.assertEqual(archive.read_bytes(),b'previous-release')
    def test_corrupt_payload_never_publishes_archive(self):
        with tempfile.TemporaryDirectory() as directory:
            base,dist=self.fixture(directory);(base/'payload/test.apk').write_bytes(b'corrupted')
            with self.assertRaisesRegex(RuntimeError,'payload'): build(base,dist)
            self.assertFalse(dist.exists())
    def test_archive_and_checksum_match(self):
        with tempfile.TemporaryDirectory() as directory:
            base,dist=self.fixture(directory);report=build(base,dist,bundle=base/'test-bundle');archive=dist/report['file']
            self.assertEqual(hashlib.sha256(archive.read_bytes()).hexdigest(),report['sha256'])
            with zipfile.ZipFile(archive) as source:
                self.assertIsNone(source.testzip());self.assertIn('Beam-Russifier-Play6/TRANSLATION.md',source.namelist())
    def test_concurrent_publication_does_not_replace_winner(self):
        import os
        with tempfile.TemporaryDirectory() as directory:
            base,dist=self.fixture(directory)
            def racing_link(source,destination):
                Path(destination).write_bytes(b'winner');raise FileExistsError('already published')
            with patch.object(os,'link',side_effect=racing_link),self.assertRaises(FileExistsError): build(base,dist,bundle=base/'test-bundle')
            self.assertEqual((dist/'beam-russifier-play6-v9.0.0.zip').read_bytes(),b'winner')
            self.assertFalse(list(dist.glob('.russifier-*')))
    def test_initial_install_commands_require_boot_bundle(self):
        with tempfile.TemporaryDirectory() as directory:
            base,dist=self.fixture(directory)
            with self.assertRaisesRegex(RuntimeError,'boot-bundle'): build(base,dist)
            self.assertFalse(dist.exists())
    def test_cmd_has_single_crlf(self):
        with tempfile.TemporaryDirectory() as directory:
            base,dist=self.fixture(directory)
            (base/'CHECK.cmd').write_bytes(b'@echo off\r\r\nexit /b 0\r\n')
            report=build(base,dist,bundle=base/'test-bundle')
            with zipfile.ZipFile(dist/report['file']) as archive:
                raw=archive.read('Beam-Russifier-Play6/CHECK.cmd')
                self.assertNotIn(b'\r\r\n',raw);self.assertNotIn(b'\n',raw.replace(b'\r\n',b''))
