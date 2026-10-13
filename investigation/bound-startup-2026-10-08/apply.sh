#!/system/bin/sh
umask 022
D=/data/local/beam-russifier-boot/releases/1.19.44-3d09369163b99a3e
RUN=$(cat /proc/sys/kernel/random/uuid)
finish() { code=$?; if [ "$(getprop vendor.xgimi.system.debug.cmd)" = "/system/bin/sh $D/apply.sh" ]; then setprop vendor.xgimi.system.debug.cmd ""; setprop vendor.xgimi.system.debugserver ""; fi; printf "%s %s\n" "$RUN" "$code" > "$D/done"; chmod 644 "$D/done"; }
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
zyg=$(pidof zygote)
test -n "$zyg"
test "${zyg#* }" = "$zyg"
ROOTDIR=/data/local/beam-russifier-boot
HC=$ROOTDIR/hashcache
HIST=$ROOTDIR/boot-history.log
touch "$HC" "$ROOTDIR/hashcount"; chmod 600 "$HC" "$ROOTDIR/hashcount"
n=$(cat "$ROOTDIR/hashcount"); n=$((${n:-0}+1)); echo "$n" > "$ROOTDIR/hashcount"
FULL=0; if [ $((n % 20)) = 0 ]; then FULL=1; fi
if [ "$(wc -l < "$HC")" -gt 400 ]; then tail -n 150 "$HC" > "$HC.new" && mv "$HC.new" "$HC"; fi
NL='
'
up() { UPN=$(</proc/uptime); UPN=${UPN%% *}; }
SIGF='%n %s:%Y:%d:%i'
# Lookup tables are shell variables filled by one awk each; names are the key with every non-alphanumeric turned into "_".
mkvars() { awk -v p="$1" '{k=$1; gsub(/[^A-Za-z0-9]/,"_",k); print p k "=\x27" $2 "\x27"}'; }
eval "$(stat -c "$SIGF" "$D/panel.apk" "$D/wirelessscreen-native.apk" "$D/gmservice-native.apk" "$D/systemui-native.apk" "$D/atmosphere-native.apk" "$D/upgrade-native.apk" "$D/shutdown-native.apk" "$D/manager-native.apk" "$D/ota-accessories-native.apk" "$D/skin.apk" /system/priv-app/release_838_newsettings/release_838_newsettings.apk /system/priv-app/SystemUI_release_838/SystemUI_release_838.apk /vendor/priv-app/Atmosphere_release838/Atmosphere_release838.apk /vendor/priv-app/release_838_shutdown/release_838_shutdown.apk /vendor/priv-app/smartaccessories_release_838/smartaccessories_release_838.apk /system/priv-app/XgimiOtaAccessories_release848/XgimiOtaAccessories_release848.apk /vendor/priv-app/xgimiiotserver_release_838/xgimiiotserver_release_838.apk /vendor/priv-app/update/update.apk /vendor/priv-app/wirelessscreen/wirelessscreen.apk /vendor/priv-app/Instruction_release838/Instruction_release838.apk /vendor/priv-app/XgimiManager_release838/XgimiManager_release838.apk /vendor/priv-app/GMService_release838/GMService_release838.apk /vendor/priv-app/AccountCenter_release838/AccountCenter_release838.apk /system/framework/framework-res.apk /vendor/priv-app/GlobalConfig_release838/GlobalConfig_release838.apk /system/priv-app/XRMService/XRMService.apk /system/priv-app/NewSounderMode/NewSounderMode.apk /vendor/app/XgimiFrameworkUi/XgimiFrameworkUi.apk /vendor/priv-app/vcontrol_release838/vcontrol_release838.apk /vendor/priv-app/mediaPlayer_release838/mediaPlayer_release838.apk 2>/dev/null | mkvars SG_)"
eval "$(nsenter -t "$zyg" -m -- stat -c "$SIGF" /system/priv-app/release_838_newsettings/release_838_newsettings.apk /system/priv-app/SystemUI_release_838/SystemUI_release_838.apk /vendor/priv-app/Atmosphere_release838/Atmosphere_release838.apk /vendor/priv-app/release_838_shutdown/release_838_shutdown.apk /vendor/priv-app/smartaccessories_release_838/smartaccessories_release_838.apk /system/priv-app/XgimiOtaAccessories_release848/XgimiOtaAccessories_release848.apk /vendor/priv-app/xgimiiotserver_release_838/xgimiiotserver_release_838.apk /vendor/priv-app/update/update.apk /vendor/priv-app/wirelessscreen/wirelessscreen.apk /vendor/priv-app/Instruction_release838/Instruction_release838.apk /vendor/priv-app/XgimiManager_release838/XgimiManager_release838.apk /vendor/priv-app/GMService_release838/GMService_release838.apk /vendor/priv-app/AccountCenter_release838/AccountCenter_release838.apk /system/framework/framework-res.apk /vendor/priv-app/GlobalConfig_release838/GlobalConfig_release838.apk /system/priv-app/XRMService/XRMService.apk /system/priv-app/NewSounderMode/NewSounderMode.apk /vendor/app/XgimiFrameworkUi/XgimiFrameworkUi.apk /vendor/priv-app/vcontrol_release838/vcontrol_release838.apk /vendor/priv-app/mediaPlayer_release838/mediaPlayer_release838.apk 2>/dev/null | mkvars NS_)"
if [ "$FULL" != 1 ]; then eval "$(awk '{k=$1 "_" $2; gsub(/[^A-Za-z0-9]/,"_",k); print "HC_" k "=\x27" $3 "\x27"}' "$HC")"; fi
get() { eval "echo \"\${$1:-}\""; }
sig() { s=$(get "SG_${1//[!A-Za-z0-9]/_}"); if [ -z "$s" ]; then s=$(stat -c "%s:%Y:%d:%i" "$1" 2>/dev/null || true); fi; echo "$s"; }
nsig() { s=$(get "NS_${1//[!A-Za-z0-9]/_}"); if [ -z "$s" ]; then s=$(nsenter -t "$zyg" -m -- stat -c "%s:%Y:%d:%i" "$1"); fi; echo "$s"; }
cache_get() { x="$1_$2"; get "HC_${x//[!A-Za-z0-9]/_}"; }
cache_put() { printf "%s %s %s\n" "$1" "$2" "$3" >> "$HC"; }
hash_file() { s=$(sig "$1"); h=$(cache_get "$1" "$s"); if [ -z "$h" ]; then h=$(sha256sum "$1" | cut -d " " -f 1); cache_put "$1" "$s" "$h"; fi; echo "$h"; }
check_hash() { actual=$(hash_file "$1"); test "$actual" = "$2"; }
# Fork-free variants (results in REPLY / RH): a command substitution costs a fork (~8 ms here), the overlay loop used ~8 per overlay.
sigv() { eval "REPLY=\${SG_${1//[!A-Za-z0-9]/_}:-}"; if [ -z "$REPLY" ]; then REPLY=$(stat -c "%s:%Y:%d:%i" "$1" 2>/dev/null || true); fi; }
nsigv() { eval "REPLY=\${NS_${1//[!A-Za-z0-9]/_}:-}"; if [ -z "$REPLY" ]; then REPLY=$(nsenter -t "$zyg" -m -- stat -c "%s:%Y:%d:%i" "$1"); fi; }
check_hash2() { sigv "$1"; CK="$1_$REPLY"; eval "CH=\${HC_${CK//[!A-Za-z0-9]/_}:-}"; if [ -z "$CH" ]; then CH=$(sha256sum "$1" | cut -d " " -f 1); cache_put "$1" "$REPLY" "$CH"; fi; test "$CH" = "$2"; }
rt_hash() { nsigv "$1"; CK="ns:$1_$REPLY"; eval "RH=\${HC_${CK//[!A-Za-z0-9]/_}:-}"; if [ -z "$RH" ]; then RH=$(nsenter -t "$zyg" -m -- sha256sum "$1" | cut -d " " -f 1); cache_put "ns:$1" "$REPLY" "$RH"; fi; }
runtime_hash() { s=$(nsig "$1"); h=$(cache_get "ns:$1" "$s"); if [ -z "$h" ]; then h=$(nsenter -t "$zyg" -m -- sha256sum "$1" | cut -d " " -f 1); cache_put "ns:$1" "$s" "$h"; fi; echo "$h"; }
HC_BEFORE=$(wc -l < "$HC")
up; S_START=$UPN
check_hash2 "$D/panel.apk" e01f5d788bf7b8e7d15313ef6906e0458217babbe86d5a38702ae299af92ff78
check_hash2 "$D/wirelessscreen-native.apk" ad620e26c5cc3d6aec7be126b8923b902af7d431a669806a1acd9c76a9f0d19c
check_hash2 "$D/gmservice-native.apk" e88a388cc83cac551ef45b70603208bca4b823b56cd6a65266ae9d358db02f62
check_hash2 "$D/systemui-native.apk" 55bb96ff9e887b4d5de12c0034e340154da8834f66683a350e595b54e08d4d3b
check_hash2 "$D/atmosphere-native.apk" 94d20c7261ebe678576df09254591c1dc3781909e49e3a8330f48065160bc50f
check_hash2 "$D/upgrade-native.apk" aad7684e0f3ddc6dbc92f6e7d6a25596d6509bc2e56f9cda6f9be63206d86653
check_hash2 "$D/shutdown-native.apk" 68f278b2ed83f078119fbf62e2b0fc8ea8a156d848b51497a3b526da9af245a4
check_hash2 "$D/manager-native.apk" e0ea357228d4d908fd19dcbd1d5bcdeadfd34db9c63d30b9fd2d2bc4f56a8da9
check_hash2 "$D/ota-accessories-native.apk" 22f3d1d83c96b41514082480e8019a9f90712b026ca69a4b82dfbbe1651ee993
check_hash2 "$D/skin.apk" 102a848f421e2954f6feb98e4fe6ad3ed14c6a55464579c55a65778b5e56c2a1
rt_hash /system/priv-app/release_838_newsettings/release_838_newsettings.apk; NATIVE_0=$RH
case "$NATIVE_0" in 15a871680fef952e7f29365643e18e6cfab25e6cd523fa8aadc52c6eeffa84a1|e01f5d788bf7b8e7d15313ef6906e0458217babbe86d5a38702ae299af92ff78|3c60e71c641cd319ae7353c8d1565c4282c59996dd362a58e83d833f4c36c859|6b3b6ec5c7ef8c86ed1c04d1436b28242a2a50839f6f5c6166b2fe48de4fa11f|0aeaa5c1d77f29d5b818abf047322d669f96c2400684dfad9147580356f7013d|44e06a37ddc4b6680c2a39141550c29cf7d02d2365b660d72409bba9505b2683|5166aab4c90b061d038c3ee18832e161421dccdc234d100d428c3d9d2d1f70cd|25bfc0f5b296bf9d487fc3da61b62e2c423df6016f320385a0a213369f5714ab|54cb31fae61e190777ab000c29e26353447b55d12150d4df2356dd77ed6c3969|8f634046e97ced0073b85826c08946535bfcb87800d95e20b8ba2a48acb7bd89|a3973200bbcacb7a5523098df25afc4f04e93466d9bbf761a6b431a7f53774fb|a901619a3559e19bf62764b89816eb0d026db6fbc4cde453b54cb0cf52a97e2f|98772d83d4724c3a6a9b45dcb4381e87b0a86ba6bb684d40d4117e84e2c72b25|96b545f76c6252357e4b12ce118c282b33daa7650d3158e1122245f07bacb463|75e2e34da642173b07a86845246cabf10b77f2eb688e623260e1783ce70e172d|79a62b05926a8c15ad6c10757bb7335cabee7107b8889ae89d4960220a844b45|4f05114a1cef4326cc92cb8f063209b4b9efc206aaeb037e9a5d809b7d568a3d|ee3c31947c85a2ea9dbb98a9b33329355c6c3725f04aef2a3f17f36b7bd96b9b) : ;; *) echo 'Unexpected APK: com.android.newsettings'; exit 12 ;; esac
rt_hash /vendor/priv-app/wirelessscreen/wirelessscreen.apk; NATIVE_1=$RH
case "$NATIVE_1" in 061191874aa6aca4e747b27b25a5c3bb8937451572fb36d9f8e76c82ec63785a|ad620e26c5cc3d6aec7be126b8923b902af7d431a669806a1acd9c76a9f0d19c|890a6ce5ba06216650434c8330acae014d9e87544a6e136732c4010f05d7c551) : ;; *) echo 'Unexpected APK: com.xgimi.wirelessscreen'; exit 12 ;; esac
rt_hash /vendor/priv-app/GMService_release838/GMService_release838.apk; NATIVE_2=$RH
case "$NATIVE_2" in 5d3d6444bcf8ffb4717db81a3f36b44fdf655df045d8cb921ee3ffbd4753f797|e88a388cc83cac551ef45b70603208bca4b823b56cd6a65266ae9d358db02f62|eeb9b3afbf8e091ffe5baa63a371e25970d9501dd13b78ab967fdeb9f56c9479) : ;; *) echo 'Unexpected APK: com.xgimi.gmservice'; exit 12 ;; esac
rt_hash /system/priv-app/SystemUI_release_838/SystemUI_release_838.apk; NATIVE_3=$RH
case "$NATIVE_3" in 740321166c5e3703e52dd2a1ea55de38a146bc6ea3624f2dd221f0ceacc14308|55bb96ff9e887b4d5de12c0034e340154da8834f66683a350e595b54e08d4d3b|86e533831d9db7d1a30f06f563bbd0fc616e640a5b4159e302c9f72b5aff6296|9e938168a38a47191e74097317c5536c631dfbbe690b689c13cf3ce270af3c89|54c6c67982ac57b97a820764fcda750e18f6e66cb74a0d820ffdf1095334b9ba) : ;; *) echo 'Unexpected APK: com.xgimi.systemui'; exit 12 ;; esac
rt_hash /vendor/priv-app/Atmosphere_release838/Atmosphere_release838.apk; NATIVE_4=$RH
case "$NATIVE_4" in a0638a3db737357c619b60b43175b4c4bf31d614b172c548a82d5d855ff2d9eb|94d20c7261ebe678576df09254591c1dc3781909e49e3a8330f48065160bc50f|6759c9a467309e5563bdbaf725b2c1b6bc201a88d2691082d3a605c4f5364f20) : ;; *) echo 'Unexpected APK: com.xgimi.atmosphere'; exit 12 ;; esac
rt_hash /vendor/priv-app/update/update.apk; NATIVE_5=$RH
case "$NATIVE_5" in 9e42ca671911ec1db739e4c3c16179b66583b09cdaa0e6d35bc660393a872a6d|aad7684e0f3ddc6dbc92f6e7d6a25596d6509bc2e56f9cda6f9be63206d86653) : ;; *) echo 'Unexpected APK: com.xgimi.upgrade'; exit 12 ;; esac
rt_hash /vendor/priv-app/release_838_shutdown/release_838_shutdown.apk; NATIVE_6=$RH
case "$NATIVE_6" in 6b2e3298157de17091d6fd69093181733b6038aa9c107571f53439db98705d23|68f278b2ed83f078119fbf62e2b0fc8ea8a156d848b51497a3b526da9af245a4) : ;; *) echo 'Unexpected APK: com.xgimi.shutdown'; exit 12 ;; esac
rt_hash /vendor/priv-app/XgimiManager_release838/XgimiManager_release838.apk; NATIVE_7=$RH
case "$NATIVE_7" in 2401bfa54ca98499a706d9f6f9c476971ba06a648d78865468b496e9b06bd9dd|e0ea357228d4d908fd19dcbd1d5bcdeadfd34db9c63d30b9fd2d2bc4f56a8da9) : ;; *) echo 'Unexpected APK: com.xgimi.manager'; exit 12 ;; esac
rt_hash /system/priv-app/XgimiOtaAccessories_release848/XgimiOtaAccessories_release848.apk; NATIVE_8=$RH
case "$NATIVE_8" in 62ee3ac5cd4e70f2b98d7cf30d9c5a4996588024dad0faf99e47ed68fc57f88d|22f3d1d83c96b41514082480e8019a9f90712b026ca69a4b82dfbbe1651ee993) : ;; *) echo 'Unexpected APK: com.xgimi.ota.accessories'; exit 12 ;; esac
up; S_NV=$UPN; echo "native_validated_uptime=$S_NV"
OLD_SKIN=$(getprop persist.sys.xgimi.themeV2.url)
setprop persist.sys.xgimi.themeV2.url "$D/skin.apk"
PSN=$(ps -A -o NAME)
sigv "$D/panel.apk"; OURS_0=${REPLY#*:*:}
nsigv /system/priv-app/release_838_newsettings/release_838_newsettings.apk; if [ "${REPLY#*:*:}" != "$OURS_0" ]; then
  nsenter -t "$zyg" -m -- mount -o bind "$D/panel.apk" /system/priv-app/release_838_newsettings/release_838_newsettings.apk
fi
needs_restart=0
if [ "$NATIVE_0" != e01f5d788bf7b8e7d15313ef6906e0458217babbe86d5a38702ae299af92ff78 ]; then needs_restart=1; fi
if [ "$OLD_SKIN" != "$D/skin.apk" ]; then needs_restart=1; fi
for p in $(pidof com.android.newsettings || true); do
  if [ "$(nsenter -t "$p" -m -- stat -c %d:%i /system/priv-app/release_838_newsettings/release_838_newsettings.apk)" != "$OURS_0" ]; then needs_restart=1; fi
done
if [ "$needs_restart" = 1 ]; then
  case "$NL$PSN$NL" in *"${NL}com.android.newsettings${NL}"*|*"${NL}com.android.newsettings:"*) am force-stop com.android.newsettings & ;; esac
