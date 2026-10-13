"""Fifteenth batch: user-visible Chinese literals of the three other native APKs
(atmosphere-native, wirelessscreen-native, gmservice-native).

gmservice and atmosphere already carry runtime translation tables (BeamRu / BeamCatalog / BeamText); only strings outside
those tables are patched here. Shared SDK widgets (search keyboard, no-network page, error code, play button) are patched
wherever they exist. Left alone: logs, analytics, debug dumps (MirrorStatusData), carrier / zodiac / lunar helpers,
tags and keys (`播放器选择`, `网络：`/`设备：` are matched with contains()), the Wi-Fi congestion words, and voice-command
names (VoiceSwitchService compares them).
Decoded trees (apktool -r of the current payload APKs) already contain every earlier patch."""
from pathlib import Path
import json, shutil
import build_photo_fixes as builder
import build_translation_batch10 as b10
import build_translation_batch12 as b12

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'investigation/translation-batch15-2026-10-13'
WORK = Path('C:/android/translation-batch15-20261013')
cls = b10.cls

COMMON = [
    (cls('SearchKeyboard', 'SearchKeyboard2'), {
        '退格': 'Удалить', '清空': 'Очистить', '清除': 'Очистить', '长按语音键搜索': 'Удерживайте кнопку голоса для поиска',
        '全键盘': 'Полная клавиатура', '九宫格': 'Цифровая клавиатура'}),
    (cls('NoNetworkCell'), {'网络不通，请检查网络连接情况': 'Нет связи. Проверьте подключение к сети'}),
    (cls('DefaultErrorPageCell2'), {'未连接网络': 'Нет подключения к сети'}),
    (cls('ErrorUtils'), {'错误码：-1000': 'Код ошибки: -1000'}),
    (cls('DialogCellFactory'), {'验证码:': 'Код:'}),
    (cls('PlayButtonBuilder', 'ExtensibleButtonBuilder'), {'播放': 'Воспроизвести'}),
]

SPECIFIC = {
    'atmosphere-native': [
        (cls('FlipClockComponent'), {'yyyy年M月d日 · EEEE': 'd MMMM yyyy · EEEE'}),
        (cls('k0'), {'M月d日, HH:mm': 'd MMM, HH:mm'}),
        (cls('WeatherScreenSaver'), {
            '定位获取失败，长按': 'Не удалось определить местоположение, удерживайте',
            '键手动选择城市': 'для выбора города вручную',
            '地理位置': 'Местоположение'}),
        (cls('PlaneGameActivity'), {'发生异常,请尝试清理缓存重试': 'Произошла ошибка. Очистите кэш и повторите попытку'}),
    ],
    'wirelessscreen-native': [
        (cls('PushPlayerActivity'), {'直播不支持倍速': 'Прямой эфир не поддерживает смену скорости', '投屏失败': 'Ошибка трансляции', '查看解决办法': 'Как исправить'}),
        (cls('PushPlayerActivityExtKt'), {
            '自动': 'Авто', '系统播放器': 'Системный плеер', '三方播放器': 'Сторонний плеер',
            '0.5倍': '0.5x', '0.75倍': '0.75x', '1.0倍': '1.0x', '1.25倍': '1.25x', '1.5倍': '1.5x', '2.0倍': '2.0x'}),
        (cls('MenuOptionDataSource'), {'自动': 'Авто'}),           # default of the saved player type; compared with the menu above
        (cls('XgActivity'), {'设置成功': 'Настройка применена', '已选择': 'Выбрано: ', '，下次投屏生效': '. Вступит в силу при следующей трансляции', '设置失败': 'Не удалось применить настройку'}),
        (cls('CastRestarter'), {'重启投屏': 'Перезапустить трансляцию', '重启中': 'Перезапуск…'}),
        (cls('NetworkGuideVO'), {
            '和投影连接同一网络': 'Подключитесь к той же сети, что и проектор',
            '连接投影热点': 'Подключитесь к точке доступа проектора',
            '和投影连接同一WiFi': 'Подключитесь к той же сети Wi-Fi, что и проектор',
            '密码：': 'Пароль: ', '热点：': 'Точка доступа: ',
            '请将电脑或手机连接到\n和当前投影仪投影同一网络\nIP：': 'Подключите компьютер или телефон\nк той же сети, что и проектор\nIP: '}),
        (cls('AndroidMiracastPage'), {'使用Miracast时需先进入本页面': 'Для Miracast сначала откройте эту страницу'}),
        (cls('SafeModeActivity'), {'无错误日志': 'Нет журнала ошибок', '已清除数据, 请重新启动投屏': 'Данные очищены, перезапустите трансляцию', '异常：': 'Ошибка: '}),
    ],
    'gmservice-native': [],
}

def main():
    m = json.loads((ROOT / 'russifier/manifest.json').read_text(encoding='utf-8'))
    assert m['version'] == '1.19.31'
    for name, digest in m['files'].items():
        assert builder.sha(ROOT / 'russifier/payload' / name) == digest, name
    OUT.mkdir(exist_ok=True)
    (OUT / 'before').mkdir(exist_ok=True)
    shutil.copyfile(ROOT / 'russifier/manifest.json', OUT / 'before/manifest.json')
    if WORK.exists():
        shutil.rmtree(WORK)
    WORK.mkdir()
    shutil.copyfile(ROOT / 'scripts/BuildAtmosphereDex.java', WORK / 'BuildDex.java')
    builder.run(builder.J / 'javac.exe', '-cp', builder.JAR, '-d', WORK, WORK / 'BuildDex.java')
    report = {}
    for apk, specific in SPECIFIC.items():
        decoded = Path('C:/android/d13-' + apk)
        before = OUT / 'before' / (apk + '.apk')
        shutil.copyfile(ROOT / 'russifier/payload' / (apk + '.apk'), before)
        targets = COMMON + specific
        all_counts, rebuilt = {}, {}
        for directory in sorted(d.name for d in decoded.iterdir() if d.name.startswith('smali')):
            smali = WORK / (apk + '-' + directory)
            shutil.copytree(decoded / directory, smali)
            counts = b12.patch_dir(smali, targets)
            if counts:
                for k, v in counts.items():
                    all_counts[k] = all_counts.get(k, 0) + v
                rebuilt[b10.dex_name(directory)] = b12.build_dex(smali, b10.dex_name(directory))
            shutil.rmtree(smali)
        wanted = {old for _, mapping in specific for old in mapping}
        missing = sorted(wanted - set(all_counts))
        assert not missing, (apk, missing)
        if not rebuilt:
            print(apk, 'nothing to patch')
            continue
        target = OUT / (apk + '.apk')
        b12.rebuild_apk(before, target, rebuilt)
        patch = next(p for p in m['runtimePatches'] if p['file'] == apk + '.apk')
        hashes = patch.setdefault('previousHashes', [])
        if m['files'][apk + '.apk'] not in hashes:
            hashes.append(m['files'][apk + '.apk'])
        shutil.copyfile(target, ROOT / 'russifier/payload' / (apk + '.apk'))
        m['files'][apk + '.apk'] = builder.sha(target)
        report[apk] = {'changedEntries': sorted(rebuilt), 'replacements': all_counts}
        print(apk, sorted(rebuilt), len(all_counts), 'literals')
    m['version'] = '1.19.32'
    (ROOT / 'russifier/manifest.json').write_text(json.dumps(m, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    (OUT / 'build-report.json').write_text(json.dumps({'version': '1.19.32', **report}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('Built 1.19.32')

if __name__ == '__main__':
    main()
