"""Build photo-confirmed UI fixes on the checksum-verified 1.19.15 payload."""
from pathlib import Path
import hashlib, json, os, re, shutil, subprocess, zipfile
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'investigation/photo-fixes-2026-10-12'
WORK = Path('C:/android/photo-fixes-20261012')
BT = Path('C:/android/sdk/build-tools/34.0.0')
J = Path('C:/android/jdk/bin')
JAR = ROOT / '.local/build-tools/apktool-2.10.0.jar'
VERSION = '1.19.16'
VERSION_CODE = 36

SYSTEMUI = {
    'custom_key_guide_title': 'Кнопка быстрого доступа',
    'custom_key_guide_desc': 'Назначьте кнопке быстрого доступа на пульте нужное действие',
    'custom_key_guide_btn_user': 'Настроить кнопку',
    'custom_key_guide_btn_cancel': 'Отмена',
    'custom_key_guide_btn_sound': 'Режим колонки (по умолчанию)',
    'custom_key_guide_btn_screen_memory': 'Память экрана (по умолчанию)',
    'custom_key_guide_btn_smart_space': 'Динамическая стена (по умолчанию)',
    'custom_key_setting_title': 'Настройка кнопки',
    'custom_key_setting_desc': 'Выберите действие для кнопки быстрого доступа на пульте',
    'custom_key_setting_btn_ambient_guide': 'Подсветка колонки (по умолчанию)',
    'custom_key_setting_btn_ambient': 'Подсветка колонки',
    'custom_key_setting_ambient_define': 'Переключение подсветки',
    'custom_key_setting_btn_source': 'Источник сигнала',
    'custom_key_setting_btn_save': 'Готово',
    'custom_key_setting_btn_sound': 'Режим колонки',
    'custom_key_setting_btn_my_app': 'Мои приложения',
    'custom_key_setting_btn_atmosphere': 'Динамический экран',
    'custom_key_smart_space_desc': 'Динамическая стена',
    'custom_key_smart_space_title': 'Динамическая стена',
    'warn_btn_ok': 'Понятно',
}
AMBIENT = {
    'ambient_light_study_dialog_title': 'Цвет подсветки',
    'ambient_light_study_dialog_desc': 'В режиме колонки нажимайте кнопку быстрого доступа, чтобы менять цвет или выключать подсветку',
}

def run(*args):
    subprocess.run(list(map(str, args)), check=True, env={**os.environ, 'JAVA_HOME': 'C:/android/jdk'})

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def patch_literals(p, replacements):
    s = p.read_text(encoding='utf-8')
    for old, new in replacements.items():
        literal = json.dumps(old, ensure_ascii=True)
        assert s.count(literal) == 1, (p, old, s.count(literal))
        s = s.replace(literal, json.dumps(new, ensure_ascii=False))
    p.write_text(s, encoding='utf-8')

def dex_patch(name, decoded, changes):
    smali = Path(decoded) / 'smali_classes2'
    changes(smali)
    dex = WORK / (name + '.dex')
    run(J/'java.exe', '-Xmx2g', '-cp', str(JAR)+';'+str(WORK), 'BuildDex', smali, dex)
    target = OUT/name
    with zipfile.ZipFile(OUT/'before'/name) as src, zipfile.ZipFile(target, 'w') as dst:
        for entry in src.infolist():
            dst.writestr(entry, dex.read_bytes() if entry.filename == 'classes2.dex' else src.read(entry.filename))
    with zipfile.ZipFile(OUT/'before'/name) as src, zipfile.ZipFile(target) as dst:
        assert src.namelist() == dst.namelist()
        assert [n for n in src.namelist() if src.read(n) != dst.read(n)] == ['classes2.dex']
    return target

def panel_changes(smali):
    patch_literals(smali/'com/xgimi/bluetooth/receiver/BluPairRequestReceiver.smali', {
        '“': '«', '” 请求蓝牙配对': '» запрашивает сопряжение по Bluetooth',
        '请确认以下配对码显示在“': 'Убедитесь, что этот код сопряжения отображается на устройстве «', '”': '»',
    })
    patch_literals(smali/'com/xgimi/bluetooth/dialog/BluetoothDevicesPairDialog.smali', {
        '配对': 'Сопряжение', '取消': 'Отмена', '正在配对': 'Выполняется сопряжение',
    })

