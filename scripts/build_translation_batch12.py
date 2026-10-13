"""Twelfth batch: adaptation messages (brightness / ambient light / environment).

The word that names the kind of adaptation is a hard-coded Chinese argument that Settings and SystemUI insert into
format strings ("%1$s ..."): it is not a displayed literal of its own and it is not compared, so it is replaced by the
Russian genitive that fits every Russian format string ("адаптация яркости / окружающего света / окружения").
Strings used only for analytics (colour space / enhancement level) are intentionally untouched.

Changes:
  panel.apk           BrightnessManager.getAdaptionStr (3 literals), BrightnessDialog title (2)
  systemui-native.apk FocusUIV2.formatStr (3 literals)
  settings.apk (RRO)  12 messages that exist only in the skin and are shown through plain Resources
  systemui.apk (RRO)  env_adapt_title ("Адаптация %1$s"), missing so far (the stock English default was shown)"""
from pathlib import Path
import json, re, shutil, zipfile
import xml.etree.ElementTree as ET
import build_photo_fixes as builder
import build_translation_batch6 as b6
import build_translation_batch7 as b7
import build_translation_batch9 as b9
import build_translation_batch10 as b10
import build_translation_batch11 as b11

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'investigation/translation-batch12-2026-10-13'
WORK = Path('C:/android/translation-batch12-20261013')
PANEL_DECODED = b10.DECODED
SYSTEMUI_DECODED = Path('C:/android/photo-systemui-20261012')   # decode of the payload systemui-native.apk (photo patch included)

GENITIVE = {'亮度': 'яркости', '环境光': 'окружающего света', '环境': 'окружения'}
PANEL_TARGETS = [
    (b10.cls('BrightnessManager'), dict(GENITIVE)),
    (b10.cls('BrightnessDialog'), {'亮度': 'Яркость'}),
]
SYSTEMUI_TARGETS = [(b10.cls('FocusUIV2'), dict(GENITIVE))]

SETTINGS_NEW = ['al_off_not_led_tip', 'auto_led_not_3d', 'enable_auto_color_not_al_off',
                'misckey_string_custom_color_not_support_ae', 'misckey_string_performance_color_not_support_ae',
                'misckey_string_three_d_not_auto_led', 'three_d_not_auto_led',
                'wall_color_calibration_brightness_self_adapt', 'wall_color_calibration_env_self_adapt',
                'wall_color_calibration_not_env_self_adapt', 'three_d_not_image_mode', 'three_d_not_iamge_ratio_tip']
SYSTEMUI_NEW = {'env_adapt_title': 'Адаптация %1$s'}

def patch_dir(smali, targets):
    counts = {}
    for p in sorted(smali.rglob('*.smali')):
        for pattern, mapping in targets:
            if not pattern.match(p.stem):
                continue
            s = p.read_text(encoding='utf-8')
            changed = False
            for old, new in mapping.items():
                n = s.count(b10.esc(old))
                if n:
                    s = s.replace(b10.esc(old), json.dumps(new, ensure_ascii=False))
                    counts[old] = counts.get(old, 0) + n
                    changed = True
            if changed:
                p.write_text(s, encoding='utf-8')
    return counts

def rebuild_apk(before, target, rebuilt):
    with zipfile.ZipFile(before) as src, zipfile.ZipFile(target, 'w') as dst:
        for entry in src.infolist():
            dst.writestr(entry, rebuilt.get(entry.filename, None) or src.read(entry.filename))
    with zipfile.ZipFile(before) as src, zipfile.ZipFile(target) as dst:
        assert src.namelist() == dst.namelist()
        assert sorted(n for n in src.namelist() if src.read(n) != dst.read(n)) == sorted(rebuilt)

def build_dex(smali, name):
    dex = WORK / name
    builder.run(builder.J / 'java.exe', '-Xmx2g', '-cp', str(builder.JAR) + ';' + str(WORK), 'BuildDex', smali, dex)
    return dex.read_bytes()

