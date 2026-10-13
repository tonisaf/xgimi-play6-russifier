# Экран выключения и перезагрузки — 1.19.3

9 октября 2026. В framework-res.apk найдены OEM-строки xgimi_warn_turnoff («正在关机…») и xgimi_warn_restart («正在重启…»). Пакет com.beam.translation.frameworkpower переводит только их: «Выключение…» и «Перезагрузка…». Исходный framework-res.apk не изменяется.

Рецепт: scripts/build_framework_power.py. Устанавливается RRO без кода с targetPackage=android и явным targetName. Как для остальных пакетов русификатора, диагностический доступ используется для idmap2 с public / ignore-overlayable. Без targetName PackageManager отказывает в установке из-за различающихся подписей.

Пробная установка: russifier/runs/20261009-224830-e13129/framework-power-result.json. Подтверждены STATE_ENABLED и точные русские значения обеих строк через cmd overlay lookup. Это проверка ресурсов; сам экран выключения пользователь ещё не проверил.

Пакет добавлен в manifest, проверки целостности и ресурсов, установку, откат и восстановление при загрузке. В комплекте теперь 15 RRO. Helper versionCode 23 установлен через UPDATE_BOOT; журнал russifier/runs/20261009-224906-6f64ae. Поколение: /data/local/beam-russifier-boot/releases/1.19.3-943657df4be56494.

SHA256 оригинального framework-res.apk: 82b06bd7cba9faf3acbdbaf409b7b514e3559209acc18cd99026844ca86f5f66.
SHA256 RRO: dc9ea97291b2089bfaae61a3b1bfe3f5f65685083e0052d23884018e35890fdf.

Аудит: 24 payload SHA256 совпали, 159 проверок форматов прошли. Собран отдельный dist/beam-russifier-play6-v1.19.3.zip; предыдущие архивы сохранены. Полная перезагрузка и визуальная проверка экрана после обновления не выполнялись. BEAM Launcher не изменён.
