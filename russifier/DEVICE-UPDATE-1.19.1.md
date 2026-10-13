# Имена заставок Atmosphere — 1.19.1

9 октября 2026. Helper versionCode 21, UPDATE_BOOT committed. Журнал russifier/runs/20261009-222539-e0e982. StartupBridge сохранён обновлятором; last.log: restore=ok.

Предыдущая версия переводила обычный TextComponent, но имя заставки в ScreensaverInfoCell.d использует SpannableTextComponent2.setText(CharSequence). Добавлен вызов существующего BeamCatalog.translate перед передачей String в этот компонент. Меняется только аргумент отображения; модель, URL, ID, выбранные настройки и getters не изменены. В APK изменяется только classes2.dex, прочие entries совпадают с оригиналом.

До исправления .local/atmo-name-before.png показывает китайское имя 夜幕星河. После установки .local/atmo-name-after.png показывает русский заголовок «Мерцание звёзд». Приложение после перезапуска открыло другую текущую заставку, поэтому это не сравнение одного названия до/после. Словарь включает 105 известных строк с вариантами пробелов; неизвестные названия не переводятся автоматически.

Аудит: 23 payload SHA256 совпали, 159 проверок форматов прошли. Финальная проверка устройства: investigation/bound-startup-2026-10-08/final-verification.json. Холодная перезагрузка 1.19.1 в этой итерации не выполнялась. BEAM Launcher не менялся.

Поколение: `/data/local/beam-russifier-boot/releases/1.19.1-8f56d39722df1244`.

Atmosphere APK SHA256: `494920ba74107c9c24b49c80ff0346b9b879da2a57ccb4fc1f8e156372052826`.

Helper SHA256: `a2d2f29b00a8814d9168dfc73f55cf87d0531b37f330068781aa3ccd57140f79`.

Версия принята пользователем 9 октября 2026. Статус и границы доказательств: [RELEASE-1.19.1.md](RELEASE-1.19.1.md).
