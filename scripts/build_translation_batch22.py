"""Twenty-second batch (1.19.41): the application installation dialog.

When an APK is installed from a launcher (BEAM's own update, a file manager), the stock `com.android.packageinstaller`
is not what the user sees: XGIMI's `XgimiFrameworkUi` draws the dialog ("正在准备安装应用", "安装 "Beam" ？", the red
"not certified by XGIMI" warning, "完成/打开", and the failure reasons). All 31 strings are Chinese-only in that APK
and absent from the skin, so they get a resource overlay of their own (same build as batch 21).
Quotes around application names are written as «%s»: ASCII quotes in a resource value need escaping that gains nothing."""
import json, os, shutil, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_translation_batch21 as b21

ROOT, OUT, PAYLOAD, STOCK = b21.ROOT, b21.ROOT / 'investigation/translation-batch22-2026-10-13', b21.PAYLOAD, b21.STOCK
NEW_VERSION = '1.19.41'
TARGET, PACKAGE, FILE, STOCK_APK = 'com.xgimi.xgimiframeworkui', 'com.beam.translation.xgimiframeworkui', 'frameworkui.apk', 'XgimiFrameworkUi.apk'
DEVICE_PATH = '/vendor/app/XgimiFrameworkUi/XgimiFrameworkUi.apk'

INCOMPATIBLE = 'Приложение несовместимо с системой, установка невозможна'
INVALID = 'Недопустимый установочный пакет, установка невозможна'
FAILED = 'Ошибка установки приложения'
CERT_WARNING = 'Источник установки не сертифицирован XGIMI, возможны проблемы совместимости. Лучше установить сертифицированное приложение из магазина'

STRINGS = {
    'but_cacel': 'Отмена',
    'but_finish': 'Готово',
    'but_install': 'Установить',
    'but_install_from_market': 'Установить сертифицированную версию',
    'but_ok': 'ОК',
    'but_open': 'Открыть',
    'but_well': 'Хорошо',
    'msg_install_apk': 'Установить «%s»?',
    'msg_install_confirm_tips_exist_on_market': CERT_WARNING,
    'msg_install_confirm_tips_unknown_pacakge': CERT_WARNING,
    'msg_install_failed': FAILED,
    'msg_install_failed_reason_block': 'Система запретила установку этого приложения',
    'msg_install_failed_reason_conflic': 'Конфликт',
    'msg_install_failed_reason_incompatible': INCOMPATIBLE,
    'msg_install_failed_reason_invalid': INVALID,
    'msg_install_failed_reason_storage': 'Недостаточно свободного места: освободите память и повторите',
    'msg_install_failed_reason_unkonow': FAILED,
    'msg_install_failed_sub_UPDATE_INCOMPATIBLE': 'Ошибка установки: удалите установленное приложение «%s» и повторите',
    'msg_install_failed_sub_reason_IMCOMPATIBLE': INCOMPATIBLE,
    'msg_install_failed_sub_reason_check_cert_failed': 'Не удалось проверить подпись приложения, установка невозможна',
    'msg_install_failed_sub_reason_downgrade': 'На устройстве уже есть более новая версия «%s»: удалите её и повторите',
    'msg_install_failed_sub_reason_incompatable_with_other_app': FAILED,
    'msg_install_failed_sub_reason_invalid_apk': INVALID,
    'msg_install_failed_sub_reason_invalid_cert': 'Подпись приложения недействительна, установка невозможна',
    'msg_install_failed_sub_reason_share_uid_imcompatible': 'UID приложения несовместим или подпись не соответствует UID',
    'msg_install_failed_sub_reason_test': 'Этот пакет предназначен только для тестирования, установка невозможна',
    'msg_install_failed_sub_user_restried': FAILED,
    'msg_install_prepare': 'Подготовка к установке приложения',
    'msg_install_version': 'Версия %s',
    'msg_installing_apk': 'Установка «%s»',
    'msg_installing_finish': 'Установка «%s» завершена',
}

def main():
    m = json.loads((ROOT / 'russifier/manifest.json').read_text(encoding='utf-8'))
    assert m['version'] in ('1.19.40', NEW_VERSION), m['version']
    OUT.mkdir(exist_ok=True)
    (OUT / 'before').mkdir(exist_ok=True)
    shutil.copyfile(ROOT / 'russifier/manifest.json', OUT / 'before/manifest.json')
    stock = b21.stock_strings(STOCK / STOCK_APK)
    for key, value in STRINGS.items():
        assert key in stock, key
        original = stock[key].get('') or next(iter(stock[key].values()))
        assert b21.args(original) == b21.args(value), (key, original, value)
    chinese = {k for k, v in stock.items() if any('一' <= ch <= '鿿' for ch in (v.get('') or ''))} - set(STRINGS)
    assert not chinese, sorted(chinese)          # nothing Chinese is left without a translation
    work = Path(os.environ['TEMP']) / 'beam-batch22'
    shutil.rmtree(work, ignore_errors=True)
    work.mkdir(parents=True)
    built = b21.build(FILE, PACKAGE, TARGET, STRINGS, work)
    shutil.copyfile(built, PAYLOAD / FILE)
    shutil.copyfile(built, OUT / FILE)
    m['files'][FILE] = b21.sha(built)
    m['originals'][TARGET] = {'path': DEVICE_PATH, 'sha256': b21.sha(STOCK / STOCK_APK)}
    if not any(o['package'] == PACKAGE for o in m['overlays']):
        m['overlays'].append({'package': PACKAGE, 'target': TARGET, 'file': FILE})
    m.setdefault('resourceChecks', {}).setdefault(TARGET, {}).update(STRINGS)
    m['version'] = NEW_VERSION
    (ROOT / 'russifier/manifest.json').write_text(json.dumps(m, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    (OUT / 'build-report.json').write_text(json.dumps({'version': NEW_VERSION, 'strings': len(STRINGS), 'sha256': m['files'][FILE]}, indent=2) + '\n', encoding='utf-8')
    print(FILE, len(STRINGS), 'strings; built', NEW_VERSION)

if __name__ == '__main__':
    main()