def systemui_changes(smali):
    p = smali/'com/xgimi/systemui/ui/dialog/ExpandViewModel.smali'
    s = p.read_text(encoding='utf-8')
    clones = []
    for declaration in ['.method public final createTitleCell(', '.method public static synthetic createTitleCell$default(']:
        start = s.index(declaration)
        end = s.index('.end method', start)+len('.end method')
        clone = s[start:end].replace('createTitleCell', 'createBeamTitleCell')
        if '$default(' not in declaration:
            assert clone.count('const/high16 v3, 0x42780000') == 1
            clone = clone.replace('const/high16 v3, 0x42780000', 'const/high16 v3, 0x42400000') # 48px
            assert clone.count('const/16 v3, 0xa') == 1
            clone = clone.replace('const/16 v3, 0xa', 'const/16 v3, 0x1') # one line within fixed slot
        clones.append(clone)
    p.write_text(s+'\n\n'+'\n\n'.join(clones)+'\n', encoding='utf-8')
    p = smali/'com/xgimi/systemui/remote/RemoteDialogFactory.smali'
    s = p.read_text(encoding='utf-8')
    for method in ['openCustomKeyGuide', 'openCustomKeySetting']:
        start = s.index('.method public final '+method+'()V')
        end = s.index('.end method', start)
        body = s[start:end]
        assert body.count('->createTitleCell$default(') == 1, method
        s = s[:start]+body.replace('->createTitleCell$default(', '->createBeamTitleCell$default(')+s[end:]
    p.write_text(s, encoding='utf-8')
    p = smali/'com/xgimi/systemui/ambientlight/AmbientLightStudyActivity.smali'
    s = p.read_text(encoding='utf-8')
    assert s.count('->createTitleCell(') == 1
    p.write_text(s.replace('->createTitleCell(', '->createBeamTitleCell('), encoding='utf-8')

def overlay(name, changes):
    base = ROOT/'.local/table-20261012/overlays'/name.removesuffix('.apk')
    work = WORK/name.removesuffix('.apk')
    shutil.copytree(base/'res', work/'res', dirs_exist_ok=True)
    for p in (work/'res').glob('values*/public.xml'):
        p.unlink()
    for folder in (work/'res').glob('values*'):
        p = folder/'strings.xml'
        if not p.exists(): continue
        tree = ET.parse(p)
        for key, value in changes.items():
            node = next((n for n in tree.getroot() if n.get('name') == key), None)
            if node is None: node = ET.SubElement(tree.getroot(), 'string', {'name':key})
            node.text = '"'+value+'"' if value != value.strip() else value
        tree.write(p, encoding='utf-8', xml_declaration=True)
    p = work/'res/xml/overlays.xml'
    tree = ET.parse(p)
    for key in changes:
        if not any(n.get('target') == 'string/'+key for n in tree.getroot()):
            ET.SubElement(tree.getroot(), 'item', {'target':'string/'+key, 'value':'@string/'+key})
    tree.write(p, encoding='utf-8', xml_declaration=True)
    tree = ET.parse(base/'AndroidManifest.xml')
    android = '{http://schemas.android.com/apk/res/android}'
    tree.getroot().set(android+'versionCode', str(VERSION_CODE))
    tree.getroot().set(android+'versionName', VERSION)
    sdk = tree.getroot().find('uses-sdk')
    if sdk is None: sdk = ET.SubElement(tree.getroot(), 'uses-sdk')
    sdk.set(android+'minSdkVersion', '30'); sdk.set(android+'targetSdkVersion', '30')
    ET.register_namespace('android', android[1:-1])
    tree.write(work/'AndroidManifest.xml', encoding='utf-8', xml_declaration=True)
    run(BT/'aapt2.exe', 'compile', '--dir', work/'res', '-o', work/'compiled.zip')
    run(BT/'aapt2.exe', 'link', '-o', work/'unsigned.apk', '-I', 'C:/android/sdk/platforms/android-34/android.jar', '--manifest', work/'AndroidManifest.xml', '--package-id', '0x80', '--no-resource-deduping', '--no-resource-removal', work/'compiled.zip')
    run(BT/'zipalign.exe', '-f', '4', work/'unsigned.apk', work/'aligned.apk')
    target = OUT/name
    run(BT/'apksigner.bat', 'sign', '--ks', Path.home()/'.android/debug.keystore', '--ks-pass', 'pass:android', '--key-pass', 'pass:android', '--out', target, work/'aligned.apk')
    run(BT/'apksigner.bat', 'verify', target)
    dump = subprocess.check_output([str(BT/'aapt2.exe'), 'dump', 'resources', str(target)]).decode('utf-8')
    for key, value in changes.items():
        # values written with quotes or backslash escapes are unescaped by aapt2, so compare the key then
        assert value in dump or (re.search(r'["\\]', value) and 'string/'+key in dump), (name, key, value)
    # Every previous locale/string and overlay target must survive this additive rebuild.
    for old in (base/'res').glob('values*/strings.xml'):
        new = ET.parse(work/'res'/old.parent.name/'strings.xml')
        values = {n.get('name'):n.text for n in new.getroot()}
        for n in ET.parse(old).getroot():
            if n.get('name') not in changes: assert values[n.get('name')] == n.text
    return target

