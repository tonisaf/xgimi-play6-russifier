#!/system/bin/sh
umask 022
D=/data/local/beam-russifier-boot/releases/1.19.52-747e4486563a96ed
RUN=$(cat /proc/sys/kernel/random/uuid)
finish() { code=$?; if [ "$(getprop vendor.xgimi.system.debug.cmd)" = "/system/bin/sh $D/skin.sh" ]; then setprop vendor.xgimi.system.debug.cmd ""; setprop vendor.xgimi.system.debugserver ""; fi; printf "%s %s\n" "$RUN" "$code" > "$D/done"; chmod 644 "$D/done"; }
trap finish EXIT
exec > "$D/last.log" 2>&1
set -e
echo "boot=$(cat /proc/sys/kernel/random/boot_id)"
id
DEVICE_IDENTITY="$(getprop ro.build.fingerprint) $(getprop ro.build.version.sdk)"
if [ "$DEVICE_IDENTITY" != 'XGIMI/Product_dayao/dragon_healthy:11/RP1A.200720.011/v1.7.116:user/dev-keys 30' ]; then
  test -f "$D/device-identity" && test "$DEVICE_IDENTITY" = "$(cat "$D/device-identity")" || exit 11
  test "$(sha256sum /system/priv-app/release_838_newsettings/release_838_newsettings.apk | cut -d " " -f 1)" = 15a871680fef952e7f29365643e18e6cfab25e6cd523fa8aadc52c6eeffa84a1
  test "$(sha256sum /system/priv-app/SystemUI_release_838/SystemUI_release_838.apk | cut -d " " -f 1)" = 740321166c5e3703e52dd2a1ea55de38a146bc6ea3624f2dd221f0ceacc14308
  test "$(sha256sum /vendor/priv-app/Atmosphere_release838/Atmosphere_release838.apk | cut -d " " -f 1)" = a0638a3db737357c619b60b43175b4c4bf31d614b172c548a82d5d855ff2d9eb
  test "$(sha256sum /vendor/priv-app/release_838_shutdown/release_838_shutdown.apk | cut -d " " -f 1)" = 6b2e3298157de17091d6fd69093181733b6038aa9c107571f53439db98705d23
  test "$(sha256sum /vendor/priv-app/smartaccessories_release_838/smartaccessories_release_838.apk | cut -d " " -f 1)" = 7390ca0e4d474e9ef79ba31adf53229135acdfed8fd0a501e893d101c15c26bc
  test "$(sha256sum /system/priv-app/XgimiOtaAccessories_release848/XgimiOtaAccessories_release848.apk | cut -d " " -f 1)" = 62ee3ac5cd4e70f2b98d7cf30d9c5a4996588024dad0faf99e47ed68fc57f88d
  test "$(sha256sum /vendor/priv-app/xgimiiotserver_release_838/xgimiiotserver_release_838.apk | cut -d " " -f 1)" = 871d78c86a4d72445bdace1934e8375e3a97390c50ba25815db4b35aaafe2d03
  test "$(sha256sum /vendor/priv-app/update/update.apk | cut -d " " -f 1)" = 9e42ca671911ec1db739e4c3c16179b66583b09cdaa0e6d35bc660393a872a6d
  test "$(sha256sum /vendor/priv-app/wirelessscreen/wirelessscreen.apk | cut -d " " -f 1)" = 061191874aa6aca4e747b27b25a5c3bb8937451572fb36d9f8e76c82ec63785a
  test "$(sha256sum /vendor/priv-app/Instruction_release838/Instruction_release838.apk | cut -d " " -f 1)" = ab452a3f89151e57afd130376f1242813f50476e6a70a1470921a0ec00e8f821
  test "$(sha256sum /vendor/priv-app/XgimiManager_release838/XgimiManager_release838.apk | cut -d " " -f 1)" = 2401bfa54ca98499a706d9f6f9c476971ba06a648d78865468b496e9b06bd9dd
  test "$(sha256sum /vendor/priv-app/GMService_release838/GMService_release838.apk | cut -d " " -f 1)" = 5d3d6444bcf8ffb4717db81a3f36b44fdf655df045d8cb921ee3ffbd4753f797
  test "$(sha256sum /vendor/priv-app/AccountCenter_release838/AccountCenter_release838.apk | cut -d " " -f 1)" = e07dc54411904c9db7a21f90ac96b665cc4c1b8c6b8d43721e7b5ee89637bc19
  test "$(sha256sum /vendor/app/XgimiFrameworkUi/XgimiFrameworkUi.apk | cut -d " " -f 1)" = 9869ccf062ded8c37e399618ad909f48317a2df079dfa88daab25ec9bbaa978a
  test "$(sha256sum /system/framework/framework-res.apk | cut -d " " -f 1)" = 82b06bd7cba9faf3acbdbaf409b7b514e3559209acc18cd99026844ca86f5f66
  test "$(sha256sum /vendor/priv-app/GlobalConfig_release838/GlobalConfig_release838.apk | cut -d " " -f 1)" = 1c83c3c170d5899aab8a2c4cb10959b649c202dc00e328464a219690bdd9aede
  test "$(sha256sum /system/priv-app/XRMService/XRMService.apk | cut -d " " -f 1)" = 40274f5049bd450047ac43cb049b5a120dd2c145964f7722f7cb5c70e07c6048
  test "$(sha256sum /system/priv-app/NewSounderMode/NewSounderMode.apk | cut -d " " -f 1)" = 4634cf008a1926de7dc231717a988635a4f568f0599170ec715372ae4f6edc33
  test "$(sha256sum /vendor/priv-app/vcontrol_release838/vcontrol_release838.apk | cut -d " " -f 1)" = 3f588ddc4dc362be833f9d5960d69a5864d9c77bedcfd87cda30af7ca2f2abe7
  test "$(sha256sum /vendor/priv-app/mediaPlayer_release838/mediaPlayer_release838.apk | cut -d " " -f 1)" = 629387b9eec7f0bd6d200f59fc0e89584d4dbf1e96b7aea75dd73374efc603fd
  test "$(sha256sum /vendor/priv-app/XgimiMusicPlayer_no_u3dRelease838/XgimiMusicPlayer_no_u3dRelease838.apk | cut -d " " -f 1)" = cd3a7b30c8aa6170b2d5a89b1872bebff794e39a30c3c335ca51bc1261904d6e
fi
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
