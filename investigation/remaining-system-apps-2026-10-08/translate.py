from pathlib import Path
import json,re,hashlib,xml.etree.ElementTree as E

OUT=Path(__file__).resolve().parent
SP=Path(r'C:\Users\USER\AppData\Local\Temp\claude\C--Users-USER-TileLauncher\4a103049-a7f5-4062-923c-147b4e6834ae\scratchpad')
TEXT={
'systemui': '''
display_21to9_not_suppport_3d|3D недоступно в режиме широкого экрана
tilt_shift_open_auto_tilt_shift_title|Смещение уменьшит потерю качества (%ds)
tilt_shift_open_auto_tilt_shit_btn_ok|Сместить
tilt_shift_open_front_projection_guide_title|Направьте проектор прямо на экран, чтобы выровнять изображение (%ds)
tilt_shift_open_micro_tilt_shit_btn_ok|Точная настройка
tilt_shift_open_micro_tilt_shit_title|Точно настройте положение проектора (%ds)
tilt_shift_open_slide_projection_guide_title|Измените угол проектора, чтобы направить изображение в нужное место (%ds)
''',
'upgrade': '''
ab_background_download_hit|Обновление в фоне
ab_clear|Освободить место
ab_continue_background|Обновлять в фоне
ab_continue_download|Повторить
ab_download_now|Обновить сейчас
ab_reboot_now|Перезагрузить сейчас
ab_upgrade_fail|Не удалось обновить
app_force_upgrade_msg|Загрузка завершена. Обновить сейчас?
app_upgrade_msg|Доступно обновление приложения xxx. Обновить сейчас?
app_upgrade_tip|Обновление приложения
app_upgrading|Обновление приложения
app_upgrading_count|Завершено %1$d/%2$d
background_download_hit|Загрузка в фоне
cancel_download|Отмена
check_failure|Не удалось подключиться к серверу. Проверьте сеть и повторите попытку
check_now|Выполняется
checkout_upgrade_msg_hint|Доступно обновление %s
continue_background|Загружать в фоне
continue_download|Продолжить загрузку
current_show|Установлена последняя версия прошивки
default_next_update|Обновление при следующем включении
dialog_confirm|Подтвердить
dialog_confirm_|Понятно
dialog_message|Идёт загрузка прошивки. Выход отменит загрузку. Отменить?
dialog_next_remind|Напомнить позже
dialog_nomore_remind|Больше не напоминать
dialog_title|Уведомление
dialog_title_format|Обновление версии (INUI %s)
dialog_update_now|Обновить сейчас
dialog_update_shutdown|Обновить при выключении
download_complete_tip|Файл обновления системы загружен
download_complete_update_tips|Файл обновления системы загружен. Обновить сейчас?
download_error|Ошибка загрузки прошивки
download_now|Загрузить обновление
find_new_version|Доступна новая версия:
find_system_new_version|Доступна новая версия системы
have_new_version|Доступна новая версия
ignore|Пропустить эту версию
insufficient_storage|Недостаточно свободного места
inui_update_error|Не удалось обновить приложение
inui_update_error_reboot_again|Не удалось обновить приложение. Повторная попытка при выключении
lack_of_electricity|Заряд ниже 50%. Обновление недоступно
later|Позже
loading_home|Обновление главного экрана XGIMI…
md5_check|Проверка MD5
md5_fail_force|Не удалось проверить прошивку
md5_fail_force_toast|Не удалось проверить прошивку. Загрузите её заново
next_boot_update|Обязательное обновление загружено. Установка при следующем включении
ota_down_now|Обновить систему сейчас
ota_force_toast|Загрузка важного обновления
ota_force_upgrade_msg|Обновление системы загружено. Установить сейчас?
ota_upgrade_msg|Доступна новая версия системы. Обновить сейчас?
ota_upgrade_tip|Обновление системы
pause_download|Приостановить загрузку
please_insert_adapter|Подключите адаптер питания и повторите попытку
server_busy|Сервер занят. Повторите попытку позже
system_integry_failure|Проверка целостности системы не пройдена. Обновление недоступно
system_update|Обновление системы
system_update_low_power|Низкий заряд. Подключите адаптер питания для обновления
this_upgrade|Это обновление
tip_checking|Проверка
tip_downloadcomplete|Загрузка завершена
tip_downloading|Загрузка
tip_installing|Установка
toast_request_busy|Слишком частые запросы. Повторите попытку позже
update_check|Проверить обновления
update_content|Что нового
update_finish|Обновление завершено
update_loading|Проверка обновлений
update_next|При следующем включении
update_next_tip|Система обновится автоматически при следующем включении
update_now|Обновить и перезагрузить
update_now_tip|Устройство перезагрузится для установки обновления
update_title|Доступно важное обновление
upgrade_fail|Не удалось загрузить
upgrade_next|Обновить при следующем включении
upgrade_now|Обновить сейчас
upgrade_power_off|Обновить при выключении
''',
'wirelessscreen': '''
againBack|Для выхода нажмите дважды
allowed_this_time|Разрешить один раз
always_allowed|Разрешать всегда
android_cast_desc|Приложение XGIMI позволяет транслировать видео, ТВ и музыку с телефона на проектор
android_cast_title|Устройства Android
android_wired_desc|Поддерживаются только некоторые телефоны Android с USB-C. Отдельные версии Android могут быть несовместимы.\nПодключите кабель к USB-порту проектора и телефону
android_wired_title|Android: подключение кабелем
app_cast_detect|Диагностика трансляции
app_cast_net_delay|Задержка трансляции
app_cast_net_delay_higher_120|%1$d (рекомендуется менее 120 мс)
app_cast_net_delay_lower_120|%1$d (рекомендуется менее 120 мс)
app_cast_net_delay_suggest|Нажмите кнопку меню на пульте и уменьшите разрешение или максимальную частоту кадров трансляции
app_common_problem|Частые проблемы
app_common_problem_device|Не рекомендуется одновременно подключать много устройств к сети Wi-Fi для трансляции
app_common_problem_keep_memory|Убедитесь, что на устройстве достаточно свободной памяти
app_common_problem_reboot_route|Попробуйте перезагрузить роутер
app_detect_tip|Проверка займёт около 5 секунд. Не используйте устройство во время проверки
app_detectioning|Проверка
app_device_memory|Оперативная память
app_device_memory_bad|Высокая загрузка памяти устройства
app_device_memory_suggest|Периодически очищайте память в приложении обслуживания проектора. Удалите ненужные приложения
app_device_memory_well|Память устройства работает нормально
app_download|Отсканируйте код для установки XGIMI и подключения устройства
app_feedback_problem|Сообщить о проблеме
app_finish|Готово
app_mirror_power|Возможности трансляции
app_mirror_power_bad|Устройство не поддерживает трансляцию экрана с частотой 60 кадров/с
app_mirror_power_suggest|Нажмите кнопку меню на пульте и уменьшите максимальную частоту кадров трансляции
app_mirror_power_well|Устройство поддерживает трансляцию экрана с частотой 60 кадров/с
app_projection_desc|Подключите мобильное устройство и проектор к одной сети
app_projection_title|Видео и музыка
app_reboot_cast_service|Перезапуск службы трансляции
app_wifi_2g|Диапазон 2,4 ГГц
app_wifi_2g_suggest|Если роутер поддерживает Wi-Fi 5 ГГц, подключите оба устройства к одной сети этого диапазона
app_wifi_5g|Диапазон 5 ГГц
app_wifi_5g_suggest|Если уже используется Wi-Fi 5 ГГц, попробуйте изменить положение роутера. Стены, шкафы и другие препятствия ослабляют сигнал
app_wifi_net|Сеть Wi-Fi
apple_cast_desc|Трансляция с iPhone и iPad с iOS 4.2 или новее и компьютеров Mac с OS X.\n\nПодключите устройство Apple и проектор к одной сети
apple_cast_title|Устройства Apple
apple_wired_desc|Подключите кабель к USB-порту проектора и телефону
apple_wired_title|Apple: подключение кабелем
blackMirror|Это приложение запрещает захват экрана для трансляции
cast|Беспроводная трансляция
cast_devices_name|Имя устройства:
cast_name_defualt|Гостиная
cast_name_lebo_suffix| (с рекламой)
cast_ssid|Текущая сеть:
cast_sutitle|Huawei Cast+ передаёт содержимое телефона на проектор. Поддерживаются некоторые телефоны Huawei с EMUI 10.0 или новее
cast_title|Трансляция Huawei Cast+
change_the_password|Изменить пароль
connect_tv|хочет подключиться к вашему телевизору
connect_xgimi_sound|Недоступно при подключении к XGIMI Sound. Отключите колонку и повторите попытку
desc_line_ios_title|iPhone
desc_line_pc_desc|Подключите компьютер к проектору кабелем HDMI для дублирования экрана
desc_line_pc_tip|Подключите кабель HDMI к проектору и компьютеру
desc_line_pc_title|Компьютер
desc_line_tip|Подключите кабель к USB-порту проектора и телефону
desc_line_title_android|Телефон Android
detail_desc_android|Подключите телефон и проектор к одной сети
detail_desc_assitant|Отсканируйте код для управления проектором с телефона и трансляции видео
detail_desc_audio|Подключите мобильное устройство и проектор к одной сети
detail_desc_mac|Подключите Mac и проектор к одной сети
detail_desc_pc|Подключите компьютер и проектор к одной сети
device_name_keting|Гостиная
dialog_desc_sound|Выйти из трансляции по кабелю?
dialog_title_sound|Уведомление
exit_3d_mode_hint|Выключите режим 3D и повторите трансляцию
help_page_btn_feedback|Сообщить о проблеме
help_page_item_key_cast_error|Подключено, но трансляция не работает
help_page_item_key_disconnected|Трансляция прерывается
help_page_item_key_jerky|Трансляция тормозит
help_page_item_key_search|Устройство не найдено
home_btn_android|Трансляция Android
home_btn_assiant|Помощник XGIMI
home_btn_audio|Видео и музыка
home_btn_pc|Экран компьютера
home_topic_android|Телефоны и планшеты с Android 4.0 или новее
home_topic_ios|iPhone и iPad с iOS 4.2 или новее, компьютеры Mac с OS X
home_topic_pc|Передача видео и музыки, управление проектором через помощник XGIMI
huawei_cast_desc|Трансляция с Huawei с EMUI 10.0 или новее
huawei_cast_encode|Защита паролем
huawei_cast_pwd|Пароль
huawei_cast_tab_title|Телефон Huawei
huawei_cast_title|Huawei Cast+
key_help_hot_spot|Через точку доступа
key_help_more|Помощь XGIMI
key_help_restart|Перезапуск трансляции
key_huawei_cast|Huawei Cast+
key_local_video|Локальные файлы
key_mirror_wireless|Экран по Wi-Fi
key_video_app|Видеоприложения
key_wired_cast|Экран по кабелю
key_xgimi_app|Видео в приложении XGIMI
key_xgimi_app_space|Видео в приложении XGIMI
line_notice_des_android_1|Подключите проектор к устройству Android кабелем. В уведомлении на телефоне выберите «Просмотр»
line_notice_des_android_2|В окне браузера выберите «ОК», загрузите и установите приложение XGIMI
line_notice_des_android_3|После установки переподключите кабель. Подтвердите запуск приложения XGIMI для дублирования экрана
line_notice_des_android_4|(Если звук через XGIMI недоступен, подключите другую Bluetooth-колонку)
line_notice_des_mac_1|Подключите устройство iOS кабелем.\nВ уведомлении на устройстве iOS выберите «Доверять»
line_notice_des_mac_2|Если установлен код доступа, введите его.\nДублирование экрана начнётся через несколько секунд
line_notice_title_android|Подключение Android по кабелю
line_text|Телефон подключён. Подготовка трансляции по кабелю
main_tab_cast_android|Экран Android
main_tab_cast_help|Помощь
main_tab_cast_ios|Экран iPhone
main_tab_cast_pc|Экран компьютера
main_tab_cast_video|Видео и музыка
menu_tag_frame_rate|Частота кадров
menu_tag_player_type|Выбор плеера
menu_tag_resolution|Разрешение трансляции
menu_tag_speed|Скорость
miracast_desc|Трансляция с устройств, поддерживающих Miracast. При подключении проектор отключится от текущей сети Wi-Fi
mirror_tips|Для стабильной трансляции используйте Wi-Fi 5 ГГц
mx_line_notice_des_android_1|1. Установите приложение XGIMI
mx_line_notice_des_android_2|2. Переподключите кабель
mx_line_notice_des_android_3|3. Подтвердите запуск XGIMI и согласитесь с политикой конфиденциальности
mx_line_notice_des_mac_1|1. В уведомлении на iPhone выберите «Доверять»
mx_line_notice_des_mac_2|2. Введите код доступа iPhone, чтобы начать дублирование экрана
mx_line_notice_title_mac|Сигнал не найден. Выполните следующие действия
notification_cast_signal_error|Нестабильный сигнал трансляции
notification_do_env_detect|Проверить условия трансляции
password|Защита паролем
password_change|Пароль
password_title|Введите этот пароль на телефоне для начала трансляции
password_toast|Пароль должен содержать не менее 6 символов
pc_wired_desc|Подключите компьютер к проектору кабелем HDMI для дублирования экрана
pc_wired_title|Компьютер Windows
pc_wireless_desc|Используйте программу трансляции для беспроводной передачи экрана компьютера
pc_wireless_tab_title|Компьютер
pc_wireless_title|Экран компьютера
pin_code_title|Код подключения Huawei Cast+
player_type_auto|Автоматически
player_type_ijk_player|Сторонний плеер
player_type_media_player|Системный плеер
reboot_cast_service_failed|Не удалось перезапустить трансляцию. Повторите попытку
reboot_cast_service_success|Служба трансляции перезапущена
refuse|Отклонить
resolution_fhd|Высокое качество
resolution_hd|HD
resolution_sd|SD
safe_mode_check_update|Проверить обновления
safe_mode_clear_data|Очистить данные трансляции XGIMI\n(выйти из безопасного режима)
safe_mode_error_log|Показать полный текст ошибки
safe_mode_no_error_log|Журнал ошибок пуст
safe_mode_open_resource_manager|Открыть файловый менеджер
safe_mode_open_setting|Открыть настройки системы
safe_mode_tips|Из-за повторных сбоев трансляция XGIMI перешла в безопасный режим.\nПопробуйте очистить данные трансляции и открыть её заново. Если проблема сохраняется, обратитесь в поддержку
safe_mode_title|Безопасный режим
safe_mode_uninstall|Удалить обновление трансляции XGIMI\n(вернуть заводскую версию)
scan_qrcode_wechat_xgimiapp|Сканируйте код через WeChat или XGIMI
soft_ap_5g_tips|* Для стабильной трансляции рекомендуется Wi-Fi 5 ГГц
soft_ap_auto_close|* Точка доступа отключится после 30 минут без трансляции
soft_ap_net_err_check|* Ошибка сети. Проверьте подключение
softap_desc|Трансляция через точку доступа помогает при поиске устройства и нестабильном соединении
start_miracast|Подключиться
tab_title_app|Видео и музыка
tab_title_line|Экран по кабелю
tab_title_wireless|Экран по Wi-Fi
tip_disconnect_line_cast|Отключено. Переподключите кабель для продолжения
toast_text_media_player_error|Не удалось загрузить видео
toast_text_usb_connect_error|Ошибка дублирования экрана. Переподключите кабель
turnOffSpeed|Удерживайте Enter, чтобы скрыть скорость сети
turnOnSpeed|Удерживайте Enter, чтобы показать скорость сети
use_toast|Поддерживаются некоторые телефоны Huawei с EMUI 10.0 или новее
using_step1|Подключите телефон и проектор к одной сети Wi-Fi. В панели телефона выберите «Беспроводная проекция»
using_step2|Выберите найденный проектор для трансляции
vcontrol_assiant_desc|Приложение XGIMI позволяет транслировать видео, ТВ и музыку с телефона на проектор
vcontrol_assiant_title|Приложение XGIMI
''',
'instruction30': '''
fetch_play_link_failed|Не удалось открыть видео. Попробуйте другое
instruction|Руководство
menu|Нажмите img или img для выбора качества и серии
menu_audio|Режим звука
menu_episode|Список видео
menu_hd_play|HD
menu_img_football|Футбол
menu_img_mode_bright|Яркий
menu_img_mode_game|Игровой
menu_img_mode_light_on|При включённом свете
menu_img_mode_natural|Естественный
menu_img_mode_office|Офисный
menu_img_mode_soft|Мягкий
menu_img_mode_standard|Стандартный
menu_img_mode_user|Пользовательский
menu_picture|Режим изображения
menu_sd_play|SD
menu_speed|Скорость воспроизведения
menu_super_play|Высокое качество
menu_surface|Формат изображения
menu_vision|Качество
network_exception|Ошибка сети. Проверьте подключение и повторите попытку
online_playaddress_empty|Не удалось получить ссылку на видео
play_continue|Нажмите OK, чтобы продолжить
play_video_error|Ошибка воспроизведения
play_video_exception|Ошибка воспроизведения
press_again_finish|Нажмите ещё раз для выхода
progress_wait_fail|Произошла ошибка
progress_wait_loading|Загрузка видео. Подождите…
start_continue|Воспроизведение продолжено. Нажмите OK, чтобы начать заново
starting|Скоро начнётся воспроизведение
toast_no_next|Это последняя серия
toast_no_previous|Это первая серия
toast_play_complete|Воспроизведение завершено
toast_playing_next|Сейчас начнётся следующая серия
toast_playing_previous|Воспроизведение предыдущей серии
up_success|Оценка сохранена
vip_buy_before_play|Для просмотра нужна подписка
'''}