fi
up; echo "t_native_0=$UPN"
sigv "$D/wirelessscreen-native.apk"; OURS_1=${REPLY#*:*:}
nsigv /vendor/priv-app/wirelessscreen/wirelessscreen.apk; if [ "${REPLY#*:*:}" != "$OURS_1" ]; then
  nsenter -t "$zyg" -m -- mount -o bind "$D/wirelessscreen-native.apk" /vendor/priv-app/wirelessscreen/wirelessscreen.apk
fi
needs_restart=0
if [ "$NATIVE_1" != ad620e26c5cc3d6aec7be126b8923b902af7d431a669806a1acd9c76a9f0d19c ]; then needs_restart=1; fi
for p in $(pidof com.xgimi.wirelessscreen || true); do
  if [ "$(nsenter -t "$p" -m -- stat -c %d:%i /vendor/priv-app/wirelessscreen/wirelessscreen.apk)" != "$OURS_1" ]; then needs_restart=1; fi
done
if [ "$needs_restart" = 1 ]; then
  case "$NL$PSN$NL" in *"${NL}com.xgimi.wirelessscreen${NL}"*|*"${NL}com.xgimi.wirelessscreen:"*) am force-stop com.xgimi.wirelessscreen & ;; esac
fi
up; echo "t_native_1=$UPN"
sigv "$D/gmservice-native.apk"; OURS_2=${REPLY#*:*:}
nsigv /vendor/priv-app/GMService_release838/GMService_release838.apk; if [ "${REPLY#*:*:}" != "$OURS_2" ]; then
  nsenter -t "$zyg" -m -- mount -o bind "$D/gmservice-native.apk" /vendor/priv-app/GMService_release838/GMService_release838.apk
fi
needs_restart=0
if [ "$NATIVE_2" != e88a388cc83cac551ef45b70603208bca4b823b56cd6a65266ae9d358db02f62 ]; then needs_restart=1; fi
for p in $(pidof com.xgimi.gmservice || true); do
  if [ "$(nsenter -t "$p" -m -- stat -c %d:%i /vendor/priv-app/GMService_release838/GMService_release838.apk)" != "$OURS_2" ]; then needs_restart=1; fi
done
if [ "$needs_restart" = 1 ]; then
  case "$NL$PSN$NL" in *"${NL}com.xgimi.gmservice${NL}"*|*"${NL}com.xgimi.gmservice:"*) am force-stop com.xgimi.gmservice & ;; esac
