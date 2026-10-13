#!/usr/bin/env bash
# XGIMI Play 6: установка перевода ТОЛЬКО через adb (без Python и без окна установщика).
# Работает в Linux и macOS (bash), нужен `adb` в PATH. Запуск из корня распакованного комплекта:
#     bash manual-adb.sh 192.168.1.50:5555
# Что делает: ставит 21 пакет перевода, кладёт «поколение» файлов на проектор, один раз применяет его от root,
# ставит helper автозапуска, перезагружает проектор и заново включает службу helper (см. MANUAL-OTHER-OS.md).
# Чего НЕ делает: часовой пояс, перевод каталога заставок и быстрой панели, BEAM, модуль кнопок пульта.
set -euo pipefail

DEVICE=${1:?укажите адрес проектора, например 192.168.1.50:5555}
KIT=${2:-.}
A="adb -s $DEVICE"
export MSYS_NO_PATHCONV=1            # только для Git Bash в Windows: не переписывать пути вида /data/...

reboot_and_wait() {      # перезагрузка и ожидание полной загрузки (минимум 60 с аптайма)
  local boot; boot=$($A shell cat /proc/sys/kernel/random/boot_id | tr -d '\r')
  $A reboot; sleep 20
  until [ "$($A shell getprop sys.boot_completed 2>/dev/null | tr -d '\r')" = 1 ] && [ "$($A shell cat /proc/sys/kernel/random/boot_id 2>/dev/null | tr -d '\r')" != "$boot" ]; do
    $A connect "$DEVICE" > /dev/null 2>&1 || true; sleep 5
  done
  until [ "$($A shell cat /proc/uptime | cut -d. -f1)" -ge 60 ]; do sleep 3; done
}

step() { printf '\n== %s\n' "$*"; }
fail() { printf 'ОШИБКА: %s\n' "$*" >&2; exit 1; }

# --- root-команды: у проектора есть служба, которая запускает скрипт от root по двум свойствам -------------
rootrun() {      # $1 = файл с командами, которые нужно выполнить от root
  local t=/data/local/tmp/rr-$RANDOM$RANDOM wrap; wrap=$(mktemp "$KIT/.rr.XXXXXX")
  { echo '#!/system/bin/sh'; echo 'umask 022'; echo '('; echo 'set -e'; cat "$1"; echo ") > $t.log 2>&1"; echo "echo \$? > $t.done"; } > "$wrap"
  $A push "$wrap" "$t.sh" > /dev/null
  for _ in $(seq 90); do [ -z "$($A shell getprop vendor.xgimi.system.debug.cmd | tr -d '\r')" ] && break; sleep 1; done
  $A shell "setprop vendor.xgimi.system.debug.cmd '/system/bin/sh $t.sh'; setprop vendor.xgimi.system.debugserver 1"
  for _ in $(seq 120); do $A shell "test -f $t.done" && break; sleep 1; done
  local code; code=$($A shell "cat $t.done" | tr -d '\r\n')
  $A shell "cat $t.log; setprop vendor.xgimi.system.debugserver ''; setprop vendor.xgimi.system.debug.cmd ''; rm -f $t.sh $t.log $t.done"
  rm -f "$wrap"
  [ "$code" = 0 ] || fail "root-команда завершилась с кодом $code"
}

step "0. Проверка проектора и комплекта"
$A connect "$DEVICE" > /dev/null || true
[ "$($A get-state | tr -d '\r')" = device ] || fail "проектор не подключён по adb (проверьте IP, что ADB включён в SystemUI Tuner и что компьютер с проектором в одной сети)"
FINGERPRINT='XGIMI/Product_dayao/dragon_healthy:11/RP1A.200720.011/v1.7.116:user/dev-keys'
[ "$($A shell getprop ro.build.fingerprint | tr -d '\r')" = "$FINGERPRINT" ] || fail "прошивка не v1.7.116 (Play 6): комплект проверен только на ней"
[ "$($A shell getenforce | tr -d '\r')" = Permissive ] || fail "SELinux не в режиме Permissive: способ не подходит"
$A shell pm list packages | grep -q 'com.beam.russifier.boot' && fail "helper уже установлен: используйте обновление, а не первую установку"
$A shell pm list packages | grep -q 'com.beam.translation' && fail "пакеты перевода уже установлены: сначала удалите их"
if [ "$($A shell getprop persist.sys.locale | tr -d '\r')" != ru-RU ]; then
  echo "Включаю русский язык и перезагружаю проектор (один раз)…"
  $A shell setprop persist.sys.locale ru-RU
  reboot_and_wait
  [ "$($A shell getprop persist.sys.locale | tr -d '\r')" = ru-RU ] || fail "не удалось включить русский язык: выберите его в настройках проектора и повторите"