data={}
for app,lines in TEXT.items():
    values={}
    for line in re.split(r'\n(?=[a-zA-Z0-9_]+\|)',lines.strip()):
        key,value=line.split('|',1)
        assert key not in values,key
        values[key]=value
    data[app]=values
candidates=json.loads((OUT/'candidates.json').read_text(encoding='utf-8'))
for app,values in candidates.items():
    assert set(values)==set(data[app]),(app,set(values)-set(data[app]),set(data[app])-set(values))
skin={x.get('name'):''.join(x.itertext()) for x in E.parse(r'C:\Users\USER\TileLauncher\skin\res\values\strings.xml').getroot() if x.tag=='string'}
for app in ['upgrade','wirelessscreen','instruction30']:
    for x in E.parse(SP/'res6'/app/'res/values/strings.xml').getroot():
        key=x.get('name');text=''.join(x.itertext())
        if x.tag=='string' and re.search('[\u4e00-\u9fff]',text) and key in skin and re.search('[А-Яа-яЁё]',skin[key]):
            data[app].setdefault(key,skin[key])
    if app=='upgrade':data[app]['app_name']='Обновление системы'
    if app=='wirelessscreen':data[app]['app_name']='Трансляция XGIMI'
    local=SP/'apps'/('com.xgimi.'+app+'.apk')
    print(app,len(data[app]),hashlib.sha256(local.read_bytes()).hexdigest())
(OUT/'translations.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
