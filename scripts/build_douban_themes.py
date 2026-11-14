"""Localize the hardcoded label and the artwork on the Play 6 theme picker."""

import argparse
import json
import re
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path

from build_douban_translation import ROOT, STOCK_SHA, TARGET, sha


PAYLOAD = 'douban-native.apk'
PICTURE = 'res/3W.webp'
DEX = 'classes5.dex'
STOCK_LABEL = r'"\u968f\u673a"'
LABEL_SITES = {
    'MenuView.smali': 'createLyricStyleItemCell',
    'PlayControlView$initView$2.smali': 'invoke',
}


def translate_label(path, method):
    source = path.read_text(encoding='utf-8')
    pattern = re.compile(
        rf'^\.method [^\n]*\b{re.escape(method)}\([^\n]*\n.*?^\.end method$',
        re.MULTILINE | re.DOTALL,
    )
    sites = [match for match in pattern.finditer(source) if STOCK_LABEL in match[0]]
    if len(sites) != 1 or sites[0][0].count(STOCK_LABEL) != 1:
        raise ValueError(f'Unexpected theme label in {path.name}')
    site = sites[0]
    path.write_text(
        source[:site.start()] + site[0].replace(STOCK_LABEL, '"Случайно"') + source[site.end():],
        encoding='utf-8',
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stock_apk', type=Path)
    parser.add_argument('decoded_dex', type=Path)
    options = parser.parse_args()
    if sha(options.stock_apk) != STOCK_SHA:
        parser.error('Expected the stock Play 6 v1.7.116 music player APK')
    manifest_path = ROOT / 'russifier/manifest.json'
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    if manifest['version'] not in ('1.19.49', '1.19.50'):
        raise ValueError(f"Unexpected base version: {manifest['version']}")

    jar = ROOT / '.local/build-tools/apktool-2.10.0.jar'
    java = Path('C:/android/jdk/bin')
    picture = Path(__file__).with_name('douban-other-themes.webp').read_bytes()
    with tempfile.TemporaryDirectory(dir=ROOT / '.local/build') as directory:
        work = Path(directory)
        smali = work / 'smali'
        shutil.copytree(options.decoded_dex, smali)
        for filename, method in LABEL_SITES.items():
            translate_label(smali / 'com/xgimi/playpage/view' / filename, method)
        source = work / 'BuildDex.java'
        shutil.copyfile(Path(__file__).with_name('BuildAtmosphereDex.java'), source)
        subprocess.run([java/'javac.exe', '-cp', jar, '-d', work, source], check=True)
        subprocess.run(
            [java/'java.exe', '-cp', f'{jar};{work}', 'BuildDex', smali, work/DEX],
            check=True,
        )
        apk = work / PAYLOAD
        replacements = {DEX: (work/DEX).read_bytes(), PICTURE: picture}
        with zipfile.ZipFile(options.stock_apk) as stock, zipfile.ZipFile(apk, 'w') as output:
            for entry in stock.infolist():
                content = replacements.get(entry.filename)
                output.writestr(entry, stock.read(entry.filename) if content is None else content)
        with zipfile.ZipFile(options.stock_apk) as stock, zipfile.ZipFile(apk) as output:
            changed = {name for name in stock.namelist() if stock.read(name) != output.read(name)}
            if stock.namelist() != output.namelist() or changed != set(replacements):
                raise ValueError(f'Unexpected APK changes: {changed}')
        digest = sha(apk)
        shutil.copyfile(apk, ROOT / 'russifier/payload' / PAYLOAD)

    manifest['files'][PAYLOAD] = digest
    if not any(item['target'] == TARGET for item in manifest['runtimePatches']):
        manifest['runtimePatches'].append({
            'target': TARGET,
            'file': PAYLOAD,
            'backing': '/data/local/tmp/beam-russifier-douban-themes.apk',
        })
    manifest['version'] = '1.19.50'
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'{PAYLOAD}: {digest}')


if __name__ == '__main__':
    main()
