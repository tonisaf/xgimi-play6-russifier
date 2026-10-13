"""Tenth batch: hard-coded Chinese literals of the calibration and network screens (panel.apk).

Only literals shown to the user are patched (toasts, dialog titles/subtitles, error pages, network names).
Log messages are left alone. A literal that is compared with text coming from the skin/resources
(equals checks) gets exactly the Russian value the skin already uses, so the comparison starts to work."""
from pathlib import Path
import json, re, shutil, zipfile
import build_photo_fixes as builder
import build_translation_batch9 as b9

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'investigation/translation-batch10-2026-10-13'
WORK = Path('C:/android/translation-batch10-20261013')
DECODED = Path('C:/android/photo-panel-20261012')          # apktool decode of the payload panel.apk (classes, classes2..6)

def cls(*names):
    return re.compile(r'^(' + '|'.join(re.escape(n) for n in names) + r')(\$.*)?$')

TARGETS = [
    (cls('CalibrationKlxqDialog'), {
        '已恢复默认': 'Сброшено к значениям по умолчанию',
        '输入距离': 'Введите расстояние',                     # compared with calibration_enter_distance (skin)
        '投影距离请控制在1.8-2.2m': 'Расстояние проекции должно быть 1,8–2,2 м',
        '请将投影与墙面的距离控制在1.8-2.2M范围内': 'Расстояние от проектора до стены должно быть от 1,8 до 2,2 м',
    }),
    (cls('DistanceInputDialog'), {
        '请输入距离': 'Введите расстояние',
        '请输入投影与画面的距离': 'Введите расстояние от проектора до экрана',
    }),
    (cls('PageCellOne'), {'如自动梯形校正后，画面不\n方正，请进行校准': 'Если после автотрапеции изображение\nне прямоугольное, выполните калибровку'}),
    (cls('PageCellTwo'), {'请将投影放在水平桌面，并\n将投影与墙面的距离控制在\n1.8-2.2M范围内': 'Поставьте проектор на горизонтальный стол\nи держите расстояние до стены\n1,8–2,2 м'}),
    (cls('PageCellThree'), {
        '微调投影角度至 [正投]\n保证当前投影画面为 [矩形]': 'Подстройте угол проекции до [прямой проекции]\nчтобы изображение стало [прямоугольным]',
        '左右高度越接近校准效果越好': 'Чем ближе левая и правая высоты, тем лучше результат калибровки',
    }),
    (cls('PageCellFour'), {'请测量投影前脸与墙面的垂\n直距离': 'Измерьте расстояние от передней панели\nпроектора до стены по перпендикуляру'}),
    (cls('PageCellSix'), {
        '校准已完成\n当前画面是否方正？': 'Калибровка завершена\nИзображение прямоугольное?',
        '若画面不方正，请选择 [重新校正]\n若画面方正，请选择 [结束校准]': 'Если изображение неровное, выберите [Откалибровать заново]\nЕсли ровное — [Завершить калибровку]',
    }),
    (cls('WifiViewModel'), {
        '音响正在重新连接…': 'Колонка переподключается…',
        '网络扫描中，音响暂不可用': 'Идёт поиск сетей — колонка пока недоступна',
    }),
    (cls('NetWorkUtils', 'WifiAdapter'), {'有线网络': 'Проводная сеть'}),                  # network_set_write_text / wired_network
    (cls('WifiAdapter'), {'无线热点': 'Беспроводная точка доступа'}),                      # network_set_ap_text
    (cls('NetWorkApRepository'), {'密码': 'Пароль'}),                                       # network_ap_ssid_pwd
    (cls('WifiDialog'), {'Wi-Fi 已关闭': 'Wi-Fi выключен'}),
    (cls('NoNetworkCell'), {'网络不通，请检查网络连接情况': 'Нет связи. Проверьте подключение к сети'}),
    (cls('DefaultErrorPageCell2'), {'未连接网络': 'Нет подключения к сети'}),
    (cls('FilterManagerActivity', 'SharingCodeActivity', 'StyleFilterActivity', 'StyleFilterHelper'), {'无网络连接': 'Нет подключения к сети'}),
]

def esc(text):
    return json.dumps(text, ensure_ascii=True)

def dex_name(directory):
    return 'classes.dex' if directory == 'smali' else directory.replace('smali_', '') + '.dex'

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
    assert m['version'] == '1.19.26'
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
    all_counts = {}
    rebuilt = {}
    for directory in sorted(d.name for d in DECODED.iterdir() if d.name.startswith('smali')):
        smali = WORK / directory
        shutil.copytree(DECODED / directory, smali)
        if directory == b9.SMALI_DIR:
            b9.patch_tree(smali)          # the decoded tree predates the 1.19.26 zoom/shift patch; keep it
        counts = patch_tree(smali)
        if not counts:
            shutil.rmtree(smali)
            continue
        for k, v in counts.items():
            all_counts[k] = all_counts.get(k, 0) + v
        dex = WORK / dex_name(directory)
        builder.run(builder.J / 'java.exe', '-Xmx2g', '-cp', str(builder.JAR) + ';' + str(WORK), 'BuildDex', smali, dex)
        rebuilt[dex_name(directory)] = dex.read_bytes()
        shutil.rmtree(smali)
    wanted = {old for _, mapping in TARGETS for old in mapping}
    assert wanted <= set(all_counts), sorted(wanted - set(all_counts))
    target = OUT / 'panel.apk'
    with zipfile.ZipFile(before) as src, zipfile.ZipFile(target, 'w') as dst:
        for entry in src.infolist():
            dst.writestr(entry, rebuilt.get(entry.filename, None) or src.read(entry.filename))
    with zipfile.ZipFile(before) as src, zipfile.ZipFile(target) as dst:
        assert src.namelist() == dst.namelist()
        assert sorted(n for n in src.namelist() if src.read(n) != dst.read(n)) == sorted(rebuilt)
    previous = m['files']['panel.apk']
    if previous not in m['previousPanelHashes']:
        m['previousPanelHashes'].append(previous)
    shutil.copyfile(target, ROOT / 'russifier/payload/panel.apk')
    m['files']['panel.apk'] = builder.sha(target)
    m['version'] = '1.19.27'
    (ROOT / 'russifier/manifest.json').write_text(json.dumps(m, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    report = {'version': '1.19.27', 'replacements': all_counts, 'nativeChangedEntries': sorted(rebuilt),
              'mapping': [{'classes': p.pattern, 'literals': mp} for p, mp in TARGETS]}
    (OUT / 'build-report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('Built 1.19.27: changed entries', sorted(rebuilt), 'literals', len(all_counts))

if __name__ == '__main__':
    main()
