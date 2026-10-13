# Меню выключения — русский перевод установлен

Целевой пакет com.xgimi.shutdown, оригинальный APK /vendor/priv-app/release_838_shutdown/release_838_shutdown.apk. SHA256 оригинала 6b2e3298157de17091d6fd69093181733b6038aa9c107571f53439db98705d23.

Создан resource-only RRO com.beam.translation.shutdown 1.0, 32 строки. Переведены четыре кнопки (Выключить экран, Выключить, Перезагрузить, Таймер выключения), отмена/уведомления/сроки таймера, режим сна, ожидания, перевозки и сообщения об обновлении. resetTv (JSON управляющих действий) и DEX не менялись. Все целевые ключи и форматные %d проверены с оригиналом; RRO не содержит кода. SHA256 c1aa423a72f091644f9eda4c777cf95aa8c3f82efa85f071319b61a37a264ecc.

RRO включён штатным механизмом через root idmap2 public/ignore-overlayable; STATE_ENABLED и lookup подтверждены. Результат root-helper: system-access-2026-10-07/shutdown-rro-apply.json. Изображение menu-ru.png подтверждает русский текст всех четырёх кнопок без обрезания. Выключение, перезагрузка, погашение экрана и установка таймера не запускались.

Код открытия проверен в SystemUIService.onStartCommand и PowerUI.dispatchAction. Безопасная проверка выполнена после am force-stop com.xgimi.shutdown, затем один вызов сервиса:

```sh
am startservice -n com.xgimi.shutdown/com.xgimi.systemui.service.SystemUIService -a com.xgimi.action.shutdown --es action com.xgimi.action.WINODWSYSTEM
```

Нельзя бездумно повторять этот вызов при открытом меню: dispatchAction в некоторых состояниях вызывает PowerUtils.shutDown. Для повторного снимка сначала закрыть окно кнопкой Назад или перезапустить только приложение меню, затем открыть один раз. Долгое/повторное нажатие питания для автоматической проверки не использовалось.

Пакет включён в русификатор 1.1.0: payload/shutdown.apk, manifest содержит SHA256 оригинального Shutdown APK, пять overlays. Установщик перезапускает сервис без action, что по коду не открывает меню и не выключает устройство. Проверяет lookup restart, PID и crash-журнал com.xgimi.shutdown. Общая установка 1.1.0 на текущем проекторе прошла успешно: пять RRO включены, новых FATAL EXCEPTION у Settings и Shutdown нет. Доступные журналы — russifier/runs/latest-install.txt и verification.json соответствующего запуска.

Условные сообщения, другие варианты меню, таймер и обновление на экране не запускались; их ресурсный перевод подтверждён сопоставлением. Сохранение после перезагрузки пока не проверено. Отмена только этого перевода: cmd overlay disable --user 0 com.beam.translation.shutdown и перезапуск сервиса без action.
