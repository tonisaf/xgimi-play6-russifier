"""Twentieth batch: skin-only strings of the other applications go into their RROs too.

Same class as batch 19 (settings): the skin carries the Russian text, but code and widgets that use plain Resources
see the stock Chinese value unless the app's RRO has it. For every RRO application: strings of the stock APK whose
shown value is Chinese, that are not in the RRO and have a Russian value in the skin (same number of format
arguments) are added with the skin's text. Two atmosphere screensaver messages exist nowhere and are translated here.
Left alone: JSON-in-string configuration values (`feature`, `resetTv`, ...) that are keys, and strings that have no
Russian text anywhere (ota.accessories, user, smartaccessories, xgimiiotserver: applications that were skipped)."""
from pathlib import Path
import json, re, shutil, subprocess
import xml.etree.ElementTree as ET
import build_photo_fixes as builder

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'investigation/translation-batch20-2026-10-13'
WORK = Path('C:/android/translation-batch20-20261013')
PULLED = Path('C:/Users/USER/AppData/Local/Temp/claude/C--Users-USER-TileLauncher/a706dd4d-6a8b-4c5d-a430-38c6bdaad0bc/scratchpad/other')
CJK = re.compile('[\u4e00-\u9fff]')
PAYLOAD = ROOT / 'russifier/payload'

# RRO payload file -> (stock APK whose resources the RRO overlays, manifest resourceChecks package)
APPS = {
    'systemui.apk': PAYLOAD / 'systemui-native.apk',
    'atmosphere.apk': PAYLOAD / 'atmosphere-native.apk',
    'shutdown.apk': PULLED / 'shutdown.apk',
    'ota.accessories.apk': PULLED / 'ota.accessories.apk',
    'smartaccessories.apk': PULLED / 'smartaccessories.apk',
    'xgimiiotserver.apk': PULLED / 'xgimiiotserver.apk',
    'user.apk': PULLED / 'user.apk',
}
EXTRA = {
    'atmosphere.apk': {'switch_screensaver_no_more_tips': 'Загрузка других заставок...', 'switch_screensaver_no_net_tips': 'Нет подключения к сети'},
}

def string_values(apk):
    dump = subprocess.run([str(builder.BT / 'aapt2.exe'), 'dump', 'resources', str(apk)], capture_output=True, check=True).stdout.decode('utf-8', 'replace')
    values, cur = {}, None
    for line in dump.split('\n'):
        m = re.match(r'\s+resource 0x[0-9a-f]+ string/(\S+)', line)
        if m:
            cur = m.group(1)
            values.setdefault(cur, {})
            continue
        if re.match(r'\s+resource 0x', line):
            cur = None
            continue
        m = re.match(r'\s+\(([^)]*)\) "(.*)"', line)
        if m and cur:
            values[cur][m.group(1)] = m.group(2)
    return values

def version_code(apk):
    out = subprocess.run([str(builder.BT / 'aapt2.exe'), 'dump', 'badging', str(apk)], capture_output=True, check=True).stdout.decode('utf-8', 'replace')
    return int(re.search(r"versionCode='(\d+)'", out).group(1))

def args(text):
    return len(re.findall(r'%(?:\d+\$)?[sdf]', text))

def main():
    m = json.loads((ROOT / 'russifier/manifest.json').read_text(encoding='utf-8'))
    assert m['version'] == '1.19.36'
    for name, digest in m['files'].items():
        assert builder.sha(PAYLOAD / name) == digest, name
    OUT.mkdir(exist_ok=True)
    (OUT / 'before').mkdir(exist_ok=True)
    shutil.copyfile(ROOT / 'russifier/manifest.json', OUT / 'before/manifest.json')
    if WORK.exists():
        shutil.rmtree(WORK)
    WORK.mkdir()
    skin = {n.get('name'): n.text for n in ET.parse(ROOT / 'skin/res/values/strings.xml').getroot()}
    report = {}
    builder.OUT = OUT
    builder.WORK = WORK
    for rro_file, stock_apk in APPS.items():
        shutil.copyfile(PAYLOAD / rro_file, OUT / 'before' / rro_file)
        stock, rro = string_values(stock_apk), string_values(PAYLOAD / rro_file)
        changes = dict(EXTRA.get(rro_file, {}))
        for key, cfgs in stock.items():
            if not cfgs:
                continue
            shown = cfgs.get('ru') or cfgs.get('') or next(iter(cfgs.values()))
            if not CJK.search(shown) or key in changes:
                continue
            have = rro.get(key)
            if have and any(not CJK.search(v) for v in have.values()):
                continue
            text = skin.get(key)
            if not text or CJK.search(text) or args(text) != args(shown):
                continue
            changes[key] = text
        if not changes:
            print(rro_file, 'nothing to add')
            continue
        base = ROOT / '.local/table-20261012/overlays' / rro_file.removesuffix('.apk')
        if base.exists():
            shutil.rmtree(base)
        subprocess.run([str(builder.J / 'java.exe'), '-jar', str(builder.JAR), 'd', '-f', '-o', str(base), str(PAYLOAD / rro_file)], check=True, capture_output=True)
        builder.VERSION, builder.VERSION_CODE = '1.19.37', version_code(PAYLOAD / rro_file) + 1
        built = builder.overlay(rro_file, changes)
        shutil.copyfile(built, PAYLOAD / rro_file)
        m['files'][rro_file] = builder.sha(built)
        report[rro_file] = {'added': len(changes), 'keys': sorted(changes)}
        print(rro_file, '+', len(changes), 'strings, versionCode', builder.VERSION_CODE)
    m['version'] = '1.19.37'
    (ROOT / 'russifier/manifest.json').write_text(json.dumps(m, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    (OUT / 'build-report.json').write_text(json.dumps({'version': '1.19.37', **report}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('Built 1.19.37')

if __name__ == '__main__':
    main()
