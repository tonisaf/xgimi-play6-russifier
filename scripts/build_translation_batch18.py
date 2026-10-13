"""Eighteenth batch: projector manager (manager) and accessory update (ota.accessories) — hard-coded Chinese literals.

Both apps become native patches like upgrade/shutdown in 1.19.33. Only literals shown to the user are patched.
Left alone: logs (KLog / BDLog / Log), analytics values (ITvManager.projectorManager*, LogReportUtils, WeChat robot
reports), enum descriptions (DeviceUpdateMode, NoticeType), Baidu SDK / plugin framework strings, DNS-repair result
words (reported), and everything that is a page/tag key.
The source is the stock APK pulled from the device (SHA256 checked against manifest.originals)."""
from pathlib import Path
import json, shutil
import build_photo_fixes as builder
import build_translation_batch10 as b10
import build_translation_batch12 as b12
import build_translation_batch16 as b16

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'investigation/translation-batch18-2026-10-13'
WORK = Path('C:/android/translation-batch18-20261013')
PULLED = b16.PULLED
cls = b10.cls

COMMON = [
    (cls('SearchKeyboard', 'SearchKeyboard2'), {
        '退格': 'Удалить', '清空': 'Очистить', '清除': 'Очистить', '长按语音键搜索': 'Удерживайте кнопку голоса для поиска',
        '全键盘': 'Полная клавиатура', '九宫格': 'Цифровая клавиатура'}),
    (cls('NoNetworkCell'), {'网络不通，请检查网络连接情况': 'Нет связи. Проверьте подключение к сети'}),
    (cls('DefaultErrorPageCell2'), {'未连接网络': 'Нет подключения к сети'}),
    (cls('ErrorUtils'), {'错误码：-1000': 'Код ошибки: -1000'}),
    (cls('DialogCellFactory'), {'验证码:': 'Код:', '按退出': 'Нажмите, чтобы выйти'}),
    (cls('PlayButtonBuilder', 'ExtensibleButtonBuilder'), {'播放': 'Воспроизвести'}),
]

APPS = {
    'manager': {
        'target': 'com.xgimi.manager', 'file': 'manager-native.apk', 'backing': '/data/local/tmp/beam-russifier-manager.apk',
        'targets': [
            (cls('TimeFormatter'), {'1-2分钟': '1–2 мин', '2-3分钟': '2–3 мин', '3分钟以上': 'Более 3 мин'}),
            (cls('SdkTrashService'), {'其他': 'Другое'}),
        ],
    },
    'ota.accessories': {
        'target': 'com.xgimi.ota.accessories', 'file': 'ota-accessories-native.apk', 'backing': '/data/local/tmp/beam-russifier-otaaccessories.apk',
        'targets': [
            (cls('SpeakerVersionInfoManager'), {'1、唐纳德音响功能更新\n2、修复部分已知问题，并优化用户体验': '1. Обновление функций колонки Donald\n2. Исправлены известные проблемы, улучшен пользовательский опыт'}),
            (cls('RcUpgradePresenter'), {'初始化连接对端设备异常,\n%s': 'Ошибка подключения к устройству,\n%s', '升级失败，\n%s': 'Не удалось обновить,\n%s'}),
            (cls('SwitchPanelTeLinkUpgradePresenter'), {'升级时连接中断': 'Соединение прервано во время обновления'}),
            (cls('RemoteUpdateActivity'), {
                '幕布已知问题修复': 'Исправлены известные проблемы экрана', '音响已知问题修复': 'Исправлены известные проблемы колонки',
                '极米智能光子幕布': 'Умный фотонный экран XGIMI', '更新一些已知问题': 'Исправлены некоторые известные проблемы'}),
            (cls('CheckVersionView'), {'当前版本': 'Текущая версия', '检查更新': 'Проверить', '当前已是最新版本': 'Установлена последняя версия'}),
            (cls('CheckSpeakerService'), {
                '当前 XGIMI Sound 版本不一致，需要更新以继续配置': 'Версия XGIMI Sound не совпадает, обновите её, чтобы продолжить настройку',
                '暂不更新将导致 XGIMI Sound 无法继续配置': 'Без обновления продолжить настройку XGIMI Sound невозможно',
                '立即更新': 'Обновить сейчас'}),
        ],
    },
}

def main():
    m = json.loads((ROOT / 'russifier/manifest.json').read_text(encoding='utf-8'))
    assert m['version'] == '1.19.34'
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
    for app, cfg in APPS.items():
        stock = PULLED / (app + '.apk')
        assert builder.sha(stock) == m['originals'][cfg['target']]['sha256'], app
        decoded = Path('C:/android/d13-o-' + app)
        targets = COMMON + cfg['targets']
        all_counts, rebuilt = {}, {}
        for directory in sorted(d.name for d in decoded.iterdir() if d.name.startswith('smali')):
            smali = WORK / (app + '-' + directory)
            shutil.copytree(decoded / directory, smali)
            counts = b12.patch_dir(smali, targets)
            if counts:
                for k, v in counts.items():
                    all_counts[k] = all_counts.get(k, 0) + v
                rebuilt[b10.dex_name(directory)] = b12.build_dex(smali, b10.dex_name(directory))
            shutil.rmtree(smali)
        wanted = {old for _, mapping in cfg['targets'] for old in mapping}
        missing = sorted(wanted - set(all_counts))
        assert not missing, (app, missing)
        target = OUT / cfg['file']
        b12.rebuild_apk(stock, target, rebuilt)
        shutil.copyfile(target, ROOT / 'russifier/payload' / cfg['file'])
        m['files'][cfg['file']] = builder.sha(target)
        if not any(p['file'] == cfg['file'] for p in m['runtimePatches']):
            m['runtimePatches'].append({'target': cfg['target'], 'file': cfg['file'], 'backing': cfg['backing']})
        report[app] = {'changedEntries': sorted(rebuilt), 'replacements': all_counts}
        print(app, sorted(rebuilt), len(all_counts), 'literals')
    m['version'] = '1.19.35'
    (ROOT / 'russifier/manifest.json').write_text(json.dumps(m, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    (OUT / 'build-report.json').write_text(json.dumps({'version': '1.19.35', **report}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('Built 1.19.35')

if __name__ == '__main__':
    main()
