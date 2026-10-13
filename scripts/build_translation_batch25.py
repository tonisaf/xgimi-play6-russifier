"""Twenty-fifth batch (1.19.44): the local player (`com.xgimi.gimiplayer`).

English is the app's default and it has no ru-RU, so all of its menus, toasts and dialogs showed English except the
labels the skin carries. A new resource overlay translates 330+ strings: playback and subtitle menus, 3D and Dolby Vision
settings, speed/format error toasts, the third-party plugin dialogs and the list of 70 language names (subtitle/audio
track languages). `app_name` is left alone (the skin's value for it is the system label, not the player's)."""
import json, os, shutil, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_translation_batch24 as b24
import build_translation_batch21 as b21
import batch25_strings as T

ROOT, PAYLOAD, AUDIT = b21.ROOT, b21.PAYLOAD, b24.AUDIT
OUT = ROOT / 'investigation/translation-batch25-2026-10-13'
NEW_VERSION = '1.19.44'
TARGET, PACKAGE, FILE = 'com.xgimi.gimiplayer', 'com.beam.translation.gimiplayer', 'gimiplayer.apk'

def main():
    m = json.loads((ROOT / 'russifier/manifest.json').read_text(encoding='utf-8'))
    assert m['version'] in ('1.19.43', NEW_VERSION), m['version']
    OUT.mkdir(exist_ok=True)
    (OUT / 'before').mkdir(exist_ok=True)
    shutil.copyfile(ROOT / 'russifier/manifest.json', OUT / 'before/manifest.json')
    final = b24.prepare(TARGET, T.GIMIPLAYER, T.SKIN_KEYS)
    work = Path(os.environ['TEMP']) / 'beam-batch25'
    shutil.rmtree(work, ignore_errors=True)
    work.mkdir(parents=True)
    built = b21.build(FILE, PACKAGE, TARGET, final, work)
    shutil.copyfile(built, PAYLOAD / FILE)
    shutil.copyfile(built, OUT / FILE)
    m['files'][FILE] = b21.sha(built)
    m['originals'][TARGET] = {'path': '/vendor/priv-app/mediaPlayer_release838/mediaPlayer_release838.apk', 'sha256': b21.sha(AUDIT / (TARGET + '.apk'))}
    if not any(o['package'] == PACKAGE for o in m['overlays']):
        m['overlays'].append({'package': PACKAGE, 'target': TARGET, 'file': FILE})
    m.setdefault('resourceChecks', {}).setdefault(TARGET, {}).update({k: v.strip() for k, v in final.items()})
    m['version'] = NEW_VERSION
    (ROOT / 'russifier/manifest.json').write_text(json.dumps(m, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    (OUT / 'build-report.json').write_text(json.dumps({'version': NEW_VERSION, 'strings': len(final), 'sha256': m['files'][FILE]}, indent=2) + '\n', encoding='utf-8')
    print(FILE, len(final), 'strings; built', NEW_VERSION)

if __name__ == '__main__':
    main()