fi
up; echo "t_native_2=$UPN"
sigv "$D/systemui-native.apk"; OURS_3=${REPLY#*:*:}
nsigv /system/priv-app/SystemUI_release_838/SystemUI_release_838.apk; if [ "${REPLY#*:*:}" != "$OURS_3" ]; then
  nsenter -t "$zyg" -m -- mount -o bind "$D/systemui-native.apk" /system/priv-app/SystemUI_release_838/SystemUI_release_838.apk
fi
needs_restart=0
if [ "$NATIVE_3" != 55bb96ff9e887b4d5de12c0034e340154da8834f66683a350e595b54e08d4d3b ]; then needs_restart=1; fi
for p in $(pidof com.xgimi.systemui || true); do
  if [ "$(nsenter -t "$p" -m -- stat -c %d:%i /system/priv-app/SystemUI_release_838/SystemUI_release_838.apk)" != "$OURS_3" ]; then needs_restart=1; fi
done
if [ "$needs_restart" = 1 ]; then
  case "$NL$PSN$NL" in *"${NL}com.xgimi.systemui${NL}"*|*"${NL}com.xgimi.systemui:"*) p=$(pidof com.xgimi.systemui); if [ -n "$p" ]; then test "${p#* }" = "$p"; kill -9 "$p"; fi ;; esac
fi
up; echo "t_native_3=$UPN"
sigv "$D/atmosphere-native.apk"; OURS_4=${REPLY#*:*:}
nsigv /vendor/priv-app/Atmosphere_release838/Atmosphere_release838.apk; if [ "${REPLY#*:*:}" != "$OURS_4" ]; then
  nsenter -t "$zyg" -m -- mount -o bind "$D/atmosphere-native.apk" /vendor/priv-app/Atmosphere_release838/Atmosphere_release838.apk
fi
needs_restart=0
if [ "$NATIVE_4" != 94d20c7261ebe678576df09254591c1dc3781909e49e3a8330f48065160bc50f ]; then needs_restart=1; fi
for p in $(pidof com.xgimi.atmosphere || true); do
  if [ "$(nsenter -t "$p" -m -- stat -c %d:%i /vendor/priv-app/Atmosphere_release838/Atmosphere_release838.apk)" != "$OURS_4" ]; then needs_restart=1; fi
done
if [ "$needs_restart" = 1 ]; then
  case "$NL$PSN$NL" in *"${NL}com.xgimi.atmosphere${NL}"*|*"${NL}com.xgimi.atmosphere:"*) am force-stop com.xgimi.atmosphere & ;; esac
fi
up; echo "t_native_4=$UPN"
sigv "$D/upgrade-native.apk"; OURS_5=${REPLY#*:*:}
nsigv /vendor/priv-app/update/update.apk; if [ "${REPLY#*:*:}" != "$OURS_5" ]; then
  nsenter -t "$zyg" -m -- mount -o bind "$D/upgrade-native.apk" /vendor/priv-app/update/update.apk
fi
needs_restart=0
if [ "$NATIVE_5" != aad7684e0f3ddc6dbc92f6e7d6a25596d6509bc2e56f9cda6f9be63206d86653 ]; then needs_restart=1; fi
for p in $(pidof com.xgimi.upgrade || true); do
  if [ "$(nsenter -t "$p" -m -- stat -c %d:%i /vendor/priv-app/update/update.apk)" != "$OURS_5" ]; then needs_restart=1; fi
done
if [ "$needs_restart" = 1 ]; then
  case "$NL$PSN$NL" in *"${NL}com.xgimi.upgrade${NL}"*|*"${NL}com.xgimi.upgrade:"*) am force-stop com.xgimi.upgrade & ;; esac
fi
up; echo "t_native_5=$UPN"
sigv "$D/shutdown-native.apk"; OURS_6=${REPLY#*:*:}
nsigv /vendor/priv-app/release_838_shutdown/release_838_shutdown.apk; if [ "${REPLY#*:*:}" != "$OURS_6" ]; then
  nsenter -t "$zyg" -m -- mount -o bind "$D/shutdown-native.apk" /vendor/priv-app/release_838_shutdown/release_838_shutdown.apk
fi
needs_restart=0
if [ "$NATIVE_6" != 68f278b2ed83f078119fbf62e2b0fc8ea8a156d848b51497a3b526da9af245a4 ]; then needs_restart=1; fi
for p in $(pidof com.xgimi.shutdown || true); do
  if [ "$(nsenter -t "$p" -m -- stat -c %d:%i /vendor/priv-app/release_838_shutdown/release_838_shutdown.apk)" != "$OURS_6" ]; then needs_restart=1; fi
done
if [ "$needs_restart" = 1 ]; then
  case "$NL$PSN$NL" in *"${NL}com.xgimi.shutdown${NL}"*|*"${NL}com.xgimi.shutdown:"*) am force-stop com.xgimi.shutdown & ;; esac
fi
up; echo "t_native_6=$UPN"
sigv "$D/manager-native.apk"; OURS_7=${REPLY#*:*:}
nsigv /vendor/priv-app/XgimiManager_release838/XgimiManager_release838.apk; if [ "${REPLY#*:*:}" != "$OURS_7" ]; then
  nsenter -t "$zyg" -m -- mount -o bind "$D/manager-native.apk" /vendor/priv-app/XgimiManager_release838/XgimiManager_release838.apk
fi
needs_restart=0
if [ "$NATIVE_7" != e0ea357228d4d908fd19dcbd1d5bcdeadfd34db9c63d30b9fd2d2bc4f56a8da9 ]; then needs_restart=1; fi
for p in $(pidof com.xgimi.manager || true); do
  if [ "$(nsenter -t "$p" -m -- stat -c %d:%i /vendor/priv-app/XgimiManager_release838/XgimiManager_release838.apk)" != "$OURS_7" ]; then needs_restart=1; fi
done
if [ "$needs_restart" = 1 ]; then
  case "$NL$PSN$NL" in *"${NL}com.xgimi.manager${NL}"*|*"${NL}com.xgimi.manager:"*) am force-stop com.xgimi.manager & ;; esac
fi
up; echo "t_native_7=$UPN"
sigv "$D/ota-accessories-native.apk"; OURS_8=${REPLY#*:*:}
nsigv /system/priv-app/XgimiOtaAccessories_release848/XgimiOtaAccessories_release848.apk; if [ "${REPLY#*:*:}" != "$OURS_8" ]; then
  nsenter -t "$zyg" -m -- mount -o bind "$D/ota-accessories-native.apk" /system/priv-app/XgimiOtaAccessories_release848/XgimiOtaAccessories_release848.apk
fi
needs_restart=0
if [ "$NATIVE_8" != 22f3d1d83c96b41514082480e8019a9f90712b026ca69a4b82dfbbe1651ee993 ]; then needs_restart=1; fi
for p in $(pidof com.xgimi.ota.accessories || true); do
  if [ "$(nsenter -t "$p" -m -- stat -c %d:%i /system/priv-app/XgimiOtaAccessories_release848/XgimiOtaAccessories_release848.apk)" != "$OURS_8" ]; then needs_restart=1; fi
done
if [ "$needs_restart" = 1 ]; then
  case "$NL$PSN$NL" in *"${NL}com.xgimi.ota.accessories${NL}"*|*"${NL}com.xgimi.ota.accessories:"*) am force-stop com.xgimi.ota.accessories & ;; esac
fi
up; echo "t_native_8=$UPN"
wait
NSV=$(nsenter -t "$zyg" -m -- stat -c "%n %d:%i" /system/priv-app/release_838_newsettings/release_838_newsettings.apk /vendor/priv-app/wirelessscreen/wirelessscreen.apk /vendor/priv-app/GMService_release838/GMService_release838.apk /system/priv-app/SystemUI_release_838/SystemUI_release_838.apk /vendor/priv-app/Atmosphere_release838/Atmosphere_release838.apk /vendor/priv-app/update/update.apk /vendor/priv-app/release_838_shutdown/release_838_shutdown.apk /vendor/priv-app/XgimiManager_release838/XgimiManager_release838.apk /system/priv-app/XgimiOtaAccessories_release848/XgimiOtaAccessories_release848.apk)
eval "$(echo "$NSV" | mkvars NSV_)"
test "${NSV__system_priv_app_release_838_newsettings_release_838_newsettings_apk:-}" = "$OURS_0"
test "${NSV__vendor_priv_app_wirelessscreen_wirelessscreen_apk:-}" = "$OURS_1"
test "${NSV__vendor_priv_app_GMService_release838_GMService_release838_apk:-}" = "$OURS_2"
test "${NSV__system_priv_app_SystemUI_release_838_SystemUI_release_838_apk:-}" = "$OURS_3"
test "${NSV__vendor_priv_app_Atmosphere_release838_Atmosphere_release838_apk:-}" = "$OURS_4"
test "${NSV__vendor_priv_app_update_update_apk:-}" = "$OURS_5"
test "${NSV__vendor_priv_app_release_838_shutdown_release_838_shutdown_apk:-}" = "$OURS_6"
test "${NSV__vendor_priv_app_XgimiManager_release838_XgimiManager_release838_apk:-}" = "$OURS_7"
test "${NSV__system_priv_app_XgimiOtaAccessories_release848_XgimiOtaAccessories_release848_apk:-}" = "$OURS_8"
up; S_NR=$UPN; echo "native_ready_uptime=$S_NR boot_completed=$(getprop sys.boot_completed)"
for p in $(pidof com.android.newsettings || true); do
  test "$(nsenter -t "$p" -m -- stat -c %d:%i /system/priv-app/release_838_newsettings/release_838_newsettings.apk)" = "$OURS_0"