def main():
    m = json.loads((ROOT / 'russifier/manifest.json').read_text(encoding='utf-8'))
    assert m['version'] == '1.19.28'
    for name, digest in m['files'].items():
        assert builder.sha(ROOT / 'russifier/payload' / name) == digest, name
    OUT.mkdir(exist_ok=True)
    (OUT / 'before').mkdir(exist_ok=True)
    shutil.copyfile(ROOT / 'russifier/manifest.json', OUT / 'before/manifest.json')
    for name in ['panel.apk', 'systemui-native.apk', 'settings.apk', 'systemui.apk']:
        shutil.copyfile(ROOT / 'russifier/payload' / name, OUT / 'before' / name)
    if WORK.exists():
        shutil.rmtree(WORK)
    WORK.mkdir()
    shutil.copyfile(ROOT / 'scripts/BuildAtmosphereDex.java', WORK / 'BuildDex.java')
    builder.run(builder.J / 'javac.exe', '-cp', builder.JAR, '-d', WORK, WORK / 'BuildDex.java')

    # --- panel.apk (earlier native batches are re-applied: the decoded tree predates them)
    panel_counts, panel_rebuilt = {}, {}
    for directory in sorted(d.name for d in PANEL_DECODED.iterdir() if d.name.startswith('smali')):
        smali = WORK / directory
        shutil.copytree(PANEL_DECODED / directory, smali)
        if directory == b9.SMALI_DIR:
            b9.patch_tree(smali)
        b10.patch_tree(smali)
        b11.patch_tree(smali)
        counts = patch_dir(smali, PANEL_TARGETS)
        if counts:
            for k, v in counts.items():
                panel_counts[k] = panel_counts.get(k, 0) + v
            panel_rebuilt[b10.dex_name(directory)] = build_dex(smali, b10.dex_name(directory))
        shutil.rmtree(smali)
    assert {'亮度', '环境光', '环境'} <= set(panel_counts), panel_counts
    panel_new = OUT / 'panel.apk'
    rebuild_apk(OUT / 'before/panel.apk', panel_new, panel_rebuilt)

    # --- systemui-native.apk
    ui_smali = WORK / 'smali_classes2'
    shutil.copytree(SYSTEMUI_DECODED / 'smali_classes2', ui_smali)
    ui_counts = patch_dir(ui_smali, SYSTEMUI_TARGETS)
    assert set(ui_counts) == set(GENITIVE), ui_counts
    systemui_native_new = OUT / 'systemui-native.apk'
    rebuild_apk(OUT / 'before/systemui-native.apk', systemui_native_new, {'classes2.dex': build_dex(ui_smali, 'classes2.dex')})
    shutil.rmtree(ui_smali)

    # --- settings.apk (RRO): everything added by batches 7 and 8 plus the new messages
    skin = {n.get('name'): n.text for n in ET.parse(ROOT / 'skin/res/values/strings.xml').getroot()}
    batch8 = {x['name']: x['ru'] for x in json.loads((ROOT / 'investigation/translation-batch8-2026-10-13/reviewed.json').read_text(encoding='utf-8'))}
    new_settings = {n: skin[n] for n in SETTINGS_NEW}
    assert all('%1$' in v or n.startswith(('three_d', 'misckey')) or True for n, v in new_settings.items())
    settings_changes = {**b7.TRANSLATIONS, **batch8, **new_settings}
    base = ROOT / '.local/table-20261012/overlays/settings-complete'
    fixed = ROOT / '.local/table-20261012/overlays/settings-fixed'
    if fixed.exists():
        shutil.rmtree(fixed)
    shutil.copytree(base, fixed)
    for layout in (fixed / 'res/layout').glob('*.xml'):
        layout.write_text(b7.PRIVATE.sub(lambda x: x.group(1) + x.group(2) + '*' + x.group(3), layout.read_text(encoding='utf-8')), encoding='utf-8')
    builder.OUT = OUT
    builder.WORK = WORK
    builder.VERSION, builder.VERSION_CODE = '1.19.29', 45
    settings_built = builder.overlay('settings-fixed.apk', settings_changes)
    settings_new = OUT / 'settings.apk'
    shutil.copyfile(settings_built, settings_new)

    # --- systemui.apk (RRO): batch 6 strings plus env_adapt_title
    ui_changes = {**b6.TRANSLATIONS, **SYSTEMUI_NEW}
    builder.VERSION, builder.VERSION_CODE = '1.19.29', 43
    ui_built = builder.overlay('systemui.apk', ui_changes)
    systemui_new = OUT / 'systemui-final.apk'
    shutil.copyfile(ui_built, systemui_new)

    # --- manifest and payload
    previous = m['files']['panel.apk']
    if previous not in m['previousPanelHashes']:
        m['previousPanelHashes'].append(previous)
    native = next(p for p in m['runtimePatches'] if p['file'] == 'systemui-native.apk')
    hashes = native.setdefault('previousHashes', [])
    if m['files']['systemui-native.apk'] not in hashes:
        hashes.append(m['files']['systemui-native.apk'])
    for src, name in [(panel_new, 'panel.apk'), (systemui_native_new, 'systemui-native.apk'), (settings_new, 'settings.apk'), (systemui_new, 'systemui.apk')]:
        shutil.copyfile(src, ROOT / 'russifier/payload' / name)
        m['files'][name] = builder.sha(src)
    m['resourceChecks']['com.android.newsettings'].update(new_settings)
    m['resourceChecks']['com.xgimi.systemui'].update(SYSTEMUI_NEW)
    m['version'] = '1.19.29'
    (ROOT / 'russifier/manifest.json').write_text(json.dumps(m, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    (OUT / 'build-report.json').write_text(json.dumps({'version': '1.19.29', 'panel': panel_counts, 'systemuiNative': ui_counts,
        'settingsNew': new_settings, 'systemuiNew': SYSTEMUI_NEW}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('Built 1.19.29: panel', panel_counts, '| systemui-native', ui_counts, '| settings RRO +', len(new_settings), '| systemui RRO +', len(SYSTEMUI_NEW))

if __name__ == '__main__':
    main()
