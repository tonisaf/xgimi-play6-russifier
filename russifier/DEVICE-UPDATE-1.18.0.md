# Atmosphere: плашка энергосбережения — 1.18.0

9 октября 2026. Установлено на XGIMI Play 6 / v1.7.116, helper versionCode 19. Обновление committed, журнал russifier/runs/20261009-215813-b475f1. Применение и точная проверка выполняются скриптом verify_device.py; результат в investigation/bound-startup-2026-10-08/final-verification.json.

Плашка в фотографии — drawable img_energy_dialog, res/MP.webp (466 × 171). Текст «任意门节能模式 / 已降低亮度以减少电量消耗» записан в пикселях картинки, а не в строковых ресурсах. Поэтому поиск RRO и literals не находил эти надписи.

BeamEnergy добавляет внутри штатной Cell подложку и две русские подписи: «Энергосбережение» / «Яркость снижена для экономии энергии». Иконка лампы, рамка, размер и положение плашки сохранены. Изменяется только classes2.dex. Таймер, EnergySaveManager, callback клавиш и управление яркостью не патчатся. BEAM Launcher не изменялся.

Сборка проверяет, что другие ZIP entries совпадают с оригиналом. Аудит: 23 payload SHA256 совпали, 159 проверок форматных контрактов прошли. Визуальный контроль новой плашки пока ожидает повторного срабатывания энергосбережения. Перезагрузка и смена темы в этой итерации не проверялись.

Рецепт: scripts/build_atmosphere_native.py. UI-подписи: scripts/BeamEnergy.smali. Предыдущие переводы Atmosphere включены в новый APK.

Поколение: `/data/local/beam-russifier-boot/releases/1.18.0-dcaebc592a8fe116`.

Atmosphere APK SHA256: `43bb6a7cbf156cba296da4aa2684a8513588a77ea61a67b368f468f83ec2c601`.

Helper SHA256: `8362d9f472c9269498a29dfb4ffc8711b5089b0e995f2815aeec38d015a57033`.
