# Последние два приложения — 1.12.0

Установлено и проверено на XGIMI Play 6, Android 11, v1.7.116. Успешный запуск установщика: russifier/runs/20261008-193926-fa7976.

## Изменения

- com.xgimi.gmservice: 19 ресурсных строк через RRO, 73 известных отображаемых текста через BeamRu. Перехвачены 35 вызовов отображения (30 TextComponent.setText и 5 toast). Названия/ID серверных сущностей и логика действий не изменены.
- com.xgimi.user: xgimi_service_name → Сервис XGIMI. Это реальная launcher activity com.xgimi.account.ui.XgimiServiceActivity, открывающая help app.
- com.android.newsettings: app_name → Настройки XGIMI. MockActivity по исходному коду сразу закрывается; поведение сохранено.
- В гарантии четыре подписи преимуществ уменьшены с 28 до 22, сокращены подписи и подсказка QR. Последний снимок подтверждает, что QR целиком помещается в 1920x1080.

## Проверено

Главный экран помощи, переход в категорию Сеть, экран гарантии, обновление обоих launcher labels. Снимки service-final.png, warranty-final.png, faq-final.png, launcher-final.png. crash.txt пуст: crash buffer процесса 29185. Установщик проверил 899 ресурсов, 28 массивов, 14 RRO и runtime native mounts; 13 исходных APK защищены SHA256. 14 тестов установщика прошли до финальной установки. Откат промежуточных кандидатов проверен, финальный payload специально не откатывался.

## Ограничение

Серверные вопросы, HTML-статьи и изображения справки остаются на китайском: проверено в категории Сеть. Неизвестный текст mapper оставляет без изменения. Runtime native bind mounts снимаются после полной перезагрузки: повторить INSTALL.cmd. Исходные system/vendor APK не переписаны.

## Артефакт

 dist/beam-russifier-play6-v1.12.0.zip, 88829177 байт, SHA256 747cf1578aa70359c67a8af76911898e65ca69f6aa98ce5e889a766af047f5f9.
Native help SHA256 eeb9b3afbf8e091ffe5baa63a371e25970d9501dd13b78ab967fdeb9f56c9479, исходный APK 5d3d6444bcf8ffb4717db81a3f36b44fdf655df045d8cb921ee3ffbd4753f797. Backing /data/local/tmp/beam-russifier-gmservice-v1.apk. Build hashes сохранены в build.json.