fi
GEN=$(grep -o '"directory": *"[^"]*"' "$KIT/boot-helper/build-info.json" | cut -d'"' -f4)
[ -n "$GEN" ] || fail "не найден каталог поколения в boot-helper/build-info.json"
echo "каталог поколения на проекторе: $GEN"

step "1. Установка 21 пакет перевода (оверлеи)"
for f in systemui settings ambient atmosphere shutdown smartaccessories ota.accessories xgimiiotserver upgrade \
         wirelessscreen instruction30 manager gmservice user framework-power config xrmservice soundermode frameworkui vcontrol gimiplayer; do
  printf '  %-22s ' "$f.apk"; $A install -r "$KIT/payload/$f.apk" | tail -1
done

step "2. Файлы поколения: 9 исправленных APK, скин и два скрипта"
STAGE=/data/local/tmp/gen-stage
$A shell "rm -rf $STAGE; mkdir -p $STAGE"
for f in panel.apk wirelessscreen-native.apk gmservice-native.apk systemui-native.apk atmosphere-native.apk \
         upgrade-native.apk shutdown-native.apk manager-native.apk ota-accessories-native.apk skin.apk; do
  $A push "$KIT/payload/$f" "$STAGE/$f" > /dev/null
done
$A push "$KIT/boot-helper/apply.sh" "$STAGE/apply.sh" > /dev/null
$A push "$KIT/boot-helper/skin.sh" "$STAGE/skin.sh" > /dev/null
STAGESH="$KIT/.stage.$$.sh"
cat > "$STAGESH" <<EOF
G=$GEN
S=$STAGE
test ! -e \$G
mkdir -p \${G%/*}
N=\$G.new
rm -rf \$N; mkdir \$N
for f in \$(ls \$S); do
  cp \$S/\$f \$N/\$f
  chown root:root \$N/\$f
  chmod 644 \$N/\$f
  case \$f in *.apk) chcon u:object_r:system_file:s0 \$N/\$f;; esac
done
chmod 755 \$N
mv \$N \$G
rm -rf \$S
ls \$G
EOF
rootrun "$STAGESH"; rm -f "$STAGESH"

step "3. Применение перевода от root (подключает APK, оверлеи и скин)"
for _ in $(seq 90); do [ -z "$($A shell getprop vendor.xgimi.system.debug.cmd | tr -d '\r')" ] && break; sleep 1; done
$A shell "setprop vendor.xgimi.system.debug.cmd '/system/bin/sh $GEN/apply.sh'; setprop vendor.xgimi.system.debugserver 1"
for _ in $(seq 180); do $A shell "test -f $GEN/done" && break; sleep 1; done
echo "результат apply.sh (последняя цифра 0 = успех): $($A shell "cat $GEN/done" | tr -d '\r')"
echo "включённых пакетов перевода: $($A shell "cmd overlay list | grep -c '\[x\] com.beam.translation'" | tr -d '\r') (должно быть 21)"

step "4. Установка helper автозапуска"
$A install -r "$KIT/boot-helper/boot-helper.apk" | tail -1

step "5. Перезагрузка проектора (правила памяти XGIMI читаются только при загрузке)"
reboot_and_wait

step "6. Включение службы helper в «Специальных возможностях»"
SERVICE=com.beam.russifier.boot/com.beam.russifier.boot.StartupBridge
CUR=$($A shell settings get secure enabled_accessibility_services | tr -d '\r')
case "$CUR" in ''|null) NEW=$SERVICE ;; *) NEW="$CUR:$SERVICE" ;; esac
$A shell "settings put secure enabled_accessibility_services '$NEW'; settings put secure accessibility_enabled 1"
echo "ждём 30 секунд: запись должна удержаться, а helper — применить перевод"
sleep 30
$A shell settings get secure enabled_accessibility_services | tr -d '\r' | grep -q "$SERVICE" || fail "система сняла службу helper; перезагрузите проектор и повторите шаг 6"

step "7. Проверка"
echo "службы доступности : $($A shell settings get secure enabled_accessibility_services | tr -d '\r')"
echo "пакетов перевода   : $($A shell "cmd overlay list | grep -c '\[x\] com.beam.translation'" | tr -d '\r') из 21 включено"
echo "скин               : $($A shell getprop persist.sys.xgimi.themeV2.url | tr -d '\r')"
echo
echo "Готово. Перезагрузите проектор ещё раз и убедитесь, что перевод остаётся (он применяется сам, около 25 секунд после включения)."