done
up; echo "t_post_panel.apk=$UPN"
for p in $(pidof com.xgimi.wirelessscreen || true); do
  test "$(nsenter -t "$p" -m -- stat -c %d:%i /vendor/priv-app/wirelessscreen/wirelessscreen.apk)" = "$OURS_1"
done
up; echo "t_post_wirelessscreen=$UPN"
for p in $(pidof com.xgimi.gmservice || true); do
  test "$(nsenter -t "$p" -m -- stat -c %d:%i /vendor/priv-app/GMService_release838/GMService_release838.apk)" = "$OURS_2"
done
up; echo "t_post_gmservice=$UPN"
n=0; while [ -z "$(pidof com.xgimi.systemui)" ] && [ "$n" -lt 20 ]; do sleep 1; n=$((n+1)); done
test -n "$(pidof com.xgimi.systemui)"
for p in $(pidof com.xgimi.systemui || true); do
  test "$(nsenter -t "$p" -m -- stat -c %d:%i /system/priv-app/SystemUI_release_838/SystemUI_release_838.apk)" = "$OURS_3"
done
up; echo "t_post_systemui=$UPN"
for p in $(pidof com.xgimi.atmosphere || true); do
  test "$(nsenter -t "$p" -m -- stat -c %d:%i /vendor/priv-app/Atmosphere_release838/Atmosphere_release838.apk)" = "$OURS_4"
done
up; echo "t_post_atmosphere=$UPN"
for p in $(pidof com.xgimi.upgrade || true); do
  test "$(nsenter -t "$p" -m -- stat -c %d:%i /vendor/priv-app/update/update.apk)" = "$OURS_5"
done
up; echo "t_post_upgrade=$UPN"
for p in $(pidof com.xgimi.shutdown || true); do
  test "$(nsenter -t "$p" -m -- stat -c %d:%i /vendor/priv-app/release_838_shutdown/release_838_shutdown.apk)" = "$OURS_6"
done
up; echo "t_post_shutdown=$UPN"
for p in $(pidof com.xgimi.manager || true); do
  test "$(nsenter -t "$p" -m -- stat -c %d:%i /vendor/priv-app/XgimiManager_release838/XgimiManager_release838.apk)" = "$OURS_7"
done
up; echo "t_post_manager=$UPN"
for p in $(pidof com.xgimi.ota.accessories || true); do
  test "$(nsenter -t "$p" -m -- stat -c %d:%i /system/priv-app/XgimiOtaAccessories_release848/XgimiOtaAccessories_release848.apk)" = "$OURS_8"
