"""Twenty-first batch (1.19.40): three more applications get a resource overlay of their own.

Found on a user's photos after the first clean installation:
  * `com.xgimi.config` (GlobalConfig): the "input source" hint after plugging in HDMI — "Next time, you can quickly access
    the input source via Quick Settings / Press @ to view" — the stock APK has English as its default and no ru-RU;
  * `com.xgimi.xrmservice` (XRMService): on-screen toasts such as "即将切换至 HDMI，按 @ 取消" (HDMI switching), 3D and
    picture-mode warnings, panel messages;
  * `com.xgimi.soundermodeservice` (NewSounderMode): "即将切换至音响模式，按 @ 取消" with the two buttons.
None of the three had an RRO and none of their keys exist in the skin. `@` is replaced by the key icon in code and must stay.
The overlays are built from scratch (like the accessory overlays of 2026-10-08) and registered in the manifest with
resource checks for every string."""
from pathlib import Path
import hashlib, json, os, re, shutil, subprocess, zipfile
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'investigation/translation-batch21-2026-10-13'
PAYLOAD = ROOT / 'russifier/payload'
STOCK = Path('C:/android/probe-hdmi')
BT = Path('C:/android/sdk/build-tools/34.0.0')
ANDROID_JAR = 'C:/android/sdk/platforms/android-34/android.jar'
NEW_VERSION = '1.19.40'

# payload file -> (overlay package, target package, stock APK, strings)
APPS = {
    'config.apk': ('com.beam.translation.config', 'com.xgimi.config', 'GlobalConfig_release838.apk', {
        'hdmi_menu_title': 'В следующий раз вы сможете быстро открыть источник сигнала через «Быстрые настройки»',
        'hdmi_menu_press': 'Нажмите @, чтобы открыть',
        'hdmi_menu_long_press': 'Удерживайте @, чтобы открыть',
    }),
    'xrmservice.apk': ('com.beam.translation.xrmservice', 'com.xgimi.xrmservice', 'XRMService.apk', {
        'dlp_lumens_fail_by_3d': 'В режиме 3D регулировка яркости недоступна',
        'hd_fail_by_switch_colorstyle_non_fusion': 'Переключение стиля цвета на «Пользовательский» отключило адаптацию к цвету стены',
        'hd_fail_by_switch_picturemode_ambient': 'Смена режима отключила адаптацию к окружению',
        'hd_fail_by_switch_picturemode_ambient_light': 'Смена режима отключила адаптацию к окружающему свету',
        'hd_fail_by_switch_picturemode_brightness': 'Смена режима отключила адаптацию яркости',
        'hd_fail_by_switch_picturestyle_fusion': 'Переключение стиля изображения на «Пользовательский» отключило адаптацию к цвету стены',
        'hdmi_cancel_switch': 'Переключение отменено',
        'hdmi_switch_tip': 'Переключение на HDMI, нажмите “<img src=%d>” для отмены',
        'hdmi_switch_tip_v2': 'Переключение на %s, нажмите @ для отмены',
        'keypad_long_press_poweroff': 'Продолжайте удерживать для выключения',
        'panel_bond_success': 'Сопряжение выполнено',
        'panel_low_power': 'Низкий заряд батареи панели выключателя, замените батарею',
        'qn_clean': 'Очистка памяти завершена',
        'switch_3d_fail_by_alon': 'Отключите адаптацию к окружающему свету, чтобы использовать настройки 3D',
        'switch_3d_fail_by_hltest': 'Текущий режим не поддерживает переключение 3D',
    }),
    'soundermode.apk': ('com.beam.translation.soundermodeservice', 'com.xgimi.soundermodeservice', 'NewSounderMode.apk', {
        'cancel': 'Отмена',
        'ok': 'ОК',
        'title_confirm': 'Переключение в режим колонки, нажмите @ для отмены',
    }),
}

DEVICE_PATHS = {
    'com.xgimi.config': '/vendor/priv-app/GlobalConfig_release838/GlobalConfig_release838.apk',
    'com.xgimi.xrmservice': '/system/priv-app/XRMService/XRMService.apk',
    'com.xgimi.soundermodeservice': '/system/priv-app/NewSounderMode/NewSounderMode.apk',
}

def run(*args):
    subprocess.run([str(a) for a in args], check=True, capture_output=True)

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def stock_strings(apk):
    out = subprocess.run([str(BT / 'aapt2.exe'), 'dump', 'resources', str(apk)], capture_output=True, check=True).stdout.decode('utf-8', 'replace')
    values, cur = {}, None
    for line in out.split('\n'):
        m = re.match(r'\s+resource 0x[0-9a-f]+ (\w+)/(\S+)', line)
        if m:
            cur = m.group(2) if m.group(1) == 'string' else None
            if cur: values.setdefault(cur, {})
            continue
        m = re.match(r'\s+\(([^)]*)\) "(.*)"', line)
        if m and cur: values[cur][m.group(1)] = m.group(2)
    return values

