"""Ninth batch: hard-coded Chinese literals of the zoom / shift screen in Settings (classes3.dex of panel.apk).

Toasts, tab titles and guide hints of this screen are string constants in the code, so neither the skin nor
the RRO can reach them. Only literals in the listed classes are patched; every replacement keeps all
equality checks inside the same class consistent (the same literal is replaced everywhere in that class)."""
from pathlib import Path
import hashlib, json, os, re, shutil, subprocess, zipfile
import build_photo_fixes as builder

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'investigation/translation-batch9-2026-10-13'
WORK = Path('C:/android/translation-batch9-20261013')
DECODED = Path('C:/android/photo-panel-20261012')          # apktool decode of the current payload panel.apk
DEX_ENTRY = 'classes3.dex'
SMALI_DIR = 'smali_classes3'

LIMITS = {
    '已调整到最大': 'Достигнут максимум', '已调整到最小': 'Достигнут минимум',
    '已调整到最左': 'Достигнут левый предел', '已调整到最右': 'Достигнут правый предел',
    '已调整到最高': 'Достигнут верхний предел', '已调整到最低': 'Достигнут нижний предел',
}
SCREEN = {
    '按OK切换功能': 'Нажмите OK для переключения', '按左右缩放': 'Влево/вправо — масштаб',
    '长按恢复默认画面': 'Удерживайте для сброса изображения', '按方向键位移': 'Стрелки — сдвиг',
    '缩放': 'Масштаб', '位移': 'Сдвиг',
    '光学无损': 'Оптика без потерь', '数码缩放': 'Цифровой зум', '光学移轴': 'Оптический сдвиг',
    '光学': 'Оптический', '数码': 'Цифровой',
}
# class-name patterns (file name without .smali) -> literals allowed there
TARGETS = [
    (re.compile(r'^(DigitalDisplacementWind|OpticsZoomShiftWind|ZoomDisplacementWind|ZoomStateView|PtzViewModel)(\$.*)?$'), LIMITS),
    (re.compile(r'^GuideZoomMoveView(\$.*)?$'), {k: SCREEN[k] for k in ['按OK切换功能', '按左右缩放', '长按恢复默认画面', '按方向键位移']}),
    (re.compile(r'^TabListView(\$.*)?$'), {k: SCREEN[k] for k in ['缩放', '位移']}),
    (re.compile(r'^ZoomMoveAutoTextView(\$.*)?$'), {k: SCREEN[k] for k in ['光学无损', '数码缩放', '光学移轴']}),
    (re.compile(r'^(ZoomDisplacementWind|ZoomStateView)\$initZoom\$1\$1$'), {k: SCREEN[k] for k in ['光学', '数码']}),
]

def esc(text):
    return json.dumps(text, ensure_ascii=True)       # smali stores non-ASCII as \uXXXX

def patch_tree(smali):
    counts = {}
    for p in sorted(smali.rglob('*.smali')):
        for pattern, mapping in TARGETS:
            if not pattern.match(p.stem):
                continue
            s = p.read_text(encoding='utf-8')
            changed = False
            for old, new in mapping.items():
                n = s.count(esc(old))
                if n:
                    s = s.replace(esc(old), json.dumps(new, ensure_ascii=False))
                    counts[old] = counts.get(old, 0) + n
                    changed = True
            if changed:
                p.write_text(s, encoding='utf-8')
    return counts

def main():
    m = json.loads((ROOT / 'russifier/manifest.json').read_text(encoding='utf-8'))
    assert m['version'] == '1.19.25'
    for name, digest in m['files'].items():
        assert builder.sha(ROOT / 'russifier/payload' / name) == digest, name
    OUT.mkdir(exist_ok=True)
    (OUT / 'before').mkdir(exist_ok=True)
    shutil.copyfile(ROOT / 'russifier/manifest.json', OUT / 'before/manifest.json')
    before = OUT / 'before/panel.apk'
    shutil.copyfile(ROOT / 'russifier/payload/panel.apk', before)
    if WORK.exists():
        shutil.rmtree(WORK)
    WORK.mkdir()
    shutil.copyfile(ROOT / 'scripts/BuildAtmosphereDex.java', WORK / 'BuildDex.java')
    builder.run(builder.J / 'javac.exe', '-cp', builder.JAR, '-d', WORK, WORK / 'BuildDex.java')
    smali = WORK / SMALI_DIR
    shutil.copytree(DECODED / SMALI_DIR, smali)
    counts = patch_tree(smali)
    wanted = set(LIMITS) | set(SCREEN)
    assert wanted <= set(counts), sorted(wanted - set(counts))
    dex = WORK / DEX_ENTRY
    builder.run(builder.J / 'java.exe', '-Xmx2g', '-cp', str(builder.JAR) + ';' + str(WORK), 'BuildDex', smali, dex)
    target = OUT / 'panel.apk'
    with zipfile.ZipFile(before) as src, zipfile.ZipFile(target, 'w') as dst:
        for entry in src.infolist():
            dst.writestr(entry, dex.read_bytes() if entry.filename == DEX_ENTRY else src.read(entry.filename))
    with zipfile.ZipFile(before) as src, zipfile.ZipFile(target) as dst:
        assert src.namelist() == dst.namelist()
        assert [n for n in src.namelist() if src.read(n) != dst.read(n)] == [DEX_ENTRY]
    previous = m['files']['panel.apk']
    if previous not in m['previousPanelHashes']:
        m['previousPanelHashes'].append(previous)
    shutil.copyfile(target, ROOT / 'russifier/payload/panel.apk')
    m['files']['panel.apk'] = builder.sha(target)
    m['version'] = '1.19.26'
    (ROOT / 'russifier/manifest.json').write_text(json.dumps(m, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    (OUT / 'build-report.json').write_text(json.dumps({'version': '1.19.26', 'replacements': counts,
        'limits': LIMITS, 'screen': SCREEN, 'nativeChangedEntries': [DEX_ENTRY]}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('Built 1.19.26: replacements', counts)

if __name__ == '__main__':
    main()