done
up; echo "t_post_ota=$UPN"
up; echo "t_orig_start=$UPN"
rt_hash /vendor/priv-app/smartaccessories_release_838/smartaccessories_release_838.apk; test "$RH" = 7390ca0e4d474e9ef79ba31adf53229135acdfed8fd0a501e893d101c15c26bc
rt_hash /vendor/priv-app/xgimiiotserver_release_838/xgimiiotserver_release_838.apk; test "$RH" = 871d78c86a4d72445bdace1934e8375e3a97390c50ba25815db4b35aaafe2d03
rt_hash /vendor/priv-app/Instruction_release838/Instruction_release838.apk; test "$RH" = ab452a3f89151e57afd130376f1242813f50476e6a70a1470921a0ec00e8f821
rt_hash /vendor/priv-app/AccountCenter_release838/AccountCenter_release838.apk; test "$RH" = e07dc54411904c9db7a21f90ac96b665cc4c1b8c6b8d43721e7b5ee89637bc19
rt_hash /system/framework/framework-res.apk; test "$RH" = 82b06bd7cba9faf3acbdbaf409b7b514e3559209acc18cd99026844ca86f5f66
rt_hash /vendor/priv-app/GlobalConfig_release838/GlobalConfig_release838.apk; test "$RH" = 1c83c3c170d5899aab8a2c4cb10959b649c202dc00e328464a219690bdd9aede
rt_hash /system/priv-app/XRMService/XRMService.apk; test "$RH" = 40274f5049bd450047ac43cb049b5a120dd2c145964f7722f7cb5c70e07c6048
rt_hash /system/priv-app/NewSounderMode/NewSounderMode.apk; test "$RH" = 4634cf008a1926de7dc231717a988635a4f568f0599170ec715372ae4f6edc33
rt_hash /vendor/app/XgimiFrameworkUi/XgimiFrameworkUi.apk; test "$RH" = 9869ccf062ded8c37e399618ad909f48317a2df079dfa88daab25ec9bbaa978a
rt_hash /vendor/priv-app/vcontrol_release838/vcontrol_release838.apk; test "$RH" = 3f588ddc4dc362be833f9d5960d69a5864d9c77bedcfd87cda30af7ca2f2abe7
rt_hash /vendor/priv-app/mediaPlayer_release838/mediaPlayer_release838.apk; test "$RH" = 629387b9eec7f0bd6d200f59fc0e89584d4dbf1e96b7aea75dd73374efc603fd
up; echo "t_orig_done=$UPN"
ov_index() {
  for d in /data/app/*/com.beam.translation.*/; do
    f=${d}base.apk; [ -f "$f" ] || continue
    n=${d%/}; n=${n##*/}; n=${n%%-*}
    eval "OV_${n//[!A-Za-z0-9]/_}='$f'"
  done
}
ov_index_pm() {
  PACKAGES=$(cmd package list packages -f com.beam.translation)
  eval "$(echo "$PACKAGES" | awk '{sub(/^package:/,""); n=split($0,a,"="); p=substr($0,1,length($0)-length(a[n])-1); k=a[n]; gsub(/[^A-Za-z0-9]/,"_",k); print "OV_" k "=\x27" p "\x27"}')"
}
ov_load() {
  OVFILES=""
  for pk in com.beam.translation.systemui com.beam.translation.settings com.beam.translation.ambient com.beam.translation.atmosphere com.beam.translation.shutdown com.beam.translation.smartaccessories com.beam.translation.otaaccessories com.beam.translation.xgimiiotserver com.beam.translation.upgrade com.beam.translation.wirelessscreen com.beam.translation.instruction30 com.beam.translation.manager com.beam.translation.gmservice com.beam.translation.user com.beam.translation.frameworkpower com.beam.translation.config com.beam.translation.xrmservice com.beam.translation.soundermodeservice com.beam.translation.xgimiframeworkui com.beam.translation.vcontrol com.beam.translation.gimiplayer; do eval "p=\${OV_${pk//[!A-Za-z0-9]/_}:-}"; k=${p#/}; OVFILES="$OVFILES $p /data/resource-cache/${k//\//@}@idmap"; done
  eval "$(stat -c "$SIGF" $OVFILES 2>/dev/null | mkvars SG_)"
}
ov_check() {
  eval "OVERLAY=\${OV_com_beam_translation_systemui:-}"; test -f "$OVERLAY" || return 1; check_hash2 "$OVERLAY" 045c0603709f045fa92e61a454fc5fd3bfe207030d9e01bbaa57a48914b2c8c4 || return 1
  eval "OVERLAY=\${OV_com_beam_translation_settings:-}"; test -f "$OVERLAY" || return 1; check_hash2 "$OVERLAY" 0f0c4800ca377d13b3720e426c8b6684be441af038bffdd4720dd32f0951c995 || return 1
  eval "OVERLAY=\${OV_com_beam_translation_ambient:-}"; test -f "$OVERLAY" || return 1; check_hash2 "$OVERLAY" 7d183367a17f7a62c02399edfd649a3cc1bdb53f18d703b1b8a04a2bf60fc389 || return 1
  eval "OVERLAY=\${OV_com_beam_translation_atmosphere:-}"; test -f "$OVERLAY" || return 1; check_hash2 "$OVERLAY" 5cf66e149ece15810a170e1120103bc63a86b28949108788e88cfdf2145c837e || return 1
  eval "OVERLAY=\${OV_com_beam_translation_shutdown:-}"; test -f "$OVERLAY" || return 1; check_hash2 "$OVERLAY" 4f4bf54166061df424d15fdcdd8890475593527c6eebb9b03697a283bde1a17b || return 1
  eval "OVERLAY=\${OV_com_beam_translation_smartaccessories:-}"; test -f "$OVERLAY" || return 1; check_hash2 "$OVERLAY" 6fdfc7ae1e35610808e932cb7d3813cf412a5fa69f9f62376df2398f174d23db || return 1
  eval "OVERLAY=\${OV_com_beam_translation_otaaccessories:-}"; test -f "$OVERLAY" || return 1; check_hash2 "$OVERLAY" 084cdca1be139957ec18d12cd9a02286e8713a29e7474049f90342719cb9537a || return 1
  eval "OVERLAY=\${OV_com_beam_translation_xgimiiotserver:-}"; test -f "$OVERLAY" || return 1; check_hash2 "$OVERLAY" 634907a8199b652e6d0e7848d2a1bb4f310c0083e960800a860bc635af23a9d4 || return 1
  eval "OVERLAY=\${OV_com_beam_translation_upgrade:-}"; test -f "$OVERLAY" || return 1; check_hash2 "$OVERLAY" 0071699690cecfab24562daca7f372ffe11526fb2b274fdb70c8044c2ed598b0 || return 1
  eval "OVERLAY=\${OV_com_beam_translation_wirelessscreen:-}"; test -f "$OVERLAY" || return 1; check_hash2 "$OVERLAY" c02608d3d66c115f3c3624be9a78b4e580780c2b4e720e2c989a50116ab35f0f || return 1
  eval "OVERLAY=\${OV_com_beam_translation_instruction30:-}"; test -f "$OVERLAY" || return 1; check_hash2 "$OVERLAY" f46430e8fc4df6aa71c926d78eb7af93c42e13ed65b8daae3728596d1dd1a043 || return 1
  eval "OVERLAY=\${OV_com_beam_translation_manager:-}"; test -f "$OVERLAY" || return 1; check_hash2 "$OVERLAY" ed34c023c4cd6d5c08495a2d54d451dad96f495afc661be34af1b512732a1fdf || return 1
  eval "OVERLAY=\${OV_com_beam_translation_gmservice:-}"; test -f "$OVERLAY" || return 1; check_hash2 "$OVERLAY" 9ac18f1cdbe76d493c959807840238960ac43217021e746185a84cf56a1e3bac || return 1
  eval "OVERLAY=\${OV_com_beam_translation_user:-}"; test -f "$OVERLAY" || return 1; check_hash2 "$OVERLAY" a3fd2614b81dfffa07b287684ab514105db68273407c6b22309183470ab7ec13 || return 1
  eval "OVERLAY=\${OV_com_beam_translation_frameworkpower:-}"; test -f "$OVERLAY" || return 1; check_hash2 "$OVERLAY" dc9ea97291b2089bfaae61a3b1bfe3f5f65685083e0052d23884018e35890fdf || return 1
  eval "OVERLAY=\${OV_com_beam_translation_config:-}"; test -f "$OVERLAY" || return 1; check_hash2 "$OVERLAY" 478729c7ee6330ad4335feb07a0b13b449e53815fd657162ad2ff98dec40424a || return 1
  eval "OVERLAY=\${OV_com_beam_translation_xrmservice:-}"; test -f "$OVERLAY" || return 1; check_hash2 "$OVERLAY" 3f8251fcf28e221bb65aab2175d7a1c7ef7ab7740e228f3510806f7ff612639a || return 1
  eval "OVERLAY=\${OV_com_beam_translation_soundermodeservice:-}"; test -f "$OVERLAY" || return 1; check_hash2 "$OVERLAY" 40f7bba82933c406263b7f2ebf4f7b13f98787d63197bb03848e642f7ee4219b || return 1
  eval "OVERLAY=\${OV_com_beam_translation_xgimiframeworkui:-}"; test -f "$OVERLAY" || return 1; check_hash2 "$OVERLAY" ad1e9a23f9b2c59558c8f6f8c39a34ec8ab6fc557f63d2c2998113a80e928db0 || return 1
  eval "OVERLAY=\${OV_com_beam_translation_vcontrol:-}"; test -f "$OVERLAY" || return 1; check_hash2 "$OVERLAY" 93e1bbe63cf7bcbff2611642a377c471dd4dbeafeed9422bfdae1158847469c8 || return 1
  eval "OVERLAY=\${OV_com_beam_translation_gimiplayer:-}"; test -f "$OVERLAY" || return 1; check_hash2 "$OVERLAY" 659968e57b1e06004afb2085afc4b553acc636bb60c12026905fe750e6d68d26 || return 1
}
ov_cache_load() { if [ -f "$OVC" ]; then eval "$(awk '{k=$1; gsub(/[^A-Za-z0-9]/,"_",k); print "OV_" k "=\x27" $2 "\x27"}' "$OVC")"; fi; }
ov_cache_save() { for pk in com.beam.translation.systemui com.beam.translation.settings com.beam.translation.ambient com.beam.translation.atmosphere com.beam.translation.shutdown com.beam.translation.smartaccessories com.beam.translation.otaaccessories com.beam.translation.xgimiiotserver com.beam.translation.upgrade com.beam.translation.wirelessscreen com.beam.translation.instruction30 com.beam.translation.manager com.beam.translation.gmservice com.beam.translation.user com.beam.translation.frameworkpower com.beam.translation.config com.beam.translation.xrmservice com.beam.translation.soundermodeservice com.beam.translation.xgimiframeworkui com.beam.translation.vcontrol com.beam.translation.gimiplayer; do eval "p=\${OV_${pk//[!A-Za-z0-9]/_}:-}"; echo "$pk $p"; done > "$OVC.new" && mv "$OVC.new" "$OVC"; chmod 600 "$OVC"; }
OVC=$ROOTDIR/ovpaths
OV_SOURCE=cache
ov_cache_load; ov_load; up; echo "t_ovload=$UPN"
if ! ov_check; then
  OV_SOURCE=glob; ov_index; ov_load
  if ! ov_check; then OV_SOURCE=pm; ov_index_pm; ov_load; ov_check; fi
  ov_cache_save
fi
echo "ov_source=$OV_SOURCE"
up; echo "t_pkgs=$UPN"
up; S_OV=$UPN; echo "overlays_validated_uptime=$S_OV"
ENABLED=$(cmd overlay list | awk '$1=="[x]"{print $2}')
up; echo "t_enabled=$UPN"
IDMAP_DONE=0; IDMAP_SKIPPED=0
eval "OVERLAY=\${OV_com_beam_translation_systemui}"
k=${OVERLAY#/}; CACHE=/data/resource-cache/${k//\//@}@idmap
sigv "$OVERLAY"; OSIG=$REPLY; sigv /system/priv-app/SystemUI_release_838/SystemUI_release_838.apk; OSIG="$OSIG|$REPLY"
CK="idmap:${CACHE}_$OSIG"; eval "want=\${HC_${CK//[!A-Za-z0-9]/_}:-}"
sigv "$CACHE"; have=$REPLY
case "$NL$ENABLED$NL" in *"${NL}com.beam.translation.systemui${NL}"*) EN=1;; *) EN=0;; esac
if [ -n "$want" ] && [ "$want" = "$have" ] && [ "$EN" = 1 ]; then IDMAP_SKIPPED=$((IDMAP_SKIPPED+1)); else
  idmap2 create --target-apk-path /system/priv-app/SystemUI_release_838/SystemUI_release_838.apk --overlay-apk-path "$OVERLAY" --idmap-path "$CACHE" --policy public --ignore-overlayable
  chown system:system "$CACHE"
  chmod 644 "$CACHE"
  cache_put "idmap:$CACHE" "$OSIG" "$(stat -c %s:%Y:%d:%i "$CACHE")"
  cmd overlay enable --user 0 com.beam.translation.systemui
  IDMAP_DONE=$((IDMAP_DONE+1))
fi
eval "OVERLAY=\${OV_com_beam_translation_settings}"
k=${OVERLAY#/}; CACHE=/data/resource-cache/${k//\//@}@idmap
sigv "$OVERLAY"; OSIG=$REPLY; sigv /system/priv-app/release_838_newsettings/release_838_newsettings.apk; OSIG="$OSIG|$REPLY"
CK="idmap:${CACHE}_$OSIG"; eval "want=\${HC_${CK//[!A-Za-z0-9]/_}:-}"
sigv "$CACHE"; have=$REPLY
case "$NL$ENABLED$NL" in *"${NL}com.beam.translation.settings${NL}"*) EN=1;; *) EN=0;; esac
if [ -n "$want" ] && [ "$want" = "$have" ] && [ "$EN" = 1 ]; then IDMAP_SKIPPED=$((IDMAP_SKIPPED+1)); else
  idmap2 create --target-apk-path /system/priv-app/release_838_newsettings/release_838_newsettings.apk --overlay-apk-path "$OVERLAY" --idmap-path "$CACHE" --policy public --ignore-overlayable
  chown system:system "$CACHE"
  chmod 644 "$CACHE"
  cache_put "idmap:$CACHE" "$OSIG" "$(stat -c %s:%Y:%d:%i "$CACHE")"
  cmd overlay enable --user 0 com.beam.translation.settings
  IDMAP_DONE=$((IDMAP_DONE+1))
fi
eval "OVERLAY=\${OV_com_beam_translation_ambient}"
k=${OVERLAY#/}; CACHE=/data/resource-cache/${k//\//@}@idmap
sigv "$OVERLAY"; OSIG=$REPLY; sigv /system/priv-app/SystemUI_release_838/SystemUI_release_838.apk; OSIG="$OSIG|$REPLY"
CK="idmap:${CACHE}_$OSIG"; eval "want=\${HC_${CK//[!A-Za-z0-9]/_}:-}"
sigv "$CACHE"; have=$REPLY
case "$NL$ENABLED$NL" in *"${NL}com.beam.translation.ambient${NL}"*) EN=1;; *) EN=0;; esac
if [ -n "$want" ] && [ "$want" = "$have" ] && [ "$EN" = 1 ]; then IDMAP_SKIPPED=$((IDMAP_SKIPPED+1)); else
  idmap2 create --target-apk-path /system/priv-app/SystemUI_release_838/SystemUI_release_838.apk --overlay-apk-path "$OVERLAY" --idmap-path "$CACHE" --policy public --ignore-overlayable
  chown system:system "$CACHE"
  chmod 644 "$CACHE"
  cache_put "idmap:$CACHE" "$OSIG" "$(stat -c %s:%Y:%d:%i "$CACHE")"
  cmd overlay enable --user 0 com.beam.translation.ambient
  IDMAP_DONE=$((IDMAP_DONE+1))
