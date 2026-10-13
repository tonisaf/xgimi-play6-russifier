"""Twenty-fourth batch (1.19.43): English-default strings of SystemUI, wireless screen and the XGIMI Assistant (vcontrol).

Audit of 2026-10-13: apps whose default language is English and that have no ru-RU show English for every string the
skin does not carry (found by a photo of GlobalConfig's hint; batches 21-23). Here: com.xgimi.systemui (+ the two
RRO files already used for it), com.xgimi.wirelessscreen and com.xgimi.vcontrol (a new RRO). Keys that hold JSON
configuration (`ambient_setting_data`, `resetTv`), QR identifiers and library accessibility strings are left alone.
Whitespace at the edges of a stock value (fragments glued to an icon or a number) is mirrored in the Russian text."""
import json, os, re, shutil, subprocess, sys
from pathlib import Path
import xml.etree.ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_photo_fixes as builder
import build_translation_batch21 as b21
import batch24_strings as T

ROOT, PAYLOAD, AUDIT = b21.ROOT, b21.PAYLOAD, Path('C:/android/audit')
OUT = ROOT / 'investigation/translation-batch24-2026-10-13'
WORK = Path('C:/android/translation-batch24-20261013')
NEW_VERSION = '1.19.43'
CJK = re.compile('[\u4e00-\u9fff]')
skin = {n.get('name'): n.text for n in ET.parse(ROOT / 'skin/res/values/strings.xml').getroot() if n.get('name')}

def version_code(apk):
    out = subprocess.run([str(builder.BT / 'aapt2.exe'), 'dump', 'badging', str(apk)], capture_output=True, check=True).stdout.decode('utf-8', 'replace')
    return int(re.search(r"versionCode='(\d+)'", out).group(1))

def prepare(target, texts, skin_keys=()):
    """Validate against the stock APK and mirror edge whitespace; returns the final key -> text."""
    stock = b21.stock_strings(AUDIT / (target + '.apk'))
    final = {}
    for key in skin_keys:
        original = stock[key].get('') or next(iter(stock[key].values()))
        text = skin.get(key)
        assert text and not CJK.search(text) and len(b21.args(text)) == len(b21.args(original)), key
        texts = {**texts, key: text}
    for key, text in texts.items():
        assert key in stock, (target, key)
        original = stock[key].get('') or next(iter(stock[key].values()))
        assert len(b21.args(original)) == len(b21.args(text)), (key, original, text)
        lead = original[:len(original) - len(original.lstrip())]
        trail = original[len(original.rstrip()):]
        final[key] = lead + text.strip() + trail
    return final

def extend_overlay(rro_file, changes, version_code_new):
    base = ROOT / '.local/table-20261012/overlays' / rro_file.removesuffix('.apk')
    if base.exists():
        shutil.rmtree(base)
    subprocess.run([str(builder.J / 'java.exe'), '-jar', str(builder.JAR), 'd', '-f', '-o', str(base), str(PAYLOAD / rro_file)], check=True, capture_output=True)
    builder.VERSION, builder.VERSION_CODE = NEW_VERSION, version_code_new
    return builder.overlay(rro_file, changes)

def main():
    m = json.loads((ROOT / 'russifier/manifest.json').read_text(encoding='utf-8'))
    assert m['version'] in ('1.19.42', NEW_VERSION), m['version']
    OUT.mkdir(exist_ok=True)
    (OUT / 'before').mkdir(exist_ok=True)
    shutil.copyfile(ROOT / 'russifier/manifest.json', OUT / 'before/manifest.json')
    shutil.rmtree(WORK, ignore_errors=True)
    WORK.mkdir(parents=True)
    builder.OUT, builder.WORK = OUT, WORK
    report = {}

    jobs = [('com.xgimi.systemui', 'systemui.apk', T.SYSTEMUI, T.SKIN_KEYS['systemui']),
            ('com.xgimi.wirelessscreen', 'wirelessscreen.apk', T.WIRELESSSCREEN, [])]
    for target, rro_file, texts, skin_keys in jobs:
        final = prepare(target, texts, skin_keys)
        shutil.copyfile(PAYLOAD / rro_file, OUT / 'before' / rro_file)
        built = extend_overlay(rro_file, final, version_code(PAYLOAD / rro_file) + 1)
        shutil.copyfile(built, PAYLOAD / rro_file)
        m['files'][rro_file] = builder.sha(built)
        m.setdefault('resourceChecks', {}).setdefault(target, {}).update({k: v.strip() for k, v in final.items()})
        report[rro_file] = {'added': len(final)}
        print(rro_file, '+', len(final), 'strings')

    # XGIMI Assistant (vcontrol): no RRO yet
    target, package, rro_file = 'com.xgimi.vcontrol', 'com.beam.translation.vcontrol', 'vcontrol.apk'
    final = prepare(target, T.VCONTROL)
    work = WORK / 'vcontrol'
    work.mkdir()
    built = b21.build(rro_file, package, target, final, work)
    shutil.copyfile(built, PAYLOAD / rro_file)
    shutil.copyfile(built, OUT / rro_file)
    m['files'][rro_file] = builder.sha(built)
    m['originals'][target] = {'path': '/vendor/priv-app/vcontrol_release838/vcontrol_release838.apk', 'sha256': builder.sha(AUDIT / (target + '.apk'))}
    if not any(o['package'] == package for o in m['overlays']):
        m['overlays'].append({'package': package, 'target': target, 'file': rro_file})
    m.setdefault('resourceChecks', {}).setdefault(target, {}).update({k: v.strip() for k, v in final.items()})
    report[rro_file] = {'added': len(final)}
    print(rro_file, len(final), 'strings')

    m['version'] = NEW_VERSION
    (ROOT / 'russifier/manifest.json').write_text(json.dumps(m, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    (OUT / 'build-report.json').write_text(json.dumps({'version': NEW_VERSION, **report}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('Built', NEW_VERSION)

if __name__ == '__main__':
    main()
