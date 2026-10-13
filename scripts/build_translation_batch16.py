"""Sixteenth batch: system update (upgrade) and power menu (shutdown) — hard-coded Chinese literals.

Both apps had only resource overlays (RRO); their code literals were still Chinese. They become native patches
(bind-mounted APK with a patched classesN.dex) exactly like the five earlier ones.
Only literals shown to the user are patched. Left alone: logs (KLog), analytics values passed to
LogReportUtils / firmwareUpdatePopupResponse (button and popup names), PowerData names (keys compared with equals),
RelaxAppUtils scene names, FirmwarePushMethodEnum, test data.
The source is the stock APK pulled from the device (its SHA256 is checked against manifest.originals)."""
from pathlib import Path
import json, shutil
import build_photo_fixes as builder
import build_translation_batch10 as b10
import build_translation_batch11 as b11
import build_translation_batch12 as b12

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'investigation/translation-batch16-2026-10-13'
WORK = Path('C:/android/translation-batch16-20261013')
PULLED = Path('C:/Users/USER/AppData/Local/Temp/claude/C--Users-USER-TileLauncher/a706dd4d-6a8b-4c5d-a430-38c6bdaad0bc/scratchpad/other')
cls = b10.cls

ERRORS = next(mp for p, mp in b11.TARGETS if p.pattern.startswith('^(ErrorUtils)'))
ERRORS = {**ERRORS,
    '下载异常，请稍后重试': 'Ошибка загрузки, повторите позже',
    '存储空间不足': 'Недостаточно места в памяти',
    'md5校验失败，请稍后重试': 'Ошибка проверки MD5, повторите позже',
    '固件验证失败，请稍后重试': 'Ошибка проверки прошивки, повторите позже',
    '未知异常（': 'Неизвестная ошибка (', '）请稍后重试': '), повторите позже',
    '未知异常，请稍后重试': 'Неизвестная ошибка, повторите позже',
    '文件异常，请稍后重试': 'Ошибка файла, повторите позже',
    '网络异常（': 'Ошибка сети (', '）请检测后重试': '), проверьте и повторите',
    '网络异常，请检查网络后重试': 'Ошибка сети, проверьте подключение и повторите',
}
SPACE_TIP = 'Очистите большие файлы или приложения, чтобы освободить место'

APPS = {
    'upgrade': {
        'target': 'com.xgimi.upgrade', 'file': 'upgrade-native.apk', 'backing': '/data/local/tmp/beam-russifier-upgrade.apk',
        'targets': [
            (cls('ErrorUtils'), ERRORS),
            (cls('ErrorTipView'), {
                '校验失败': 'Проверка не пройдена', '\n错误码:': '\nКод ошибки: ', '下载失败': 'Ошибка загрузки', '更新失败': 'Ошибка обновления',
                '空间不足，更新失败': 'Недостаточно места, обновление не удалось',
                '进行“大文件清理”或“应用管理”\n将有效释放空间': 'Очистите большие файлы или приложения,\nчтобы освободить место',
                '安装完成': 'Установка завершена', '重启设备完成更新': 'Перезагрузите устройство, чтобы завершить обновление',
                '空间不足，下载失败': 'Недостаточно места, загрузка не удалась'}),
            (cls('XgimiOtaView'), {
                '错误原因：': 'Причина ошибки: ',
                '错误原因:电量不足，请接入适配器后重试': 'Причина ошибки: недостаточный заряд, подключите адаптер питания и повторите',
                '错误原因:更新异常（': 'Причина ошибки: сбой обновления (', '） 请检测后重试': '), проверьте и повторите',
                '安装完成，请重启': 'Установка завершена, перезагрузите устройство',
                '仍需 ': 'Требуется ещё ', '，进行“大文件清理”或“应用管理”，将有效释放空间': '. ' + SPACE_TIP}),
            (cls('DialogManager'), {
                '新版本下载失败': 'Не удалось загрузить новую версию', '空间不足': 'Недостаточно места',
                '按查看详情': 'Нажмите, чтобы посмотреть подробности', '空间不足，仍需 ': 'Недостаточно места, нужно ещё ',
                '新版本更新失败': 'Не удалось обновиться до новой версии', '新版本更新完成': 'Обновление до новой версии завершено',
                '重启设备立即体验新版本': 'Перезагрузите устройство, чтобы начать пользоваться новой версией', '已更新至新版本': 'Обновлено до новой версии'}),
            (cls('ShowErrorManager'), {
                '电量不足，请接入适配器后重试': 'Недостаточный заряд. Подключите адаптер питания и повторите',
                '更新异常，请检查后重试': 'Сбой обновления. Проверьте и повторите'}),
            (cls('UpdateTipShowMsgImp'), {
                '安装系统新版本？': 'Установить новую версию системы?',
                '已自动下载新版本，是否立即更新，更新过程将\n重启设备': 'Новая версия загружена автоматически. Обновить сейчас? Во время обновления\nустройство перезагрузится',
                '新版本下载完成，是否立即更新，更新过程将\n重启设备': 'Новая версия загружена. Обновить сейчас? Во время обновления\nустройство перезагрузится',
                '稍后再说': 'Позже', '立即更新': 'Обновить сейчас'}),
            (cls('XgimiLogoView'), {'当前版本 ': 'Текущая версия ', '最近检查时间：': 'Последняя проверка: '}),
            (cls('UpdateMainActivity'), {'已是最新版本': 'Установлена последняя версия'}),
        ],
    },
    'shutdown': {
        'target': 'com.xgimi.shutdown', 'file': 'shutdown-native.apk', 'backing': '/data/local/tmp/beam-russifier-shutdown.apk',
        'targets': [(cls('PowerAdapter'), {' 后关机': ' до выключения'})],       # "<countdown> до выключения"
    },
}

def main():
    m = json.loads((ROOT / 'russifier/manifest.json').read_text(encoding='utf-8'))
    assert m['version'] == '1.19.32'
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
        all_counts, rebuilt = {}, {}
        for directory in sorted(d.name for d in decoded.iterdir() if d.name.startswith('smali')):
            smali = WORK / (app + '-' + directory)
            shutil.copytree(decoded / directory, smali)
            counts = b12.patch_dir(smali, cfg['targets'])
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
    m['version'] = '1.19.33'
    (ROOT / 'russifier/manifest.json').write_text(json.dumps(m, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    (OUT / 'build-report.json').write_text(json.dumps({'version': '1.19.33', **report}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('Built 1.19.33')

if __name__ == '__main__':
    main()
