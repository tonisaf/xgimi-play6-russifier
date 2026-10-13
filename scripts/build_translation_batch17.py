"""Seventeenth batch: shorter captions for the system update page (RRO of com.xgimi.upgrade).

The "check for updates" button is a fixed-width pill (about 17 characters at its text size): "Проверить обновления" was cut
off on the real screen ("…оверить обновлен…"). The button now says "Проверить"; the same pill is used while checking."""
from pathlib import Path
import json, shutil
import build_photo_fixes as builder

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'investigation/translation-batch17-2026-10-13'
WORK = Path('C:/android/translation-batch17-20261013')
CHANGES = {'update_check': 'Проверить', 'update_loading': 'Проверка…'}

def main():
    m = json.loads((ROOT / 'russifier/manifest.json').read_text(encoding='utf-8'))
    assert m['version'] == '1.19.33'
    for name, digest in m['files'].items():
        assert builder.sha(ROOT / 'russifier/payload' / name) == digest, name
    OUT.mkdir(exist_ok=True)
    (OUT / 'before').mkdir(exist_ok=True)
    shutil.copyfile(ROOT / 'russifier/manifest.json', OUT / 'before/manifest.json')
    shutil.copyfile(ROOT / 'russifier/payload/upgrade.apk', OUT / 'before/upgrade.apk')
    if WORK.exists():
        shutil.rmtree(WORK)
    WORK.mkdir()
    builder.OUT = OUT
    builder.WORK = WORK
    builder.VERSION, builder.VERSION_CODE = '1.19.34', 3
    built = builder.overlay('upgrade.apk', CHANGES)
    shutil.copyfile(built, ROOT / 'russifier/payload/upgrade.apk')
    m['files']['upgrade.apk'] = builder.sha(built)
    m['resourceChecks'].setdefault('com.xgimi.upgrade', {}).update(CHANGES)
    m['version'] = '1.19.34'
    (ROOT / 'russifier/manifest.json').write_text(json.dumps(m, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    (OUT / 'build-report.json').write_text(json.dumps({'version': '1.19.34', 'changes': CHANGES}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('Built 1.19.34', m['files']['upgrade.apk'][:16])

if __name__ == '__main__':
    main()