fi
eval "OVERLAY=\${OV_com_beam_translation_atmosphere}"
k=${OVERLAY#/}; CACHE=/data/resource-cache/${k//\//@}@idmap
sigv "$OVERLAY"; OSIG=$REPLY; sigv /vendor/priv-app/Atmosphere_release838/Atmosphere_release838.apk; OSIG="$OSIG|$REPLY"
CK="idmap:${CACHE}_$OSIG"; eval "want=\${HC_${CK//[!A-Za-z0-9]/_}:-}"
sigv "$CACHE"; have=$REPLY
case "$NL$ENABLED$NL" in *"${NL}com.beam.translation.atmosphere${NL}"*) EN=1;; *) EN=0;; esac
if [ -n "$want" ] && [ "$want" = "$have" ] && [ "$EN" = 1 ]; then IDMAP_SKIPPED=$((IDMAP_SKIPPED+1)); else
  idmap2 create --target-apk-path /vendor/priv-app/Atmosphere_release838/Atmosphere_release838.apk --overlay-apk-path "$OVERLAY" --idmap-path "$CACHE" --policy public --ignore-overlayable
  chown system:system "$CACHE"
  chmod 644 "$CACHE"
  cache_put "idmap:$CACHE" "$OSIG" "$(stat -c %s:%Y:%d:%i "$CACHE")"
  cmd overlay enable --user 0 com.beam.translation.atmosphere
  IDMAP_DONE=$((IDMAP_DONE+1))
fi
eval "OVERLAY=\${OV_com_beam_translation_shutdown}"
k=${OVERLAY#/}; CACHE=/data/resource-cache/${k//\//@}@idmap
sigv "$OVERLAY"; OSIG=$REPLY; sigv /vendor/priv-app/release_838_shutdown/release_838_shutdown.apk; OSIG="$OSIG|$REPLY"
CK="idmap:${CACHE}_$OSIG"; eval "want=\${HC_${CK//[!A-Za-z0-9]/_}:-}"
sigv "$CACHE"; have=$REPLY
case "$NL$ENABLED$NL" in *"${NL}com.beam.translation.shutdown${NL}"*) EN=1;; *) EN=0;; esac
if [ -n "$want" ] && [ "$want" = "$have" ] && [ "$EN" = 1 ]; then IDMAP_SKIPPED=$((IDMAP_SKIPPED+1)); else
  idmap2 create --target-apk-path /vendor/priv-app/release_838_shutdown/release_838_shutdown.apk --overlay-apk-path "$OVERLAY" --idmap-path "$CACHE" --policy public --ignore-overlayable
  chown system:system "$CACHE"
  chmod 644 "$CACHE"
  cache_put "idmap:$CACHE" "$OSIG" "$(stat -c %s:%Y:%d:%i "$CACHE")"
  cmd overlay enable --user 0 com.beam.translation.shutdown
  IDMAP_DONE=$((IDMAP_DONE+1))
fi
eval "OVERLAY=\${OV_com_beam_translation_smartaccessories}"
k=${OVERLAY#/}; CACHE=/data/resource-cache/${k//\//@}@idmap
sigv "$OVERLAY"; OSIG=$REPLY; sigv /vendor/priv-app/smartaccessories_release_838/smartaccessories_release_838.apk; OSIG="$OSIG|$REPLY"
CK="idmap:${CACHE}_$OSIG"; eval "want=\${HC_${CK//[!A-Za-z0-9]/_}:-}"
sigv "$CACHE"; have=$REPLY
case "$NL$ENABLED$NL" in *"${NL}com.beam.translation.smartaccessories${NL}"*) EN=1;; *) EN=0;; esac
if [ -n "$want" ] && [ "$want" = "$have" ] && [ "$EN" = 1 ]; then IDMAP_SKIPPED=$((IDMAP_SKIPPED+1)); else
  idmap2 create --target-apk-path /vendor/priv-app/smartaccessories_release_838/smartaccessories_release_838.apk --overlay-apk-path "$OVERLAY" --idmap-path "$CACHE" --policy public --ignore-overlayable
  chown system:system "$CACHE"
  chmod 644 "$CACHE"
  cache_put "idmap:$CACHE" "$OSIG" "$(stat -c %s:%Y:%d:%i "$CACHE")"
  cmd overlay enable --user 0 com.beam.translation.smartaccessories
  IDMAP_DONE=$((IDMAP_DONE+1))
fi
eval "OVERLAY=\${OV_com_beam_translation_otaaccessories}"
k=${OVERLAY#/}; CACHE=/data/resource-cache/${k//\//@}@idmap
sigv "$OVERLAY"; OSIG=$REPLY; sigv /system/priv-app/XgimiOtaAccessories_release848/XgimiOtaAccessories_release848.apk; OSIG="$OSIG|$REPLY"
CK="idmap:${CACHE}_$OSIG"; eval "want=\${HC_${CK//[!A-Za-z0-9]/_}:-}"
sigv "$CACHE"; have=$REPLY
case "$NL$ENABLED$NL" in *"${NL}com.beam.translation.otaaccessories${NL}"*) EN=1;; *) EN=0;; esac
if [ -n "$want" ] && [ "$want" = "$have" ] && [ "$EN" = 1 ]; then IDMAP_SKIPPED=$((IDMAP_SKIPPED+1)); else
  idmap2 create --target-apk-path /system/priv-app/XgimiOtaAccessories_release848/XgimiOtaAccessories_release848.apk --overlay-apk-path "$OVERLAY" --idmap-path "$CACHE" --policy public --ignore-overlayable
  chown system:system "$CACHE"
  chmod 644 "$CACHE"
  cache_put "idmap:$CACHE" "$OSIG" "$(stat -c %s:%Y:%d:%i "$CACHE")"
  cmd overlay enable --user 0 com.beam.translation.otaaccessories
  IDMAP_DONE=$((IDMAP_DONE+1))
fi
eval "OVERLAY=\${OV_com_beam_translation_xgimiiotserver}"
k=${OVERLAY#/}; CACHE=/data/resource-cache/${k//\//@}@idmap
sigv "$OVERLAY"; OSIG=$REPLY; sigv /vendor/priv-app/xgimiiotserver_release_838/xgimiiotserver_release_838.apk; OSIG="$OSIG|$REPLY"
CK="idmap:${CACHE}_$OSIG"; eval "want=\${HC_${CK//[!A-Za-z0-9]/_}:-}"
sigv "$CACHE"; have=$REPLY
case "$NL$ENABLED$NL" in *"${NL}com.beam.translation.xgimiiotserver${NL}"*) EN=1;; *) EN=0;; esac
if [ -n "$want" ] && [ "$want" = "$have" ] && [ "$EN" = 1 ]; then IDMAP_SKIPPED=$((IDMAP_SKIPPED+1)); else
  idmap2 create --target-apk-path /vendor/priv-app/xgimiiotserver_release_838/xgimiiotserver_release_838.apk --overlay-apk-path "$OVERLAY" --idmap-path "$CACHE" --policy public --ignore-overlayable
  chown system:system "$CACHE"
  chmod 644 "$CACHE"
  cache_put "idmap:$CACHE" "$OSIG" "$(stat -c %s:%Y:%d:%i "$CACHE")"
  cmd overlay enable --user 0 com.beam.translation.xgimiiotserver
  IDMAP_DONE=$((IDMAP_DONE+1))
fi
eval "OVERLAY=\${OV_com_beam_translation_upgrade}"
k=${OVERLAY#/}; CACHE=/data/resource-cache/${k//\//@}@idmap
sigv "$OVERLAY"; OSIG=$REPLY; sigv /vendor/priv-app/update/update.apk; OSIG="$OSIG|$REPLY"
CK="idmap:${CACHE}_$OSIG"; eval "want=\${HC_${CK//[!A-Za-z0-9]/_}:-}"
sigv "$CACHE"; have=$REPLY
case "$NL$ENABLED$NL" in *"${NL}com.beam.translation.upgrade${NL}"*) EN=1;; *) EN=0;; esac
if [ -n "$want" ] && [ "$want" = "$have" ] && [ "$EN" = 1 ]; then IDMAP_SKIPPED=$((IDMAP_SKIPPED+1)); else
  idmap2 create --target-apk-path /vendor/priv-app/update/update.apk --overlay-apk-path "$OVERLAY" --idmap-path "$CACHE" --policy public --ignore-overlayable
  chown system:system "$CACHE"
  chmod 644 "$CACHE"
  cache_put "idmap:$CACHE" "$OSIG" "$(stat -c %s:%Y:%d:%i "$CACHE")"
  cmd overlay enable --user 0 com.beam.translation.upgrade
  IDMAP_DONE=$((IDMAP_DONE+1))
