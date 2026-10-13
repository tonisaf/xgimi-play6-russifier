"""Twenty-third batch (1.19.42): the whole product UI of GlobalConfig (`com.xgimi.config`).

Batch 21 translated only the HDMI hint after a user photo. A second photo showed the sibling hint for USB drives still
in English ("Next time, you can quickly access the USB drive via Quick Settings"): the app's default language is English
and it has no ru-RU at all, so every user-visible string of it shows English. This batch covers all of them:
intelligent eye protection, peripherals (microphone, smart curtain, phone), AI picture quality, super resolution,
height-measure reminders, the HDMI/USB hints. Developer/test strings of the app (app_install, click_*, clean_* ...)
are not product UI and are left alone. `@` is the key icon placeholder and stays."""
import json, os, shutil, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_translation_batch21 as b21

ROOT, PAYLOAD, STOCK = b21.ROOT, b21.PAYLOAD, b21.STOCK
OUT = ROOT / 'investigation/translation-batch23-2026-10-13'
NEW_VERSION = '1.19.42'
FILE = 'config.apk'
PACKAGE, TARGET, STOCK_APK, _old = b21.APPS[FILE]

STRINGS = {
    'aipq_tip': 'Оптимизировано для режима %s',
    'aipq_title': 'Улучшение качества изображения с помощью ИИ',
    'app_background_service_started': 'Фоновая служба запущена',
    'app_close': 'Выкл.',
    'app_enable_anti_shoot_eye_window': 'Включить всплывающее окно защиты глаз',
    'app_enable_peripheral_disconnect_tip': 'Включить уведомление об отключении периферии',
    'app_enable_peripheral_window': 'Включить всплывающее окно периферии',
    'app_enable_player_animation': 'Запускать анимацию плеера',
    'app_inintelligent_anti_shooting_eye_has_been_turned_off': 'Интеллектуальная защита глаз отключена',
    'app_music_effect_native': 'Звуковой эффект: исходный',
    'app_name': 'Конфигурация',
    'connected': 'Подключено',
    'curtain_notice_desc_connected': 'Подключено',
    'curtain_notice_desc_disconnect': 'Отключено',
    'curtain_notice_title': 'Умная штора',
    'disconnected': 'Отключено',
    'eye_project_back_exit': 'Нажмите @, чтобы выйти',
    'eye_project_confirm_cancel': 'Отмена',
    'eye_project_confirm_desc': 'После отключения этой функции яркость больше не будет автоматически снижаться, когда кто-то находится перед объективом. Берегите глаза и не смотрите прямо на источник света.',
    'eye_project_confirm_title': 'Отключить интеллектуальную защиту глаз?',
    'eye_project_desc': 'В зоне датчика обнаружено движение человека. Яркость проекции снижена, чтобы защитить глаза.',
    'eye_project_menu_close': 'Удерживайте @, чтобы закрыть',
    'eye_project_title': 'Интеллектуальная защита глаз',
    'file_manager_menu_title': 'В следующий раз вы сможете быстро открыть USB-накопитель через «Быстрые настройки»',
    'hdmi_menu_long_press': 'Удерживайте @, чтобы открыть',
    'hdmi_menu_press': 'Нажмите @, чтобы открыть',
    'hdmi_menu_title': 'В следующий раз вы сможете быстро открыть источник сигнала через «Быстрые настройки»',
    'low_power': 'Низкий заряд',
    'mic_effect_ktv': 'Караоке',
    'mic_effect_minions': 'Миньоны',
    'mic_effect_monster': 'Монстр',
    'mic_effect_origin': 'Оригинал',
    'microphone': 'Микрофон',
    'microphone_effect': 'Звуковой эффект: %s',
    'microphone_low_power': 'Низкий заряд микрофона',
    'peripheral_bluetooth': 'Bluetooth телефона',
    'peripheral_connect_success': 'Подключено',
    'peripheral_connecting': 'Подключение…',
    'peripheral_sound': 'Сабвуфер',
    'peripheral_tip_curtain': 'Умная штора',
    'peripheral_tip_microphone': 'Микрофон',
    'peripheral_tip_phone': 'Приложение на телефоне',
    'remote_control': 'Пульт ДУ',
    'super_resolution_desc': 'Управление в разделе «Настройки > Видео»',
    'super_resolution_desc_1': 'Управление в разделе «Настройки > Изображение»',
    'super_resolution_desc_2': 'Управление в разделе «Настройки > Яркость и экран»',
    'super_resolution_title': 'Суперразрешение включено',
    'text_measure_notice_title': 'Прошло 30 дней: посмотрим, насколько подрос(ла) %1$s',
    'text_measure_notice_title_mult': 'Не забудьте измерить текущий рост: %1$s и %2$s',
    'tip': 'Коротко нажмите кнопку питания на микрофоне, чтобы переключать звуковые эффекты.',
    'tip_exit_eyeprojection_text': 'Вы вышли из интеллектуальной защиты глаз',
    'tip_eyeprojection': 'Нажмите @, чтобы перейти',
    'tip_eyeprojection_path_text': 'Управление в разделе «Настройки > Общие»',
    'tip_measure_height': 'Нажмите @, чтобы измерить рост',
}

def main():
    m = json.loads((ROOT / 'russifier/manifest.json').read_text(encoding='utf-8'))
    assert m['version'] in ('1.19.41', NEW_VERSION), m['version']
    OUT.mkdir(exist_ok=True)
    (OUT / 'before').mkdir(exist_ok=True)
    shutil.copyfile(ROOT / 'russifier/manifest.json', OUT / 'before/manifest.json')
    stock = b21.stock_strings(STOCK / STOCK_APK)
    for key, value in STRINGS.items():
        assert key in stock, key
        original = stock[key].get('') or next(iter(stock[key].values()))
        assert b21.args(original) == b21.args(value), (key, original, value)
    work = Path(os.environ['TEMP']) / 'beam-batch23'
    shutil.rmtree(work, ignore_errors=True)
    work.mkdir(parents=True)
    built = b21.build(FILE, PACKAGE, TARGET, STRINGS, work)
    shutil.copyfile(built, PAYLOAD / FILE)
    shutil.copyfile(built, OUT / FILE)
    m['files'][FILE] = b21.sha(built)
    m.setdefault('resourceChecks', {})[TARGET] = dict(STRINGS)
    m['version'] = NEW_VERSION
    (ROOT / 'russifier/manifest.json').write_text(json.dumps(m, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    (OUT / 'build-report.json').write_text(json.dumps({'version': NEW_VERSION, 'strings': len(STRINGS), 'sha256': m['files'][FILE]}, indent=2) + '\n', encoding='utf-8')
    print(FILE, len(STRINGS), 'strings; built', NEW_VERSION)

if __name__ == '__main__':
    main()
