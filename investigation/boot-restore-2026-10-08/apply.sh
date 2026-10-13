#!/system/bin/sh
umask 022
D=/data/local/beam-russifier-boot
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
test "$(getprop sys.boot_completed)" = 1
zyg=$(pidof zygote)
test -n "$zyg"
test "${zyg#* }" = "$zyg"
check_hash() { actual=$(sha256sum "$1" | cut -d " " -f 1); test "$actual" = "$2"; }
runtime_hash() { nsenter -t "$zyg" -m -- sha256sum "$1" | cut -d " " -f 1; }
check_hash "$D/panel.apk" 25bfc0f5b296bf9d487fc3da61b62e2c423df6016f320385a0a213369f5714ab
check_hash "$D/wirelessscreen-native.apk" 890a6ce5ba06216650434c8330acae014d9e87544a6e136732c4010f05d7c551
check_hash "$D/gmservice-native.apk" eeb9b3afbf8e091ffe5baa63a371e25970d9501dd13b78ab967fdeb9f56c9479
actual=$(runtime_hash /system/priv-app/release_838_newsettings/release_838_newsettings.apk)
case "$actual" in 15a871680fef952e7f29365643e18e6cfab25e6cd523fa8aadc52c6eeffa84a1|25bfc0f5b296bf9d487fc3da61b62e2c423df6016f320385a0a213369f5714ab) : ;; *) echo 'Unexpected APK: com.android.newsettings'; exit 12 ;; esac
actual=$(runtime_hash /system/priv-app/SystemUI_release_838/SystemUI_release_838.apk)
case "$actual" in 740321166c5e3703e52dd2a1ea55de38a146bc6ea3624f2dd221f0ceacc14308) : ;; *) echo 'Unexpected APK: com.xgimi.systemui'; exit 12 ;; esac
actual=$(runtime_hash /vendor/priv-app/Atmosphere_release838/Atmosphere_release838.apk)
case "$actual" in a0638a3db737357c619b60b43175b4c4bf31d614b172c548a82d5d855ff2d9eb) : ;; *) echo 'Unexpected APK: com.xgimi.atmosphere'; exit 12 ;; esac
actual=$(runtime_hash /vendor/priv-app/release_838_shutdown/release_838_shutdown.apk)
case "$actual" in 6b2e3298157de17091d6fd69093181733b6038aa9c107571f53439db98705d23) : ;; *) echo 'Unexpected APK: com.xgimi.shutdown'; exit 12 ;; esac
actual=$(runtime_hash /vendor/priv-app/smartaccessories_release_838/smartaccessories_release_838.apk)
case "$actual" in 7390ca0e4d474e9ef79ba31adf53229135acdfed8fd0a501e893d101c15c26bc) : ;; *) echo 'Unexpected APK: com.xgimi.smartaccessories'; exit 12 ;; esac
actual=$(runtime_hash /system/priv-app/XgimiOtaAccessories_release848/XgimiOtaAccessories_release848.apk)
case "$actual" in 62ee3ac5cd4e70f2b98d7cf30d9c5a4996588024dad0faf99e47ed68fc57f88d) : ;; *) echo 'Unexpected APK: com.xgimi.ota.accessories'; exit 12 ;; esac
actual=$(runtime_hash /vendor/priv-app/xgimiiotserver_release_838/xgimiiotserver_release_838.apk)
case "$actual" in 871d78c86a4d72445bdace1934e8375e3a97390c50ba25815db4b35aaafe2d03) : ;; *) echo 'Unexpected APK: com.xgimi.xgimiiotserver'; exit 12 ;; esac
actual=$(runtime_hash /vendor/priv-app/update/update.apk)
case "$actual" in 9e42ca671911ec1db739e4c3c16179b66583b09cdaa0e6d35bc660393a872a6d) : ;; *) echo 'Unexpected APK: com.xgimi.upgrade'; exit 12 ;; esac
actual=$(runtime_hash /vendor/priv-app/wirelessscreen/wirelessscreen.apk)
case "$actual" in 061191874aa6aca4e747b27b25a5c3bb8937451572fb36d9f8e76c82ec63785a|890a6ce5ba06216650434c8330acae014d9e87544a6e136732c4010f05d7c551) : ;; *) echo 'Unexpected APK: com.xgimi.wirelessscreen'; exit 12 ;; esac
actual=$(runtime_hash /vendor/priv-app/Instruction_release838/Instruction_release838.apk)
case "$actual" in ab452a3f89151e57afd130376f1242813f50476e6a70a1470921a0ec00e8f821) : ;; *) echo 'Unexpected APK: com.xgimi.instruction30'; exit 12 ;; esac
actual=$(runtime_hash /vendor/priv-app/XgimiManager_release838/XgimiManager_release838.apk)
case "$actual" in 2401bfa54ca98499a706d9f6f9c476971ba06a648d78865468b496e9b06bd9dd) : ;; *) echo 'Unexpected APK: com.xgimi.manager'; exit 12 ;; esac
actual=$(runtime_hash /vendor/priv-app/GMService_release838/GMService_release838.apk)
case "$actual" in 5d3d6444bcf8ffb4717db81a3f36b44fdf655df045d8cb921ee3ffbd4753f797|eeb9b3afbf8e091ffe5baa63a371e25970d9501dd13b78ab967fdeb9f56c9479) : ;; *) echo 'Unexpected APK: com.xgimi.gmservice'; exit 12 ;; esac
actual=$(runtime_hash /vendor/priv-app/AccountCenter_release838/AccountCenter_release838.apk)
case "$actual" in e07dc54411904c9db7a21f90ac96b665cc4c1b8c6b8d43721e7b5ee89637bc19) : ;; *) echo 'Unexpected APK: com.xgimi.user'; exit 12 ;; esac
OVERLAY=$(pm path com.beam.translation.systemui)
OVERLAY=${OVERLAY#package:}
test -f "$OVERLAY"
check_hash "$OVERLAY" 77548eb01e245b07839df8c9d2f0050f6e1196631bfe9a1cd51a57aaf70d1621
OVERLAY=$(pm path com.beam.translation.settings)
OVERLAY=${OVERLAY#package:}
test -f "$OVERLAY"
check_hash "$OVERLAY" 1ff2277e14bfa6950f7fd82f5ca84d3f72d1a77349196b5732ae9855acec163e
OVERLAY=$(pm path com.beam.translation.ambient)
OVERLAY=${OVERLAY#package:}
test -f "$OVERLAY"
check_hash "$OVERLAY" 0c97f36f50144da872121f8acbd33a06887ecf45c4b9521e12d6bd29f5c66a38
OVERLAY=$(pm path com.beam.translation.atmosphere)
OVERLAY=${OVERLAY#package:}
test -f "$OVERLAY"
check_hash "$OVERLAY" 74748ad5a7f51456efb1e0090d5858828b2ab5cfb66a0e01013c83fefb89c535
OVERLAY=$(pm path com.beam.translation.shutdown)
OVERLAY=${OVERLAY#package:}
test -f "$OVERLAY"
check_hash "$OVERLAY" c1aa423a72f091644f9eda4c777cf95aa8c3f82efa85f071319b61a37a264ecc
OVERLAY=$(pm path com.beam.translation.smartaccessories)
OVERLAY=${OVERLAY#package:}
test -f "$OVERLAY"
check_hash "$OVERLAY" b72ad586022d8102db8ca54088b568e3f7abccd82f689314d9c71468ca2b2703
OVERLAY=$(pm path com.beam.translation.otaaccessories)
OVERLAY=${OVERLAY#package:}
test -f "$OVERLAY"
check_hash "$OVERLAY" 527153ba726039a513832a217be18984ae7d7c1efa8184ed9b7183ead5d7e504
OVERLAY=$(pm path com.beam.translation.xgimiiotserver)
OVERLAY=${OVERLAY#package:}
test -f "$OVERLAY"
check_hash "$OVERLAY" a4e5cd91bff5e1fa395251a3adcb1e96a7ff3febeb8f6b1278533d6a3885378b
OVERLAY=$(pm path com.beam.translation.upgrade)
OVERLAY=${OVERLAY#package:}
test -f "$OVERLAY"
check_hash "$OVERLAY" f76fb30682adfa39904af7c570057f66feca5ec008dfc36c972091a9c03ad8e2
OVERLAY=$(pm path com.beam.translation.wirelessscreen)
OVERLAY=${OVERLAY#package:}
test -f "$OVERLAY"
check_hash "$OVERLAY" db7b21bf5afe0ea3be0df824d4ca5bdf0ed20985b884c1bfebce4c6c62821c9b
OVERLAY=$(pm path com.beam.translation.instruction30)
OVERLAY=${OVERLAY#package:}
test -f "$OVERLAY"
check_hash "$OVERLAY" f46430e8fc4df6aa71c926d78eb7af93c42e13ed65b8daae3728596d1dd1a043
OVERLAY=$(pm path com.beam.translation.manager)
OVERLAY=${OVERLAY#package:}
test -f "$OVERLAY"
check_hash "$OVERLAY" ed34c023c4cd6d5c08495a2d54d451dad96f495afc661be34af1b512732a1fdf
OVERLAY=$(pm path com.beam.translation.gmservice)
OVERLAY=${OVERLAY#package:}
test -f "$OVERLAY"
check_hash "$OVERLAY" 9ac18f1cdbe76d493c959807840238960ac43217021e746185a84cf56a1e3bac
OVERLAY=$(pm path com.beam.translation.user)
OVERLAY=${OVERLAY#package:}
test -f "$OVERLAY"
check_hash "$OVERLAY" 4585143fc31df61f5ab91aa4e700426b241b4f7af5b6b328865bdb8d26532fba
check_hash "$D/skin.apk" 317202039f4bd31de63e8b8a1e9b9d3e16507810aaf203664491ae2984cc1a92
OVERLAY=$(pm path com.beam.translation.systemui)
OVERLAY=${OVERLAY#package:}
CACHE=/data/resource-cache/$(echo "${OVERLAY#/}" | tr / @)@idmap
idmap2 create --target-apk-path /system/priv-app/SystemUI_release_838/SystemUI_release_838.apk --overlay-apk-path "$OVERLAY" --idmap-path "$CACHE" --policy public --ignore-overlayable
chown system:system "$CACHE"
chmod 644 "$CACHE"
cmd overlay enable --user 0 com.beam.translation.systemui
OVERLAY=$(pm path com.beam.translation.settings)
OVERLAY=${OVERLAY#package:}
CACHE=/data/resource-cache/$(echo "${OVERLAY#/}" | tr / @)@idmap
idmap2 create --target-apk-path /system/priv-app/release_838_newsettings/release_838_newsettings.apk --overlay-apk-path "$OVERLAY" --idmap-path "$CACHE" --policy public --ignore-overlayable
chown system:system "$CACHE"
chmod 644 "$CACHE"
cmd overlay enable --user 0 com.beam.translation.settings
OVERLAY=$(pm path com.beam.translation.ambient)
OVERLAY=${OVERLAY#package:}
CACHE=/data/resource-cache/$(echo "${OVERLAY#/}" | tr / @)@idmap
idmap2 create --target-apk-path /system/priv-app/SystemUI_release_838/SystemUI_release_838.apk --overlay-apk-path "$OVERLAY" --idmap-path "$CACHE" --policy public --ignore-overlayable
chown system:system "$CACHE"
chmod 644 "$CACHE"
cmd overlay enable --user 0 com.beam.translation.ambient
OVERLAY=$(pm path com.beam.translation.atmosphere)
OVERLAY=${OVERLAY#package:}
CACHE=/data/resource-cache/$(echo "${OVERLAY#/}" | tr / @)@idmap
idmap2 create --target-apk-path /vendor/priv-app/Atmosphere_release838/Atmosphere_release838.apk --overlay-apk-path "$OVERLAY" --idmap-path "$CACHE" --policy public --ignore-overlayable
chown system:system "$CACHE"
chmod 644 "$CACHE"
cmd overlay enable --user 0 com.beam.translation.atmosphere
OVERLAY=$(pm path com.beam.translation.shutdown)
OVERLAY=${OVERLAY#package:}
CACHE=/data/resource-cache/$(echo "${OVERLAY#/}" | tr / @)@idmap
idmap2 create --target-apk-path /vendor/priv-app/release_838_shutdown/release_838_shutdown.apk --overlay-apk-path "$OVERLAY" --idmap-path "$CACHE" --policy public --ignore-overlayable
chown system:system "$CACHE"
chmod 644 "$CACHE"
cmd overlay enable --user 0 com.beam.translation.shutdown
OVERLAY=$(pm path com.beam.translation.smartaccessories)
OVERLAY=${OVERLAY#package:}
CACHE=/data/resource-cache/$(echo "${OVERLAY#/}" | tr / @)@idmap
idmap2 create --target-apk-path /vendor/priv-app/smartaccessories_release_838/smartaccessories_release_838.apk --overlay-apk-path "$OVERLAY" --idmap-path "$CACHE" --policy public --ignore-overlayable
chown system:system "$CACHE"
chmod 644 "$CACHE"
cmd overlay enable --user 0 com.beam.translation.smartaccessories
OVERLAY=$(pm path com.beam.translation.otaaccessories)
OVERLAY=${OVERLAY#package:}
CACHE=/data/resource-cache/$(echo "${OVERLAY#/}" | tr / @)@idmap
idmap2 create --target-apk-path /system/priv-app/XgimiOtaAccessories_release848/XgimiOtaAccessories_release848.apk --overlay-apk-path "$OVERLAY" --idmap-path "$CACHE" --policy public --ignore-overlayable
chown system:system "$CACHE"
chmod 644 "$CACHE"
cmd overlay enable --user 0 com.beam.translation.otaaccessories
OVERLAY=$(pm path com.beam.translation.xgimiiotserver)
OVERLAY=${OVERLAY#package:}
CACHE=/data/resource-cache/$(echo "${OVERLAY#/}" | tr / @)@idmap
idmap2 create --target-apk-path /vendor/priv-app/xgimiiotserver_release_838/xgimiiotserver_release_838.apk --overlay-apk-path "$OVERLAY" --idmap-path "$CACHE" --policy public --ignore-overlayable
chown system:system "$CACHE"
chmod 644 "$CACHE"
cmd overlay enable --user 0 com.beam.translation.xgimiiotserver
OVERLAY=$(pm path com.beam.translation.upgrade)
OVERLAY=${OVERLAY#package:}
CACHE=/data/resource-cache/$(echo "${OVERLAY#/}" | tr / @)@idmap
idmap2 create --target-apk-path /vendor/priv-app/update/update.apk --overlay-apk-path "$OVERLAY" --idmap-path "$CACHE" --policy public --ignore-overlayable
chown system:system "$CACHE"
chmod 644 "$CACHE"
cmd overlay enable --user 0 com.beam.translation.upgrade
OVERLAY=$(pm path com.beam.translation.wirelessscreen)
OVERLAY=${OVERLAY#package:}
CACHE=/data/resource-cache/$(echo "${OVERLAY#/}" | tr / @)@idmap
idmap2 create --target-apk-path /vendor/priv-app/wirelessscreen/wirelessscreen.apk --overlay-apk-path "$OVERLAY" --idmap-path "$CACHE" --policy public --ignore-overlayable
chown system:system "$CACHE"
chmod 644 "$CACHE"
cmd overlay enable --user 0 com.beam.translation.wirelessscreen
OVERLAY=$(pm path com.beam.translation.instruction30)
OVERLAY=${OVERLAY#package:}
CACHE=/data/resource-cache/$(echo "${OVERLAY#/}" | tr / @)@idmap
idmap2 create --target-apk-path /vendor/priv-app/Instruction_release838/Instruction_release838.apk --overlay-apk-path "$OVERLAY" --idmap-path "$CACHE" --policy public --ignore-overlayable
chown system:system "$CACHE"
chmod 644 "$CACHE"
cmd overlay enable --user 0 com.beam.translation.instruction30
OVERLAY=$(pm path com.beam.translation.manager)
OVERLAY=${OVERLAY#package:}
CACHE=/data/resource-cache/$(echo "${OVERLAY#/}" | tr / @)@idmap
idmap2 create --target-apk-path /vendor/priv-app/XgimiManager_release838/XgimiManager_release838.apk --overlay-apk-path "$OVERLAY" --idmap-path "$CACHE" --policy public --ignore-overlayable
chown system:system "$CACHE"
chmod 644 "$CACHE"
cmd overlay enable --user 0 com.beam.translation.manager
OVERLAY=$(pm path com.beam.translation.gmservice)
OVERLAY=${OVERLAY#package:}
CACHE=/data/resource-cache/$(echo "${OVERLAY#/}" | tr / @)@idmap
idmap2 create --target-apk-path /vendor/priv-app/GMService_release838/GMService_release838.apk --overlay-apk-path "$OVERLAY" --idmap-path "$CACHE" --policy public --ignore-overlayable
chown system:system "$CACHE"
chmod 644 "$CACHE"
cmd overlay enable --user 0 com.beam.translation.gmservice
OVERLAY=$(pm path com.beam.translation.user)
OVERLAY=${OVERLAY#package:}
CACHE=/data/resource-cache/$(echo "${OVERLAY#/}" | tr / @)@idmap
idmap2 create --target-apk-path /vendor/priv-app/AccountCenter_release838/AccountCenter_release838.apk --overlay-apk-path "$OVERLAY" --idmap-path "$CACHE" --policy public --ignore-overlayable
chown system:system "$CACHE"
chmod 644 "$CACHE"
cmd overlay enable --user 0 com.beam.translation.user
setprop persist.sys.xgimi.themeV2.url "$D/skin.apk"
if [ "$(runtime_hash /system/priv-app/release_838_newsettings/release_838_newsettings.apk)" != 25bfc0f5b296bf9d487fc3da61b62e2c423df6016f320385a0a213369f5714ab ]; then
  nsenter -t "$zyg" -m -- mount -o bind "$D/panel.apk" /system/priv-app/release_838_newsettings/release_838_newsettings.apk
  am force-stop com.android.newsettings
fi
test "$(runtime_hash /system/priv-app/release_838_newsettings/release_838_newsettings.apk)" = 25bfc0f5b296bf9d487fc3da61b62e2c423df6016f320385a0a213369f5714ab
if [ "$(runtime_hash /vendor/priv-app/wirelessscreen/wirelessscreen.apk)" != 890a6ce5ba06216650434c8330acae014d9e87544a6e136732c4010f05d7c551 ]; then
  nsenter -t "$zyg" -m -- mount -o bind "$D/wirelessscreen-native.apk" /vendor/priv-app/wirelessscreen/wirelessscreen.apk
  am force-stop com.xgimi.wirelessscreen
fi
test "$(runtime_hash /vendor/priv-app/wirelessscreen/wirelessscreen.apk)" = 890a6ce5ba06216650434c8330acae014d9e87544a6e136732c4010f05d7c551
if [ "$(runtime_hash /vendor/priv-app/GMService_release838/GMService_release838.apk)" != eeb9b3afbf8e091ffe5baa63a371e25970d9501dd13b78ab967fdeb9f56c9479 ]; then
  nsenter -t "$zyg" -m -- mount -o bind "$D/gmservice-native.apk" /vendor/priv-app/GMService_release838/GMService_release838.apk
  am force-stop com.xgimi.gmservice
fi
test "$(runtime_hash /vendor/priv-app/GMService_release838/GMService_release838.apk)" = eeb9b3afbf8e091ffe5baa63a371e25970d9501dd13b78ab967fdeb9f56c9479
echo "restore=ok"