fi
eval "OVERLAY=\${OV_com_beam_translation_wirelessscreen}"
k=${OVERLAY#/}; CACHE=/data/resource-cache/${k//\//@}@idmap
sigv "$OVERLAY"; OSIG=$REPLY; sigv /vendor/priv-app/wirelessscreen/wirelessscreen.apk; OSIG="$OSIG|$REPLY"
CK="idmap:${CACHE}_$OSIG"; eval "want=\${HC_${CK//[!A-Za-z0-9]/_}:-}"
sigv "$CACHE"; have=$REPLY
case "$NL$ENABLED$NL" in *"${NL}com.beam.translation.wirelessscreen${NL}"*) EN=1;; *) EN=0;; esac
if [ -n "$want" ] && [ "$want" = "$have" ] && [ "$EN" = 1 ]; then IDMAP_SKIPPED=$((IDMAP_SKIPPED+1)); else
  idmap2 create --target-apk-path /vendor/priv-app/wirelessscreen/wirelessscreen.apk --overlay-apk-path "$OVERLAY" --idmap-path "$CACHE" --policy public --ignore-overlayable
  chown system:system "$CACHE"
  chmod 644 "$CACHE"
  cache_put "idmap:$CACHE" "$OSIG" "$(stat -c %s:%Y:%d:%i "$CACHE")"
  cmd overlay enable --user 0 com.beam.translation.wirelessscreen
  IDMAP_DONE=$((IDMAP_DONE+1))
fi
eval "OVERLAY=\${OV_com_beam_translation_instruction30}"
k=${OVERLAY#/}; CACHE=/data/resource-cache/${k//\//@}@idmap
sigv "$OVERLAY"; OSIG=$REPLY; sigv /vendor/priv-app/Instruction_release838/Instruction_release838.apk; OSIG="$OSIG|$REPLY"
CK="idmap:${CACHE}_$OSIG"; eval "want=\${HC_${CK//[!A-Za-z0-9]/_}:-}"
sigv "$CACHE"; have=$REPLY
case "$NL$ENABLED$NL" in *"${NL}com.beam.translation.instruction30${NL}"*) EN=1;; *) EN=0;; esac
if [ -n "$want" ] && [ "$want" = "$have" ] && [ "$EN" = 1 ]; then IDMAP_SKIPPED=$((IDMAP_SKIPPED+1)); else
  idmap2 create --target-apk-path /vendor/priv-app/Instruction_release838/Instruction_release838.apk --overlay-apk-path "$OVERLAY" --idmap-path "$CACHE" --policy public --ignore-overlayable
  chown system:system "$CACHE"
  chmod 644 "$CACHE"
  cache_put "idmap:$CACHE" "$OSIG" "$(stat -c %s:%Y:%d:%i "$CACHE")"
  cmd overlay enable --user 0 com.beam.translation.instruction30
  IDMAP_DONE=$((IDMAP_DONE+1))
fi
eval "OVERLAY=\${OV_com_beam_translation_manager}"
k=${OVERLAY#/}; CACHE=/data/resource-cache/${k//\//@}@idmap
sigv "$OVERLAY"; OSIG=$REPLY; sigv /vendor/priv-app/XgimiManager_release838/XgimiManager_release838.apk; OSIG="$OSIG|$REPLY"
CK="idmap:${CACHE}_$OSIG"; eval "want=\${HC_${CK//[!A-Za-z0-9]/_}:-}"
sigv "$CACHE"; have=$REPLY
case "$NL$ENABLED$NL" in *"${NL}com.beam.translation.manager${NL}"*) EN=1;; *) EN=0;; esac
if [ -n "$want" ] && [ "$want" = "$have" ] && [ "$EN" = 1 ]; then IDMAP_SKIPPED=$((IDMAP_SKIPPED+1)); else
  idmap2 create --target-apk-path /vendor/priv-app/XgimiManager_release838/XgimiManager_release838.apk --overlay-apk-path "$OVERLAY" --idmap-path "$CACHE" --policy public --ignore-overlayable
  chown system:system "$CACHE"
  chmod 644 "$CACHE"
  cache_put "idmap:$CACHE" "$OSIG" "$(stat -c %s:%Y:%d:%i "$CACHE")"
  cmd overlay enable --user 0 com.beam.translation.manager
  IDMAP_DONE=$((IDMAP_DONE+1))
fi
eval "OVERLAY=\${OV_com_beam_translation_gmservice}"
k=${OVERLAY#/}; CACHE=/data/resource-cache/${k//\//@}@idmap
sigv "$OVERLAY"; OSIG=$REPLY; sigv /vendor/priv-app/GMService_release838/GMService_release838.apk; OSIG="$OSIG|$REPLY"
CK="idmap:${CACHE}_$OSIG"; eval "want=\${HC_${CK//[!A-Za-z0-9]/_}:-}"
sigv "$CACHE"; have=$REPLY
case "$NL$ENABLED$NL" in *"${NL}com.beam.translation.gmservice${NL}"*) EN=1;; *) EN=0;; esac
if [ -n "$want" ] && [ "$want" = "$have" ] && [ "$EN" = 1 ]; then IDMAP_SKIPPED=$((IDMAP_SKIPPED+1)); else
  idmap2 create --target-apk-path /vendor/priv-app/GMService_release838/GMService_release838.apk --overlay-apk-path "$OVERLAY" --idmap-path "$CACHE" --policy public --ignore-overlayable
  chown system:system "$CACHE"
  chmod 644 "$CACHE"
  cache_put "idmap:$CACHE" "$OSIG" "$(stat -c %s:%Y:%d:%i "$CACHE")"
  cmd overlay enable --user 0 com.beam.translation.gmservice
  IDMAP_DONE=$((IDMAP_DONE+1))
fi
eval "OVERLAY=\${OV_com_beam_translation_user}"
k=${OVERLAY#/}; CACHE=/data/resource-cache/${k//\//@}@idmap
sigv "$OVERLAY"; OSIG=$REPLY; sigv /vendor/priv-app/AccountCenter_release838/AccountCenter_release838.apk; OSIG="$OSIG|$REPLY"
CK="idmap:${CACHE}_$OSIG"; eval "want=\${HC_${CK//[!A-Za-z0-9]/_}:-}"
sigv "$CACHE"; have=$REPLY
case "$NL$ENABLED$NL" in *"${NL}com.beam.translation.user${NL}"*) EN=1;; *) EN=0;; esac
if [ -n "$want" ] && [ "$want" = "$have" ] && [ "$EN" = 1 ]; then IDMAP_SKIPPED=$((IDMAP_SKIPPED+1)); else
  idmap2 create --target-apk-path /vendor/priv-app/AccountCenter_release838/AccountCenter_release838.apk --overlay-apk-path "$OVERLAY" --idmap-path "$CACHE" --policy public --ignore-overlayable
  chown system:system "$CACHE"
  chmod 644 "$CACHE"
  cache_put "idmap:$CACHE" "$OSIG" "$(stat -c %s:%Y:%d:%i "$CACHE")"
  cmd overlay enable --user 0 com.beam.translation.user
  IDMAP_DONE=$((IDMAP_DONE+1))
fi
eval "OVERLAY=\${OV_com_beam_translation_frameworkpower}"
k=${OVERLAY#/}; CACHE=/data/resource-cache/${k//\//@}@idmap
sigv "$OVERLAY"; OSIG=$REPLY; sigv /system/framework/framework-res.apk; OSIG="$OSIG|$REPLY"
CK="idmap:${CACHE}_$OSIG"; eval "want=\${HC_${CK//[!A-Za-z0-9]/_}:-}"
sigv "$CACHE"; have=$REPLY
case "$NL$ENABLED$NL" in *"${NL}com.beam.translation.frameworkpower${NL}"*) EN=1;; *) EN=0;; esac
if [ -n "$want" ] && [ "$want" = "$have" ] && [ "$EN" = 1 ]; then IDMAP_SKIPPED=$((IDMAP_SKIPPED+1)); else
  idmap2 create --target-apk-path /system/framework/framework-res.apk --overlay-apk-path "$OVERLAY" --idmap-path "$CACHE" --policy public --ignore-overlayable
  chown system:system "$CACHE"
  chmod 644 "$CACHE"
  cache_put "idmap:$CACHE" "$OSIG" "$(stat -c %s:%Y:%d:%i "$CACHE")"
  cmd overlay enable --user 0 com.beam.translation.frameworkpower
  IDMAP_DONE=$((IDMAP_DONE+1))
fi
eval "OVERLAY=\${OV_com_beam_translation_config}"
k=${OVERLAY#/}; CACHE=/data/resource-cache/${k//\//@}@idmap
sigv "$OVERLAY"; OSIG=$REPLY; sigv /vendor/priv-app/GlobalConfig_release838/GlobalConfig_release838.apk; OSIG="$OSIG|$REPLY"
CK="idmap:${CACHE}_$OSIG"; eval "want=\${HC_${CK//[!A-Za-z0-9]/_}:-}"
sigv "$CACHE"; have=$REPLY
case "$NL$ENABLED$NL" in *"${NL}com.beam.translation.config${NL}"*) EN=1;; *) EN=0;; esac
if [ -n "$want" ] && [ "$want" = "$have" ] && [ "$EN" = 1 ]; then IDMAP_SKIPPED=$((IDMAP_SKIPPED+1)); else
  idmap2 create --target-apk-path /vendor/priv-app/GlobalConfig_release838/GlobalConfig_release838.apk --overlay-apk-path "$OVERLAY" --idmap-path "$CACHE" --policy public --ignore-overlayable
  chown system:system "$CACHE"
  chmod 644 "$CACHE"
  cache_put "idmap:$CACHE" "$OSIG" "$(stat -c %s:%Y:%d:%i "$CACHE")"
  cmd overlay enable --user 0 com.beam.translation.config
  IDMAP_DONE=$((IDMAP_DONE+1))
