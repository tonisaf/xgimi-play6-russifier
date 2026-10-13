"""Nineteenth batch: carry every skin-only string of the settings app in the Settings RRO.

Found on the real screen: the tooltip of the "Bluetooth visible to other devices" switch (`bluetooth_device_name_tip`)
was Chinese. The skin has the Russian text, but only widgets that go through SkinEngine read the skin; tooltips and
anything else that uses plain Resources get the stock Chinese value unless the RRO carries it too.
Batches 7, 8 and 12 added such keys by hand (toasts, messages). This batch closes the whole class: every string of the
original settings APK that has a Chinese value, is not in the RRO and has a Russian value in the skin is added to the RRO
with the skin's text. Skin-aware widgets still read the skin first, so nothing changes for them."""
from pathlib import Path
import json, re, shutil, subprocess
import xml.etree.ElementTree as ET
import build_photo_fixes as builder
import build_translation_batch7 as b7
import build_translation_batch12 as b12

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'investigation/translation-batch19-2026-10-13'
WORK = Path('C:/android/translation-batch19-20261013')
ORIGINAL_PANEL = Path('C:/android/panel-current-20261009-original.apk')
CJK = re.compile('[\u4e00-\u9fff]')

def string_values(apk):
    dump = subprocess.run([str(builder.BT / 'aapt2.exe'), 'dump', 'resources', str(apk)], capture_output=True, check=True).stdout.decode('utf-8', 'replace')
    values, cur = {}, None
    for line in dump.split('\n'):
        m = re.match(r'\s+resource 0x[0-9a-f]+ string/(\S+)', line)
        if m:
            cur = m.group(1)
            values.setdefault(cur, [])
            continue
        if re.match(r'\s+resource 0x', line):
            cur = None
            continue
        m = re.match(r'\s+\(([^)]*)\) "(.*)"', line)
        if m and cur:
            values[cur].append(m.group(2))
    return values

def main():
    m = json.loads((ROOT / 'russifier/manifest.json').read_text(encoding='utf-8'))
    assert m['version'] == '1.19.35'
    for name, digest in m['files'].items():
        assert builder.sha(ROOT / 'russifier/payload' / name) == digest, name
    OUT.mkdir(exist_ok=True)
    (OUT / 'before').mkdir(exist_ok=True)
    shutil.copyfile(ROOT / 'russifier/manifest.json', OUT / 'before/manifest.json')
    shutil.copyfile(ROOT / 'russifier/payload/settings.apk', OUT / 'before/settings.apk')
    if WORK.exists():
        shutil.rmtree(WORK)
    WORK.mkdir()

    panel = string_values(ORIGINAL_PANEL)
    rro = string_values(ROOT / 'russifier/payload/settings.apk')
    skin = {n.get('name'): n.text for n in ET.parse(ROOT / 'skin/res/values/strings.xml').getroot()}
    skin_only = {}
    for key, values in panel.items():
        if not any(CJK.search(v) for v in values) or key in rro:
            continue
        text = skin.get(key)
        if not text or CJK.search(text):
            continue
        original = next(v for v in values if CJK.search(v))
        # same number of format arguments as the stock string, otherwise the call site would crash
        if len(re.findall(r'%(?:\d+\$)?[sdf]', original)) != len(re.findall(r'%(?:\d+\$)?[sdf]', text)):
            continue
        skin_only[key] = text

    batch8 = {x['name']: x['ru'] for x in json.loads((ROOT / 'investigation/translation-batch8-2026-10-13/reviewed.json').read_text(encoding='utf-8'))}
    earlier = {**b7.TRANSLATIONS, **batch8, **{n: skin[n] for n in b12.SETTINGS_NEW}}
    changes = {**earlier, **{k: v for k, v in skin_only.items() if k not in earlier}}

    base = ROOT / '.local/table-20261012/overlays/settings-complete'
    fixed = ROOT / '.local/table-20261012/overlays/settings-fixed'
    if fixed.exists():
        shutil.rmtree(fixed)
    shutil.copytree(base, fixed)
    for layout in (fixed / 'res/layout').glob('*.xml'):
        layout.write_text(b7.PRIVATE.sub(lambda x: x.group(1) + x.group(2) + '*' + x.group(3), layout.read_text(encoding='utf-8')), encoding='utf-8')
    builder.OUT = OUT
    builder.WORK = WORK
    builder.VERSION, builder.VERSION_CODE = '1.19.36', 46
    built = builder.overlay('settings-fixed.apk', changes)
    target = OUT / 'settings.apk'
    shutil.copyfile(built, target)
    shutil.copyfile(target, ROOT / 'russifier/payload/settings.apk')
    m['files']['settings.apk'] = builder.sha(target)
    m['resourceChecks']['com.android.newsettings'].update({'bluetooth_device_name_tip': skin['bluetooth_device_name_tip']})
    m['version'] = '1.19.36'
    (ROOT / 'russifier/manifest.json').write_text(json.dumps(m, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    (OUT / 'build-report.json').write_text(json.dumps({'version': '1.19.36', 'added': len(skin_only), 'rroStrings': len(changes),
        'example': {k: skin_only[k] for k in list(skin_only)[:8]}}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('Built 1.19.36: skin-only keys added', len(skin_only), '| settings RRO changed strings', len(changes))

if __name__ == '__main__':
    main()
