# Установка не на Windows 10/11: Linux, macOS, старые Windows

Окно установщика (`XgimiInstaller.exe`) работает только в **Windows 10/11, 64-разрядная** (проверено на Windows 11).
Но весь перевод ставится обычными командами `adb`, поэтому на другой системе его тоже можно поставить.
Эти способы **не входят в проверенный набор**: основной путь — окно установщика. Если что-то пойдёт не так — пишите, приложив вывод команд.

Подходит только проектор **XGIMI Play 6, прошивка v1.7.116** (Android 11). На другой прошивке не ставьте.

## Что нужно в любом случае

1. Распакуйте комплект (ZIP) в папку без пробелов в пути и без русских букв.
2. Установите `adb` (Android platform-tools): Linux — `sudo apt install adb` (или пакет `android-tools`), macOS — `brew install android-platform-tools`,
   любая ОС — архив «SDK Platform-Tools» с developer.android.com.
3. Включите ADB на проекторе (в штатных настройках его нет), см. START-HERE.txt: через приложение **SystemUI Tuner** — включить ADB, узнать IP проектора.
4. Русский язык на проекторе включать заранее не нужно: установка включит его сама (потребуется одна перезагрузка).
5. Подключитесь: `adb connect 192.168.1.50:5555` (свой IP) и **разрешите отладку на экране проектора** («Всегда разрешать»).

## Способ А (рекомендуется): те же скрипты, что в окне установщика, через Python

Нужен Python 3.10 или новее (проверено на 3.14). `adb` берётся из PATH; если он лежит в другом месте:
`export XGIMI_ADB=/путь/к/adb`.

Команды выполняются из папки `Beam-Russifier-Play6` комплекта (в Windows замените `python3` на `python`):

```bash
python3 launch.py check --device 192.168.1.50:5555            # проверка: прошивка, оригинальные файлы, права
python3 launch.py prepare-install --device 192.168.1.50:5555 --timezone Europe/Moscow --disable-services --install-beam
python3 launch.py install-remote --device 192.168.1.50:5555   # модуль кнопок пульта (по желанию)
python3 launch.py finish-setup --device 192.168.1.50:5555     # перезагрузка и включение служб (ОБЯЗАТЕЛЬНО после первой установки)
```

- `--timezone`, `--disable-services`, `--install-beam` — необязательные: часовой пояс, отключение фоновых китайских служб, лаунчер BEAM. Что не нужно — уберите.
- Обновление при выходе новой версии: `python3 launch.py update-boot --device 192.168.1.50:5555`.
- Убрать автозапуск: `python3 launch.py remove-autostart --backup <папка-резервной-копии> --device …`; вернуть: `recover-autostart` с теми же параметрами.
- Журналы каждого запуска лежат в `runs/`; при проблемах приложите их.

## Способ Б: голые команды adb (без Python)

В комплекте есть готовый скрипт `manual-adb.sh` (Linux/macOS, bash). Он выполняет ровно то, что написано ниже:

```bash
bash manual-adb.sh 192.168.1.50:5555
```

Он ставит перевод **системных окон и приложений**, но не делает: часовой пояс, перевод каталога заставок и быстрой панели (база данных),
BEAM, модуль кнопок пульта, отключение фоновых служб. Для них используйте способ А или окно установщика на Windows.

### Команды вручную

Дальше `A` — это `adb -s 192.168.1.50:5555`. Пути — относительно папки комплекта (в ней есть `payload/` и `boot-helper/`).

**1. Проверка.** Все строки должны дать указанный результат (язык на этом этапе может быть любым):

```bash
A="adb -s 192.168.1.50:5555"
$A shell getprop ro.build.fingerprint     # XGIMI/Product_dayao/dragon_healthy:11/RP1A.200720.011/v1.7.116:user/dev-keys
$A shell getenforce                       # Permissive
$A shell pm list packages | grep -E 'com.beam'    # ничего (чистая первая установка)
```

**2. Русский язык** (если он ещё не включён; на свежем проекторе его нет):

```bash
$A shell setprop persist.sys.locale ru-RU
$A reboot        # подождите, пока проектор загрузится, и подключитесь снова
```

**3. Пакеты перевода (21 штука):**

```bash
for f in systemui settings ambient atmosphere shutdown smartaccessories ota.accessories xgimiiotserver upgrade \
         wirelessscreen instruction30 manager gmservice user framework-power config xrmservice soundermode frameworkui vcontrol gimiplayer; do
  $A install -r payload/$f.apk
done
```

**4. Файлы «поколения» на проектор.** Имя каталога — поле `directory` в `boot-helper/build-info.json`
(для версии 1.19.44: `/data/local/beam-russifier-boot/releases/1.19.44-3d09369163b99a3e`). Сначала положите файлы в обычную папку:

```bash
S=/data/local/tmp/gen-stage
$A shell "rm -rf $S; mkdir -p $S"
for f in panel wirelessscreen-native gmservice-native systemui-native atmosphere-native upgrade-native shutdown-native manager-native ota-accessories-native skin; do
  $A push payload/$f.apk $S/$f.apk
done
$A push boot-helper/apply.sh $S/apply.sh
$A push boot-helper/skin.sh  $S/skin.sh
```

Теперь перенесите их в каталог поколения **от имени root**. Root на проекторе выдаёт штатная служба XGIMI: она выполняет команду из свойства
`vendor.xgimi.system.debug.cmd`, когда выставлено `vendor.xgimi.system.debugserver=1`. Создайте файл `stage.sh` (подставьте свой каталог в `G`):

```sh
#!/system/bin/sh
G=/data/local/beam-russifier-boot/releases/1.19.44-3d09369163b99a3e
S=/data/local/tmp/gen-stage
test ! -e $G && mkdir -p ${G%/*} && rm -rf $G.new && mkdir $G.new || exit 1
for f in $(ls $S); do
  cp $S/$f $G.new/$f; chown root:root $G.new/$f; chmod 644 $G.new/$f
  case $f in *.apk) chcon u:object_r:system_file:s0 $G.new/$f;; esac
done
chmod 755 $G.new; mv $G.new $G; rm -rf $S
echo 0 > /data/local/tmp/stage.done
```

И запустите его через эту службу (канал должен быть свободен: оба свойства пустые):

```bash
$A push stage.sh /data/local/tmp/stage.sh
$A shell getprop vendor.xgimi.system.debug.cmd        # должно быть пусто; если нет — подождите минуту
$A shell "setprop vendor.xgimi.system.debug.cmd '/system/bin/sh /data/local/tmp/stage.sh'; setprop vendor.xgimi.system.debugserver 1"
# ждите, пока файл появится (несколько секунд):
$A shell "test -f /data/local/tmp/stage.done && cat /data/local/tmp/stage.done"
$A shell "setprop vendor.xgimi.system.debugserver ''; setprop vendor.xgimi.system.debug.cmd ''; rm -f /data/local/tmp/stage.*"
```

**5. Применить перевод** (подключает исправленные APK, оверлеи и скин; ~10 секунд). Путь — тот же каталог `G`:

```bash
G=/data/local/beam-russifier-boot/releases/1.19.44-3d09369163b99a3e
$A shell "setprop vendor.xgimi.system.debug.cmd '/system/bin/sh $G/apply.sh'; setprop vendor.xgimi.system.debugserver 1"
# через ~15 секунд:
$A shell "cmd overlay list | grep -c '\[x\] com.beam.translation'"       # должно быть 21
$A shell "setprop vendor.xgimi.system.debugserver ''; setprop vendor.xgimi.system.debug.cmd ''"
```

**6. Автозапуск после перезагрузок — helper:**

```bash
$A install -r boot-helper/boot-helper.apk
$A reboot
```

**7. После перезагрузки (подождите минуту после появления экрана) включите службу helper:**

```bash
$A shell settings get secure enabled_accessibility_services     # запомните то, что там есть
$A shell "settings put secure enabled_accessibility_services 'com.xgimi.duertts/.MonitorService:com.beam.russifier.boot/com.beam.russifier.boot.StartupBridge'"
$A shell settings put secure accessibility_enabled 1
```

(Если в первой строке были другие службы, оставьте их в списке через `:`.) Подождите 30 секунд и проверьте, что запись на месте — иначе повторите шаг после ещё одной перезагрузки.
Почему так: система XGIMI выгружает фоновые приложения и при этом снимает с них службу доступности; правила, которые это запрещают, читаются только при загрузке.

**8. Проверка:** `cmd overlay list | grep -c '\[x\] com.beam.translation'` — 21; перезагрузите ещё раз: через ~25 секунд после включения перевод на месте.

### Удаление (откат)

```bash
$A shell settings put secure enabled_accessibility_services com.xgimi.duertts/.MonitorService
$A shell am force-stop com.beam.russifier.boot
$A uninstall com.beam.russifier.boot
for p in $($A shell pm list packages | tr -d '\r' | sed 's/package://' | grep '^com.beam.translation\.'); do $A uninstall $p; done
# затем от root (через stage.sh, как в шаге 4):  rm -f /data/local/xgimi_gmui_manager/sys_pkg_adj.json
#                                            setprop persist.sys.xgimi.themeV2.url ""
#                                            rm -rf /data/local/beam-russifier-boot
$A reboot        # оригинальные APK возвращаются при перезагрузке
```

Проще и надёжнее откатывать способом А: `python3 launch.py rollback --device 192.168.1.50:5555` (в Windows — `ROLLBACK.cmd`).