fi
eval "OVERLAY=\${OV_com_beam_translation_xrmservice}"
k=${OVERLAY#/}; CACHE=/data/resource-cache/${k//\//@}@idmap
sigv "$OVERLAY"; OSIG=$REPLY; sigv /system/priv-app/XRMService/XRMService.apk; OSIG="$OSIG|$REPLY"
CK="idmap:${CACHE}_$OSIG"; eval "want=\${HC_${CK//[!A-Za-z0-9]/_}:-}"
sigv "$CACHE"; have=$REPLY
case "$NL$ENABLED$NL" in *"${NL}com.beam.translation.xrmservice${NL}"*) EN=1;; *) EN=0;; esac
if [ -n "$want" ] && [ "$want" = "$have" ] && [ "$EN" = 1 ]; then IDMAP_SKIPPED=$((IDMAP_SKIPPED+1)); else
  idmap2 create --target-apk-path /system/priv-app/XRMService/XRMService.apk --overlay-apk-path "$OVERLAY" --idmap-path "$CACHE" --policy public --ignore-overlayable
  chown system:system "$CACHE"
  chmod 644 "$CACHE"
  cache_put "idmap:$CACHE" "$OSIG" "$(stat -c %s:%Y:%d:%i "$CACHE")"
  cmd overlay enable --user 0 com.beam.translation.xrmservice
  IDMAP_DONE=$((IDMAP_DONE+1))
fi
eval "OVERLAY=\${OV_com_beam_translation_soundermodeservice}"
k=${OVERLAY#/}; CACHE=/data/resource-cache/${k//\//@}@idmap
sigv "$OVERLAY"; OSIG=$REPLY; sigv /system/priv-app/NewSounderMode/NewSounderMode.apk; OSIG="$OSIG|$REPLY"
CK="idmap:${CACHE}_$OSIG"; eval "want=\${HC_${CK//[!A-Za-z0-9]/_}:-}"
sigv "$CACHE"; have=$REPLY
case "$NL$ENABLED$NL" in *"${NL}com.beam.translation.soundermodeservice${NL}"*) EN=1;; *) EN=0;; esac
if [ -n "$want" ] && [ "$want" = "$have" ] && [ "$EN" = 1 ]; then IDMAP_SKIPPED=$((IDMAP_SKIPPED+1)); else
  idmap2 create --target-apk-path /system/priv-app/NewSounderMode/NewSounderMode.apk --overlay-apk-path "$OVERLAY" --idmap-path "$CACHE" --policy public --ignore-overlayable
  chown system:system "$CACHE"
  chmod 644 "$CACHE"
  cache_put "idmap:$CACHE" "$OSIG" "$(stat -c %s:%Y:%d:%i "$CACHE")"
  cmd overlay enable --user 0 com.beam.translation.soundermodeservice
  IDMAP_DONE=$((IDMAP_DONE+1))
fi
eval "OVERLAY=\${OV_com_beam_translation_xgimiframeworkui}"
k=${OVERLAY#/}; CACHE=/data/resource-cache/${k//\//@}@idmap
sigv "$OVERLAY"; OSIG=$REPLY; sigv /vendor/app/XgimiFrameworkUi/XgimiFrameworkUi.apk; OSIG="$OSIG|$REPLY"
CK="idmap:${CACHE}_$OSIG"; eval "want=\${HC_${CK//[!A-Za-z0-9]/_}:-}"
sigv "$CACHE"; have=$REPLY
case "$NL$ENABLED$NL" in *"${NL}com.beam.translation.xgimiframeworkui${NL}"*) EN=1;; *) EN=0;; esac
if [ -n "$want" ] && [ "$want" = "$have" ] && [ "$EN" = 1 ]; then IDMAP_SKIPPED=$((IDMAP_SKIPPED+1)); else
  idmap2 create --target-apk-path /vendor/app/XgimiFrameworkUi/XgimiFrameworkUi.apk --overlay-apk-path "$OVERLAY" --idmap-path "$CACHE" --policy public --ignore-overlayable
  chown system:system "$CACHE"
  chmod 644 "$CACHE"
  cache_put "idmap:$CACHE" "$OSIG" "$(stat -c %s:%Y:%d:%i "$CACHE")"
  cmd overlay enable --user 0 com.beam.translation.xgimiframeworkui
  IDMAP_DONE=$((IDMAP_DONE+1))
fi
eval "OVERLAY=\${OV_com_beam_translation_vcontrol}"
k=${OVERLAY#/}; CACHE=/data/resource-cache/${k//\//@}@idmap
sigv "$OVERLAY"; OSIG=$REPLY; sigv /vendor/priv-app/vcontrol_release838/vcontrol_release838.apk; OSIG="$OSIG|$REPLY"
CK="idmap:${CACHE}_$OSIG"; eval "want=\${HC_${CK//[!A-Za-z0-9]/_}:-}"
sigv "$CACHE"; have=$REPLY
case "$NL$ENABLED$NL" in *"${NL}com.beam.translation.vcontrol${NL}"*) EN=1;; *) EN=0;; esac
if [ -n "$want" ] && [ "$want" = "$have" ] && [ "$EN" = 1 ]; then IDMAP_SKIPPED=$((IDMAP_SKIPPED+1)); else
  idmap2 create --target-apk-path /vendor/priv-app/vcontrol_release838/vcontrol_release838.apk --overlay-apk-path "$OVERLAY" --idmap-path "$CACHE" --policy public --ignore-overlayable
  chown system:system "$CACHE"
  chmod 644 "$CACHE"
  cache_put "idmap:$CACHE" "$OSIG" "$(stat -c %s:%Y:%d:%i "$CACHE")"
  cmd overlay enable --user 0 com.beam.translation.vcontrol
  IDMAP_DONE=$((IDMAP_DONE+1))
fi
eval "OVERLAY=\${OV_com_beam_translation_gimiplayer}"
k=${OVERLAY#/}; CACHE=/data/resource-cache/${k//\//@}@idmap
sigv "$OVERLAY"; OSIG=$REPLY; sigv /vendor/priv-app/mediaPlayer_release838/mediaPlayer_release838.apk; OSIG="$OSIG|$REPLY"
CK="idmap:${CACHE}_$OSIG"; eval "want=\${HC_${CK//[!A-Za-z0-9]/_}:-}"
sigv "$CACHE"; have=$REPLY
case "$NL$ENABLED$NL" in *"${NL}com.beam.translation.gimiplayer${NL}"*) EN=1;; *) EN=0;; esac
if [ -n "$want" ] && [ "$want" = "$have" ] && [ "$EN" = 1 ]; then IDMAP_SKIPPED=$((IDMAP_SKIPPED+1)); else
  idmap2 create --target-apk-path /vendor/priv-app/mediaPlayer_release838/mediaPlayer_release838.apk --overlay-apk-path "$OVERLAY" --idmap-path "$CACHE" --policy public --ignore-overlayable
  chown system:system "$CACHE"
  chmod 644 "$CACHE"
  cache_put "idmap:$CACHE" "$OSIG" "$(stat -c %s:%Y:%d:%i "$CACHE")"
  cmd overlay enable --user 0 com.beam.translation.gimiplayer
  IDMAP_DONE=$((IDMAP_DONE+1))
fi
up; echo "t_ov_loop=$UPN"
POLICY=/data/local/xgimi_gmui_manager/sys_pkg_adj.json
POLICY_STATE=ok
if ! grep -q '"com.beam.russifier.boot"' "$POLICY" 2>/dev/null; then
  BASE="$POLICY"
  if [ ! -f "$BASE" ]; then BASE=/vendor/etc/xgimisys/sys_pkg_adj.json; fi
  if awk -v e='        {"pkg": "com.beam.russifier.boot", "max": 800, "min": 500, "start": 200}' '{l[NR]=$0} END{for(i=2;i<=NR;i++) if(l[i] ~ /^    \]/ && l[i-1] ~ /^        }$/){k=i;break} if(!k) exit 3; for(i=1;i<=NR;i++){ if(i==k-1) print "        },"; else if(i==k){print e; print l[i]} else print l[i]}}' "$BASE" > "$POLICY.beam-new" && [ "$(grep -c '{' "$POLICY.beam-new")" = "$(grep -c '}' "$POLICY.beam-new")" ] && grep -q '"com.beam.russifier.boot"' "$POLICY.beam-new"; then
    chown system:system "$POLICY.beam-new"; chmod 600 "$POLICY.beam-new"; restorecon "$POLICY.beam-new" 2>/dev/null
    mv -f "$POLICY.beam-new" "$POLICY"; POLICY_STATE=repaired
  else
    rm -f "$POLICY.beam-new"; POLICY_STATE=repair_failed
  fi
fi
echo "policy=$POLICY_STATE"
up; S_END=$UPN; echo "end_uptime=$S_END boot_completed=$(getprop sys.boot_completed)"
NEWH=$(( $(wc -l < "$HC") - HC_BEFORE ))
echo "cache_new_hashes=$NEWH idmap_done=$IDMAP_DONE idmap_skipped=$IDMAP_SKIPPED full_check=$FULL"
{ printf '%s start=%s nv=%s nr=%s ov=%s end=%s policy=%s hashed=%s idmap=%s/%s full=%s\n' "$(cat /proc/sys/kernel/random/boot_id)" "$S_START" "$S_NV" "$S_NR" "$S_OV" "$S_END" "$POLICY_STATE" "$NEWH" "$IDMAP_DONE" "$IDMAP_SKIPPED" "$FULL" >> "$HIST"; tail -n 60 "$HIST" > "$HIST.new" && mv "$HIST.new" "$HIST"; chmod 644 "$HIST"; } || true
echo "restore=ok"