def main():
    m = json.loads((ROOT/'russifier/manifest.json').read_text(encoding='utf-8'))
    assert m['version'] == '1.19.15'
    OUT.mkdir(exist_ok=False)
    (OUT/'before').mkdir()
    WORK.mkdir(exist_ok=False)
    for name, digest in m['files'].items(): assert sha(ROOT/'russifier/payload'/name) == digest, name
    (OUT/'before/manifest.json').write_text(json.dumps(m, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    for name in ['panel.apk', 'systemui-native.apk', 'systemui.apk', 'ambient.apk']:
        shutil.copyfile(ROOT/'russifier/payload'/name, OUT/'before'/name)
    shutil.copyfile(ROOT/'scripts/BuildAtmosphereDex.java', WORK/'BuildDex.java')
    run(J/'javac.exe', '-cp', JAR, '-d', WORK, WORK/'BuildDex.java')
    # Original Play6 names gate new RRO mappings; Titan-only features are excluded.
    original = ET.parse(ROOT/'investigation/titan-2026-10-12/comparison/decoded/play6-systemui/res/values/strings.xml')
    keys = {n.get('name') for n in original.getroot()}
    assert set(SYSTEMUI)|set(AMBIENT) <= keys
    outputs = [dex_patch('panel.apk', 'C:/android/photo-panel-20261012', panel_changes),
               dex_patch('systemui-native.apk', 'C:/android/photo-systemui-20261012', systemui_changes),
               overlay('systemui.apk', SYSTEMUI), overlay('ambient.apk', AMBIENT)]
    previous = m['files']['panel.apk']
    if previous not in m['previousPanelHashes']: m['previousPanelHashes'].append(previous)
    systemui = next(p for p in m['runtimePatches'] if p['file'] == 'systemui-native.apk')
    hashes = systemui.setdefault('previousHashes', [])
    if m['files']['systemui-native.apk'] not in hashes:
        hashes.append(m['files']['systemui-native.apk'])
    for p in outputs:
        shutil.copyfile(p, ROOT/'russifier/payload'/p.name)
        m['files'][p.name] = sha(p)
    m['version'] = VERSION
    m['resourceChecks'].setdefault('com.xgimi.systemui', {}).update({**SYSTEMUI, **AMBIENT})
    (ROOT/'russifier/manifest.json').write_text(json.dumps(m, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    (OUT/'build-report.json').write_text(json.dumps({'version':VERSION, 'systemui':SYSTEMUI, 'ambient':AMBIENT, 'changedFiles':{p.name:sha(p) for p in outputs}, 'nativeChangedEntries':['classes2.dex'], 'titleFontSize':48, 'titleMaxLines':1, 'deviceTested':False}, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print('Built '+VERSION+'; 4 payload files updated; only classes2.dex changed in native APKs.')

if __name__ == '__main__': main()
