# Сеть и стиль темы — 8 октября 2026

Установлено через общий русификатор 1.9.0. Быстрая Сеть: нижняя кнопка «Настройки сети». Стиль темы: «Светлая», «Тёмная», «Синяя», «Авто»; текущее значение в Общих — «Синяя». Визуальные доказательства network-final.png, theme-final.png, general-final.png. Тема и Wi-Fi не переключались.

Кнопка сети — один литерал WifiDialog$cell$2 в classes5.dex. Названия тем из конфигурации переводит отдельный ThemeEntity.getDisplayName(): заменены только вызовы для подписей в ThemeAdapter и ThemeRepository. getName() для action ID сохранён, getThemePath() и команды выбора не менялись. Статус Авто — отдельный литерал. Отображение дневной/ночной темы, дополнительных настроек и уведомления о сети дополняет RRO: 166 строк, обе прежние разметки, все 159 прежних переводов сохранены. Эти условные подписи проверены ресурсами, отдельно визуально не вызывались.

Оригинальный native base: investigation/settings-literals-2026-10-08/beam-settings-panel-ru-v5.apk. Пересобраны classes5 и classes6; прежние UI/Видео/HDMI патчи повторно применены из сохранённых исходников. Остальные ZIP entries, включая classes4 с яркостью/датой/Bluetooth, сохранены. Сборка build.py; checks.json; build.json. Новый mount backing /data/local/tmp/beam-russifier-panel-v4.apk отдельно от предыдущих, исходный APK не переписывается.

Итоговая установка runs/20261008-175136-f252a3. 729 строковых lookup и 28 массивов прошли; 14 локальных тестов прошли. PID настроек 21323, нет FATAL EXCEPTION в crash-final.log. RRO settings SHA bdd4ae2b1f0f992a2a49237410a490eb9a9cae7e6880bf852f11afaa105620b1; panel SHA 44e06a37ddc4b6680c2a39141550c29cf7d02d2365b660d72409bba9505b2683.

ZIP dist/beam-russifier-play6-v1.9.0.zip, 80680952 байта, SHA a3973cfca8a07b72c26bac5a04a809bc0621ddd83857429eb86655ec248e5566, CRC проверен, 93 файла, без пользовательских backups/DB/cache. Применение native временное до reboot; затем повторить INSTALL.cmd. Записано в Notion журнал.
