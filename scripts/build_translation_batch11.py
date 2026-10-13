"""Eleventh batch: hard-coded Chinese literals of Bluetooth, update (OTA), power-saving, picture-mode warnings and search.

Same rules as batch 10: only literals that are shown to the user are patched (Toast, setText, dialog title/desc),
logs and strings used as keys or compared with device names are left alone.
The decoded smali tree predates the earlier native patches, so batches 9 and 10 are re-applied before this one."""
from pathlib import Path
import json, re, shutil, zipfile
import build_photo_fixes as builder
import build_translation_batch9 as b9
import build_translation_batch10 as b10

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'investigation/translation-batch11-2026-10-13'
WORK = Path('C:/android/translation-batch11-20261013')
DECODED = b10.DECODED
cls = b10.cls

TARGETS = [
    (cls('BatteryDialogCell'), {'电池电量': 'Заряд батареи', '节能模式': 'Режим энергосбережения'}),
    (cls('BluetoothViewModel'), {
        '请退出 Miracast 后重试': 'Выйдите из Miracast и повторите попытку',
        '清除后，无法使用遥控器控制此投影设备，\n可长按 nnn和 nnn重新配对': 'После очистки пульт не сможет управлять проектором,\nудерживайте nnn и nnn для повторного сопряжения',
    }),
    (cls('BluetoothFactory'), {
        '清除后，无法使用遥控器控制此投影设备，可长按 nnn和 nnn重新配对': 'После очистки пульт не сможет управлять проектором, удерживайте nnn и nnn для повторного сопряжения',
        '已配置': 'Настроено',
    }),
    (cls('ShareAudioDialog'), {'待共享的设备参数异常，不能进行共享': 'Параметры устройства некорректны, общий доступ невозможен'}),
    (cls('AbUpdateDialog'), {'正在后台更新': 'Идёт обновление в фоновом режиме', '正在更新...': 'Обновление…'}),
    (cls('TimerSelectorDialog'), {'请选择开始时间': 'Выберите время начала', '保存': 'Сохранить', '按': 'Нажмите'}),
    (cls('AbTipsView'), {'按': 'Нажмите', '查看详情': 'Подробнее'}),
    (cls('BackTipCell'), {'按': 'Нажмите', '退出': 'Выйти'}),
    (cls('SwitchCell'), {'节能模式': 'Режим энергосбережения'}),
    (cls('CoreRepository'), {'加载配置文件失败': 'Не удалось загрузить файл настроек'}),
    (cls('DialogCellFactory'), {'按退出': 'Нажмите, чтобы выйти'}),
    (cls('LawRepository'), {'数据加载中，请退出重试': 'Данные загружаются, выйдите и повторите попытку'}),
    (cls('MoreViewModel'), {'设置开始时间': 'Время начала', '设置结束时间': 'Время окончания'}),
    (cls('ExportSettingsDialog'), {'导出时出现异常，请重试': 'Ошибка экспорта, повторите попытку', '导出成功': 'Экспорт выполнен'}),
    (cls('BrightnessDialog'), {'亮度 10+': 'Яркость 10+'}),
    (cls('PictureFactory'), {
        '切换至极速模式降低延迟？': 'Переключиться в режим максимальной скорости, чтобы снизить задержку?',
        '1. 切换后，画面将恢复默认形状，可手动移动投影设备\n2. 极速模式下不支持调整画面大小、形状、位置等':
            '1. После переключения изображение вернётся к форме по умолчанию, устройство можно переместить вручную\n2. В режиме максимальной скорости нельзя менять размер, форму и положение изображения',
        '切换': 'Переключить',
    }),
    (cls('PictureRepository'), {
        '切换至“Boost 档位”以支持性\n能模式?': 'Переключиться на уровень «Boost», чтобы включить\nрежим производительности?',
        '切换过程将保持屏幕关闭一段时间，完成后自动亮屏\n切换前请确保设备通风口无遮挡、且室温不超过25°C。请勿长时间使用此模式，否则可能造成设备过热影响使用寿命':
            'Во время переключения экран на некоторое время погаснет и включится сам\nПеред переключением убедитесь, что вентиляционные отверстия не закрыты, а температура в помещении не выше 25 °C. Не используйте этот режим долго: устройство может перегреться, а срок службы сократиться',
    }),
    (cls('PictureViewModel'), {'所有图像设置均会重置为出厂状态，是否继续？': 'Все настройки изображения будут сброшены к заводским. Продолжить?'}),
    (cls('SerialPortControlFactory'), {'非信号源': 'Нет источника'}),
    (cls('ErrorUtils'), {
        '未知异常': 'Неизвестная ошибка', '当前不可回滚': 'Откат сейчас невозможен', '回滚异常': 'Ошибка отката',
        '当前使用镜像不匹配': 'Используемый образ не подходит', '升级文件不存在': 'Файл обновления не найден',
        '设备电量不足': 'Недостаточный заряд устройства', '设备异常，无法更新': 'Сбой устройства, обновление невозможно',
        '存储空间不足': 'Недостаточно места в памяти', '已安装更新，请重启设备': 'Обновление установлено, перезагрузите устройство',
        '用户取消升级': 'Обновление отменено пользователем', '文件系统校验失败': 'Не пройдена проверка файловой системы',
        '写入分区失败': 'Не удалось записать раздел', 'OTA文件异常': 'Файл OTA повреждён', '升级过程异常': 'Ошибка в процессе обновления',
        '文件系统复制错误': 'Ошибка копирования файловой системы', '错误码：-1000': 'Код ошибки: -1000',
    }),
    (cls('AbUpgradeService'), {'错误原因：': 'Причина ошибки: ', ' 错误码：': ' Код ошибки: ', '更新失败': 'Не удалось обновить'}),
    (cls('SearchKeyboard', 'SearchKeyboard2'), {'退格': 'Удалить', '清空': 'Очистить', '清除': 'Очистить', '长按语音键搜索': 'Удерживайте кнопку голоса для поиска'}),
]

def patch_tree(smali):
    counts = {}
    for p in sorted(smali.rglob('*.smali')):
        for pattern, mapping in TARGETS:
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

def main():
    m = json.loads((ROOT / 'russifier/manifest.json').read_text(encoding='utf-8'))
    assert m['version'] == '1.19.27'
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
            b9.patch_tree(smali)
        b10.patch_tree(smali)             # earlier batches live only in the payload, not in the decoded tree
        counts = patch_tree(smali)
        if not counts:
            shutil.rmtree(smali)
            continue
        for k, v in counts.items():
            all_counts[k] = all_counts.get(k, 0) + v
        dex = WORK / b10.dex_name(directory)
        builder.run(builder.J / 'java.exe', '-Xmx2g', '-cp', str(builder.JAR) + ';' + str(WORK), 'BuildDex', smali, dex)
        rebuilt[b10.dex_name(directory)] = dex.read_bytes()
        shutil.rmtree(smali)
    wanted = {old for _, mapping in TARGETS for old in mapping}
    missing = sorted(wanted - set(all_counts))
    assert not missing, missing
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
    m['version'] = '1.19.28'
    (ROOT / 'russifier/manifest.json').write_text(json.dumps(m, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    report = {'version': '1.19.28', 'replacements': all_counts, 'nativeChangedEntries': sorted(rebuilt),
              'mapping': [{'classes': p.pattern, 'literals': mp} for p, mp in TARGETS]}
    (OUT / 'build-report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('Built 1.19.28: changed entries', sorted(rebuilt), 'literals', len(all_counts))

if __name__ == '__main__':
    main()
