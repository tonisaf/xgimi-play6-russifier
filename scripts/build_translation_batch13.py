"""Thirteenth batch: hard-coded Chinese literals shown by SystemUI (systemui-native.apk).

Only literals that reach the user are patched (cell texts, dialog buttons, toasts). Left alone on purpose:
log messages, analytics values, test/mock strings (RichTextUtil, TVUIDialogBuilder, MultiFuncSingleTextCell),
SDK feature names (FeatureSdkUtils, GmSystemManager, ShowTitleType), battery labels that only go to the log,
and the 240 lunar-calendar names of LunarCalendar.
The decoded tree predates batch 12, so the FocusUIV2 adaptation words are re-applied first."""
from pathlib import Path
import json, shutil, zipfile
import build_photo_fixes as builder
import build_translation_batch10 as b10
import build_translation_batch12 as b12

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'investigation/translation-batch13-2026-10-13'
WORK = Path('C:/android/translation-batch13-20261013')
DECODED = b12.SYSTEMUI_DECODED
cls = b10.cls

TARGETS = [
    (cls('EnvDonePageCell'), {
        '已匹配校正设置': 'Настройки коррекции подобраны',
        '若投影环境变化，可至“设置 > 画面校正设置”更改': 'Если условия проекции изменятся, измените их в «Настройки > Настройки коррекции»',
        '完成': 'Готово',
        '去更改': 'Изменить',
        '已开启': 'Включено',
        '未开启': 'Выключено',
        '画面智能避障': 'Умный обход препятствий',
        '画幕自动对齐': 'Автовыравнивание по экрану',
        '墙面颜色适配': 'Адаптация к цвету стены',
    }),
    (cls('FocusDialogFactory'), {'稍后可在“画面校正 > 画面校正设置”设置': 'Позже это можно настроить в «Коррекция изображения > Настройки коррекции»'}),
    (cls('DelayOffLightingDialog'), {
        '完成': 'Готово',
        ' 分钟': ' мин',
        '自定义延时关灯键': 'Кнопка отложенного выключения света',
        '可配置遥控器的【延时关灯键】，定义每次按下后自动关灯\n的延迟时间': 'Можно настроить [кнопку отложенного выключения света] на пульте: задержку до автоматического выключения света после каждого нажатия',
        '1分钟': '1 мин', '5分钟': '5 мин', '15分钟': '15 мин', '30分钟': '30 мин',
        '自定义时长': 'Своё время',
    }),
    (cls('InputDelayOffLightingDialog'), {'分钟': 'мин', '支持1-120分钟内自定义': 'Можно задать от 1 до 120 минут'}),
    (cls('DuaBtAnimView'), {
        '音频共享回连通知': 'Уведомление о повторном подключении общего аудио',
        '发现蓝牙': 'Обнаружен Bluetooth',
        '按': 'Нажмите',
        '音频共享': 'для общего доступа к аудио',
    }),
    (cls('PushPullScreen'), {
        '画面调整时不支持手推屏': 'Ручное перемещение экрана недоступно во время настройки изображения',
        '巨幕模式下不支持手推屏': 'Ручное перемещение экрана недоступно в режиме гигантского экрана',
        '极速游戏模式不支持手推屏': 'Ручное перемещение экрана недоступно в режиме максимальной скорости',
    }),
    (cls('DialogCellFactory'), {'验证码:': 'Код:', '按退出': 'Нажмите, чтобы выйти'}),
    (cls('NoNetworkCell'), {'网络不通，请检查网络连接情况': 'Нет связи. Проверьте подключение к сети'}),
    (cls('DefaultErrorPageCell2'), {'未连接网络': 'Нет подключения к сети'}),
    (cls('ErrorUtils'), {'错误码：-1000': 'Код ошибки: -1000'}),
    (cls('SearchKeyboard', 'SearchKeyboard2'), {
        '退格': 'Удалить', '清空': 'Очистить', '清除': 'Очистить', '长按语音键搜索': 'Удерживайте кнопку голоса для поиска',
        '全键盘': 'Полная клавиатура', '九宫格': 'Цифровая клавиатура',
    }),
    (cls('PlayButtonBuilder', 'ExtensibleButtonBuilder'), {'播放': 'Воспроизвести'}),
]

def main():
    m = json.loads((ROOT / 'russifier/manifest.json').read_text(encoding='utf-8'))
    assert m['version'] == '1.19.29'
    for name, digest in m['files'].items():
        assert builder.sha(ROOT / 'russifier/payload' / name) == digest, name
    OUT.mkdir(exist_ok=True)
    (OUT / 'before').mkdir(exist_ok=True)
    shutil.copyfile(ROOT / 'russifier/manifest.json', OUT / 'before/manifest.json')
    before = OUT / 'before/systemui-native.apk'
    shutil.copyfile(ROOT / 'russifier/payload/systemui-native.apk', before)
    if WORK.exists():
        shutil.rmtree(WORK)
    WORK.mkdir()
    shutil.copyfile(ROOT / 'scripts/BuildAtmosphereDex.java', WORK / 'BuildDex.java')
    builder.run(builder.J / 'javac.exe', '-cp', builder.JAR, '-d', WORK, WORK / 'BuildDex.java')
    all_counts, rebuilt = {}, {}
    for directory in sorted(d.name for d in DECODED.iterdir() if d.name.startswith('smali')):
        smali = WORK / directory
        shutil.copytree(DECODED / directory, smali)
        if directory == 'smali_classes2':
            b12.patch_dir(smali, b12.SYSTEMUI_TARGETS)          # batch 12 lives only in the payload
        counts = b12.patch_dir(smali, TARGETS)
        if not counts:
            shutil.rmtree(smali)
            continue
        for k, v in counts.items():
            all_counts[k] = all_counts.get(k, 0) + v
        rebuilt[b10.dex_name(directory)] = b12.build_dex(smali, b10.dex_name(directory))
        shutil.rmtree(smali)
    wanted = {old for _, mapping in TARGETS for old in mapping}
    assert wanted <= set(all_counts), sorted(wanted - set(all_counts))
    target = OUT / 'systemui-native.apk'
    b12.rebuild_apk(before, target, rebuilt)
    native = next(p for p in m['runtimePatches'] if p['file'] == 'systemui-native.apk')
    hashes = native.setdefault('previousHashes', [])
    if m['files']['systemui-native.apk'] not in hashes:
        hashes.append(m['files']['systemui-native.apk'])
    shutil.copyfile(target, ROOT / 'russifier/payload/systemui-native.apk')
    m['files']['systemui-native.apk'] = builder.sha(target)
    m['version'] = '1.19.30'
    (ROOT / 'russifier/manifest.json').write_text(json.dumps(m, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    (OUT / 'build-report.json').write_text(json.dumps({'version': '1.19.30', 'replacements': all_counts, 'changedEntries': sorted(rebuilt),
        'mapping': [{'classes': p.pattern, 'literals': mp} for p, mp in TARGETS]}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('Built 1.19.30: entries', sorted(rebuilt), 'literals', len(all_counts))

if __name__ == '__main__':
    main()
