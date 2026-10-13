#!/system/bin/sh
umask 022
D=/data/local/beam-russifier-boot/releases/1.19.45-3a892d950f7f1e77
RUN=$(cat /proc/sys/kernel/random/uuid)
finish() { code=$?; if [ "$(getprop vendor.xgimi.system.debug.cmd)" = "/system/bin/sh $D/skin.sh" ]; then setprop vendor.xgimi.system.debug.cmd ""; setprop vendor.xgimi.system.debugserver ""; fi; printf "%s %s\n" "$RUN" "$code" > "$D/done"; chmod 644 "$D/done"; }
trap finish EXIT
exec > "$D/last.log" 2>&1
set -e
echo "boot=$(cat /proc/sys/kernel/random/boot_id)"
id
test "$(getprop ro.build.fingerprint)" = XGIMI/Product_dayao/dragon_healthy:11/RP1A.200720.011/v1.7.116:user/dev-keys
test "$(getprop ro.build.version.sdk)" = 30
test "$(getprop persist.sys.locale)" = ru-RU
test "$(getenforce)" = Permissive
echo "start_uptime=$(cut -d " " -f 1 /proc/uptime) boot_completed=$(getprop sys.boot_completed)"
check_hash() { actual=$(sha256sum "$1" | cut -d " " -f 1); test "$actual" = "$2"; }
check_hash "$D/skin.apk" 102a848f421e2954f6feb98e4fe6ad3ed14c6a55464579c55a65778b5e56c2a1
if [ "$(getprop persist.sys.xgimi.themeV2.url)" != "$D/skin.apk" ]; then
  setprop persist.sys.xgimi.themeV2.url "$D/skin.apk"
  am force-stop com.android.newsettings
fi
test "$(getprop persist.sys.xgimi.themeV2.url)" = "$D/skin.apk"
echo "skin_restore=ok"
