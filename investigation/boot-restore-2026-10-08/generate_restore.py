"""Generate a fixed, checksum-gated boot restore; no supplied command is executed."""
from pathlib import Path
import hashlib,json,shlex
H=Path(__file__).resolve().parent;ROOT=H.parents[1]
m=json.loads((ROOT/'russifier/manifest.json').read_text(encoding='utf-8'))
q=shlex.quote
D='/data/local/beam-russifier-boot'
native=[{'target':'com.android.newsettings','file':'panel.apk'}]+m['runtimePatches']
lines=['#!/system/bin/sh','umask 022',f'D={q(D)}','RUN=$(cat /proc/sys/kernel/random/uuid)',
 'finish() { code=$?; if [ "$(getprop vendor.xgimi.system.debug.cmd)" = "/system/bin/sh $D/apply.sh" ]; then setprop vendor.xgimi.system.debug.cmd ""; setprop vendor.xgimi.system.debugserver ""; fi; printf "%s %s\\n" "$RUN" "$code" > "$D/done"; chmod 644 "$D/done"; }',
 "trap finish EXIT",'exec > "$D/last.log" 2>&1','set -e',
 'echo "boot=$(cat /proc/sys/kernel/random/boot_id)"','id',
 'test "$(getprop ro.build.fingerprint)" = '+q(m['fingerprint']),
 'test "$(getprop ro.build.version.sdk)" = '+q(m['sdk']),
 'test "$(getprop persist.sys.locale)" = ru-RU',
 'test "$(getenforce)" = Permissive',
 'test "$(getprop sys.boot_completed)" = 1',
 'zyg=$(pidof zygote)','test -n "$zyg"','test "${zyg#* }" = "$zyg"',
 'check_hash() { actual=$(sha256sum "$1" | cut -d " " -f 1); test "$actual" = "$2"; }',
 'runtime_hash() { nsenter -t "$zyg" -m -- sha256sum "$1" | cut -d " " -f 1; }']
# Validate everything before touching overlays or mounts.
for item in native:
 lines += ['check_hash "$D/'+item['file']+'" '+q(m['files'][item['file']])]
for target,original in m['originals'].items():
 allowed=[original['sha256']]+[m['files'][item['file']] for item in native if item['target']==target]
 lines += ['actual=$(runtime_hash '+q(original['path'])+')',
           'case "$actual" in '+'|'.join(allowed)+') : ;; *) echo '+q('Unexpected APK: '+target)+'; exit 12 ;; esac']
for item in m['overlays']:
 lines += ['OVERLAY=$(pm path '+q(item['package'])+')','OVERLAY=${OVERLAY#package:}',
  'test -f "$OVERLAY"','check_hash "$OVERLAY" '+q(m['files'][item['file']])]
lines += ['check_hash "$D/skin.apk" '+q(m['files']['skin.apk'])]
for item in m['overlays']:
 lines += ['OVERLAY=$(pm path '+q(item['package'])+')','OVERLAY=${OVERLAY#package:}',
  'CACHE=/data/resource-cache/$(echo "${OVERLAY#/}" | tr / @)@idmap',
  'idmap2 create --target-apk-path '+q(m['originals'][item['target']]['path'])+' --overlay-apk-path "$OVERLAY" --idmap-path "$CACHE" --policy public --ignore-overlayable',
  'chown system:system "$CACHE"','chmod 644 "$CACHE"','cmd overlay enable --user 0 '+q(item['package'])]
lines += ['setprop persist.sys.xgimi.themeV2.url "$D/skin.apk"']
for item in native:
 target=m['originals'][item['target']]['path'];digest=m['files'][item['file']]
 lines += ['if [ "$(runtime_hash '+q(target)+')" != '+q(digest)+' ]; then',
  '  nsenter -t "$zyg" -m -- mount -o bind "$D/'+item['file']+'" '+q(target),
  '  am force-stop '+q(item['target']), 'fi',
  'test "$(runtime_hash '+q(target)+')" = '+q(digest)]
lines += ['echo "restore=ok"']
script='\n'.join(lines)+'\n';(H/'apply.sh').write_text(script,encoding='utf-8',newline='\n')
digest=hashlib.sha256(script.encode('utf-8')).hexdigest()
constants=H/'app/src/com/beam/russifier/boot/RestoreConfig.java'
constants.write_text('package com.beam.russifier.boot;\nfinal class RestoreConfig {\n'
 'static final String FINGERPRINT = '+json.dumps(m['fingerprint'])+';\n'
 'static final String SCRIPT = '+json.dumps(D+'/apply.sh')+';\n'
 'static final String SHA256 = '+json.dumps(digest)+';\n'
 'static final String DIRECTORY = '+json.dumps(D)+';\n}\n',encoding='utf-8')
print(json.dumps({'scriptSha256':digest,'nativePatches':len(native),'overlays':len(m['overlays'])}))
