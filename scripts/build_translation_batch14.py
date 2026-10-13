"""Fourteenth batch: remaining user-visible hard-coded Chinese literals of panel.apk (settings app).

Checked by context in smali: of the 305 literals left after 1.19.29, only the ones below reach the screen.
Left alone on purpose: log messages (Log/KLog), analytics values (SettingsDataReporter, AgileWallRemoteHelper),
device-name and key comparisons (BluetoothExtKt, AgreementHistoryDialog, HdmiDialog, ItemsWidget, VoiceFactory),
SDK function names, mock/demo classes (SimpleActivity, MockService, RequestSample, BeamPlace, Microphone*).
ThemeEntity already returns Russian names. The decoded tree predates batches 9-12, so they are re-applied first."""
from pathlib import Path
import json, shutil
import build_photo_fixes as builder
import build_translation_batch9 as b9
import build_translation_batch10 as b10
import build_translation_batch11 as b11
import build_translation_batch12 as b12

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'investigation/translation-batch14-2026-10-13'
WORK = Path('C:/android/translation-batch14-20261013')
DECODED = b10.DECODED
cls = b10.cls

UPLOAD = 'Также можно загрузить через '
TARGETS = [
    (cls('BrightnessDialog'), {'已关闭': 'Выключено: ', '亮度 ': 'Яркость '}),
    (cls('SerialPortControlFactory'), {'当前信号源：': 'Текущий источник сигнала: '}),
    (cls('DetailsCell'), {'作者:': 'Автор: ', '分享码:': 'Код доступа: '}),
    (cls('UsbUtils'), {'移动存储': 'Внешний накопитель'}),
    (cls('ImageModeTwoTitleCell'), {'杜比视界': 'Dolby Vision'}),
    (cls('DialogCellFactory'), {'验证码:': 'Код:'}),
    (cls('Page1Item', 'PlayButtonBuilder', 'ExtensibleButtonBuilder'), {'播放': 'Воспроизвести'}),
    (cls('SearchKeyboard2'), {'全键盘': 'Полная клавиатура', '九宫格': 'Цифровая клавиатура'}),
    (cls('FilterManagerPage'), {
        '删除': 'Удалить', '刷新': 'Обновить',
        '请选中后再删除': 'Сначала выберите элемент для удаления',
        '扫码上传滤镜文件': 'Загрузите файл фильтра по QR-коду',
        '您也可以通过': UPLOAD, '也可以通过': UPLOAD, '上传': '',       # "<prefix><upload url><suffix>"
        '我上传的滤镜': 'Мои загруженные фильтры', '我下载的滤镜': 'Мои скачанные фильтры',
        '暂无内容，您可以扫码上传滤镜文件': 'Пока пусто. Загрузите файл фильтра, отсканировав QR-код',
    }),
    (cls('DataSourceRepository', 'StyleFilterCell'), {'我的': 'Мои'}),           # also used as a cell tag: both sides change together
    (cls('DataSourceRepository'), {'登录极米账号': 'Войти в аккаунт XGIMI'}),
]

def main():
    m = json.loads((ROOT / 'russifier/manifest.json').read_text(encoding='utf-8'))
    assert m['version'] == '1.19.30'
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
    all_counts, rebuilt = {}, {}
    for directory in sorted(d.name for d in DECODED.iterdir() if d.name.startswith('smali')):
        smali = WORK / directory
        shutil.copytree(DECODED / directory, smali)
        if directory == b9.SMALI_DIR:
            b9.patch_tree(smali)
        b10.patch_tree(smali)
        b11.patch_tree(smali)
        b12.patch_dir(smali, b12.PANEL_TARGETS)
        counts = b12.patch_dir(smali, TARGETS)
        if not counts:
            shutil.rmtree(smali)
            continue
        for k, v in counts.items():
            all_counts[k] = all_counts.get(k, 0) + v
        rebuilt[b10.dex_name(directory)] = b12.build_dex(smali, b10.dex_name(directory))
        shutil.rmtree(smali)
    wanted = {old for _, mapping in TARGETS for old in mapping}
    missing = sorted(wanted - set(all_counts))
    assert not missing, missing
    target = OUT / 'panel.apk'
    b12.rebuild_apk(before, target, rebuilt)
    previous = m['files']['panel.apk']
    if previous not in m['previousPanelHashes']:
        m['previousPanelHashes'].append(previous)
    shutil.copyfile(target, ROOT / 'russifier/payload/panel.apk')
    m['files']['panel.apk'] = builder.sha(target)
    m['version'] = '1.19.31'
    (ROOT / 'russifier/manifest.json').write_text(json.dumps(m, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    (OUT / 'build-report.json').write_text(json.dumps({'version': '1.19.31', 'replacements': all_counts, 'changedEntries': sorted(rebuilt),
        'mapping': [{'classes': p.pattern, 'literals': mp} for p, mp in TARGETS]}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('Built 1.19.31: entries', sorted(rebuilt), 'literals', len(all_counts))

if __name__ == '__main__':
    main()