def args(text):
    return re.findall(r'%(?:\d+\$)?[sdf]', text)

def build(payload_name, package, target, strings, work):
    res = work / 'res'
    for folder in ('values', 'values-ru', 'values-en', 'values-zh-rCN'):
        (res / folder).mkdir(parents=True, exist_ok=True)
        root = ET.Element('resources')
        for key, value in strings.items():
            ET.SubElement(root, 'string', {'name': key, 'formatted': 'false'}).text = ('"' + value + '"' if value != value.strip() else value.replace('\n', r'\n'))
        ET.indent(root)
        ET.ElementTree(root).write(res / folder / 'strings.xml', encoding='utf-8', xml_declaration=True)
    (res / 'xml').mkdir(exist_ok=True)
    mapping = ET.Element('overlay')
    for key in strings:
        ET.SubElement(mapping, 'item', {'target': 'string/' + key, 'value': '@string/' + key})
    ET.ElementTree(mapping).write(res / 'xml/overlays.xml', encoding='utf-8', xml_declaration=True)
    (work / 'AndroidManifest.xml').write_text(
        '<manifest xmlns:android="http://schemas.android.com/apk/res/android" package="' + package + '" android:versionCode="1" android:versionName="1.0">'
        '<uses-sdk android:minSdkVersion="30" android:targetSdkVersion="30"/><application android:hasCode="false" android:label="Beam: перевод"/>'
        '<overlay android:targetPackage="' + target + '" android:targetName="BeamTranslation" android:resourcesMap="@xml/overlays" android:isStatic="false" android:priority="999"/></manifest>',
        encoding='utf-8')
    run(BT / 'aapt2.exe', 'compile', '--dir', res, '-o', work / 'compiled.zip')
    run(BT / 'aapt2.exe', 'link', '-o', work / 'unsigned.apk', '-I', ANDROID_JAR, '--manifest', work / 'AndroidManifest.xml',
        '--package-id', '0x80', '--no-resource-deduping', '--no-resource-removal', work / 'compiled.zip')
    run(BT / 'zipalign.exe', '-f', '4', work / 'unsigned.apk', work / 'aligned.apk')
    signed = work / 'signed.apk'
    run(BT / 'apksigner.bat', 'sign', '--ks', Path.home() / '.android/debug.keystore', '--ks-pass', 'pass:android', '--key-pass', 'pass:android', '--out', signed, work / 'aligned.apk')
    run(BT / 'apksigner.bat', 'verify', signed)
    with zipfile.ZipFile(signed) as z:
        assert not any(n.endswith('.dex') for n in z.namelist()), payload_name
    return signed

def main():
    m = json.loads((ROOT / 'russifier/manifest.json').read_text(encoding='utf-8'))
    assert m['version'] in ('1.19.39', NEW_VERSION), m['version']
    OUT.mkdir(exist_ok=True)
    (OUT / 'before').mkdir(exist_ok=True)
    shutil.copyfile(ROOT / 'russifier/manifest.json', OUT / 'before/manifest.json')
    work_root = Path(os.environ['TEMP']) / 'beam-batch21'
    shutil.rmtree(work_root, ignore_errors=True)
    report = {}
    for payload_name, (package, target, stock_apk, strings) in APPS.items():
        stock = stock_strings(STOCK / stock_apk)
        for key, value in strings.items():
            assert key in stock, (target, key)
            original = stock[key].get('') or next(iter(stock[key].values()))
            assert args(original) == args(value), (key, original, value)
        work = work_root / payload_name
        work.mkdir(parents=True)
        built = build(payload_name, package, target, strings, work)
        shutil.copyfile(built, PAYLOAD / payload_name)
        shutil.copyfile(built, OUT / payload_name)
        m['files'][payload_name] = sha(built)
        # The boot restore checks every overlay target against its stock hash before touching idmaps.
        m['originals'][target] = {'path': DEVICE_PATHS[target], 'sha256': sha(STOCK / stock_apk)}
        if not any(o['package'] == package for o in m['overlays']):
            m['overlays'].append({'package': package, 'target': target, 'file': payload_name})
        checks = m.setdefault('resourceChecks', {}).setdefault(target, {})
        for key, value in strings.items():
            checks[key] = value
        report[payload_name] = {'package': package, 'target': target, 'strings': len(strings), 'sha256': m['files'][payload_name]}
        print(payload_name, len(strings), 'strings')
    m['version'] = NEW_VERSION
    (ROOT / 'russifier/manifest.json').write_text(json.dumps(m, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    (OUT / 'build-report.json').write_text(json.dumps({'version': NEW_VERSION, **report}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('Built', NEW_VERSION)

if __name__ == '__main__':
    main()
