"""Generate a fixed, checksum-gated boot restore; no supplied command is executed."""
from pathlib import Path
import hashlib,json,re,shlex
H=Path(__file__).resolve().parent;ROOT=H.parents[1]
m=json.loads((ROOT/'russifier/manifest.json').read_text(encoding='utf-8'))
q=shlex.quote
identity=hashlib.sha256()
identity.update(json.dumps(m,sort_keys=True).encode())
identity.update(Path(__file__).read_bytes())
identity.update((H/'app/AndroidManifest.xml').read_bytes())
for source in sorted((H/'app/src').rglob('*.java')):
 if source.name!='RestoreConfig.java': identity.update(source.read_bytes())
D='/data/local/beam-russifier-boot/releases/'+m['version']+'-'+identity.hexdigest()[:16]
native=[{'target':'com.android.newsettings','file':'panel.apk'}]+m['runtimePatches']
lines=['#!/system/bin/sh','umask 022',f'D={q(D)}','RUN=$(cat /proc/sys/kernel/random/uuid)',
 'finish() { code=$?; if [ "$(getprop vendor.xgimi.system.debug.cmd)" = "/system/bin/sh $D/apply.sh" ]; then setprop vendor.xgimi.system.debug.cmd ""; setprop vendor.xgimi.system.debugserver ""; fi; printf "%s %s\\n" "$RUN" "$code" > "$D/done"; chmod 644 "$D/done"; }',
 "trap finish EXIT",'exec > "$D/last.log" 2>&1','set -e',
 'echo "boot=$(cat /proc/sys/kernel/random/boot_id)"','id',
 'test "$(getprop ro.build.fingerprint)" = '+q(m['fingerprint']),
 'test "$(getprop ro.build.version.sdk)" = '+q(m['sdk']),
 'test "$(getprop persist.sys.locale)" = ru-RU',
 'test "$(getenforce)" = Permissive',
 'echo "start_uptime=$(cut -d \" \" -f 1 /proc/uptime) boot_completed=$(getprop sys.boot_completed)"',
 'zyg=$(pidof zygote)','test -n "$zyg"','test "${zyg#* }" = "$zyg"',
 ]
# Hash cache: an immutable file is re-read only when path, size, mtime, device or inode change.
# Every 20th run ignores the cache and re-reads everything, so silent corruption is still found.
# Lookups use shell built-ins and one batched stat: each exec costs ~15 ms on this device.
CACHE_BLOCK=r'''ROOTDIR=/data/local/beam-russifier-boot
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
eval "$(stat -c "$SIGF" @PAYLOAD@ @ORIG@ 2>/dev/null | mkvars SG_)"
eval "$(nsenter -t "$zyg" -m -- stat -c "$SIGF" @ORIG@ 2>/dev/null | mkvars NS_)"
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
up; S_START=$UPN'''
payload_args=' '.join('"$D/'+f+'"' for f in [i['file'] for i in native]+['skin.apk'])
orig_args=' '.join(q(o['path']) for o in m['originals'].values())
lines += [CACHE_BLOCK.replace('@PAYLOAD@',payload_args).replace('@ORIG@',orig_args)]
# Native patches form their own phase: validate every source and native target first.
# Verify the mount by inode afterwards; the same root-owned source was just hashed.
for item in native:
 lines += ['check_hash2 "$D/'+item['file']+'" '+q(m['files'][item['file']])]
lines += ['check_hash2 "$D/skin.apk" '+q(m['files']['skin.apk'])]
for index,item in enumerate(native):
 target=item['target']; original=m['originals'][target]
 allowed=[original['sha256'],m['files'][item['file']]]
 allowed+=item.get('previousHashes',[])
 if target=='com.android.newsettings': allowed+=m.get('previousPanelHashes',[])
 lines += ['rt_hash '+q(original['path'])+'; NATIVE_'+str(index)+'=$RH',
           'case "$NATIVE_'+str(index)+'" in '+'|'.join(allowed)+') : ;; *) echo '+q('Unexpected APK: '+target)+'; exit 12 ;; esac']
lines += ['up; S_NV=$UPN; echo "native_validated_uptime=$S_NV"',
          'OLD_SKIN=$(getprop persist.sys.xgimi.themeV2.url)',
          'setprop persist.sys.xgimi.themeV2.url "$D/skin.apk"']
import re
lines += ['PSN=$(ps -A -o NAME)']          # one snapshot: which application processes exist before the mounts
for index,item in enumerate(native):
 target=m['originals'][item['target']]['path']; digest=m['files'][item['file']]; pkg=item['target']
 # Only a running application needs a restart; a stopped one starts later from the already mounted APK.
 # Restarts run in the background (each `am` is a JVM start, ~0.3 s) and are awaited once before the final checks.
 restart='am force-stop '+q(pkg)+' &'
 if pkg=='com.xgimi.systemui':
  restart='p=$(pidof com.xgimi.systemui); if [ -n "$p" ]; then test "${p#* }" = "$p"; kill -9 "$p"; fi'
 lines += ['sigv "$D/'+item['file']+'"; OURS_'+str(index)+'=${REPLY#*:*:}',
  'nsigv '+q(target)+'; if [ "${REPLY#*:*:}" != "$OURS_'+str(index)+'" ]; then',
  '  nsenter -t "$zyg" -m -- mount -o bind "$D/'+item['file']+'" '+q(target),
  'fi',
  'needs_restart=0',
  'if [ "$NATIVE_'+str(index)+'" != '+q(digest)+' ]; then needs_restart=1; fi']
 if pkg=='com.android.newsettings':
  lines += ['if [ "$OLD_SKIN" != "$D/skin.apk" ]; then needs_restart=1; fi']
 lines += ['for p in $(pidof '+q(pkg)+' || true); do',
  '  if [ "$(nsenter -t "$p" -m -- stat -c %d:%i '+q(target)+')" != "$OURS_'+str(index)+'" ]; then needs_restart=1; fi','done',
  'if [ "$needs_restart" = 1 ]; then',
  '  case "$NL$PSN$NL" in *"${NL}'+pkg+'${NL}"*|*"${NL}'+pkg+':"*) '+restart+' ;; esac',
  'fi',
  'up; echo "t_native_'+str(index)+'=$UPN"']
# After all restarts finished: one namespace stat for every native target instead of one per target.
lines += ['wait',
 'NSV=$(nsenter -t "$zyg" -m -- stat -c "%n %d:%i" '+' '.join(q(m['originals'][i['target']]['path']) for i in native)+')',
 'eval "$(echo "$NSV" | mkvars NSV_)"']
for index,item in enumerate(native):
 key=re.sub(r'[^A-Za-z0-9]','_',m['originals'][item['target']]['path'])
 lines += ['test "${NSV_'+key+':-}" = "$OURS_'+str(index)+'"']
lines += ['up; S_NR=$UPN; echo "native_ready_uptime=$S_NR boot_completed=$(getprop sys.boot_completed)"']
for index,item in enumerate(native):
 target=item['target'];path=m['originals'][target]['path']
 if target=='com.xgimi.systemui':
  lines += ['n=0; while [ -z "$(pidof com.xgimi.systemui)" ] && [ "$n" -lt 20 ]; do sleep 1; n=$((n+1)); done', 'test -n "$(pidof com.xgimi.systemui)"']
 lines += ['for p in $(pidof '+q(target)+' || true); do',
           '  test "$(nsenter -t "$p" -m -- stat -c %d:%i '+q(path)+')" = "$OURS_'+str(index)+'"','done',
           'up; echo "t_post_'+item['file'].split('-')[0]+'=$UPN"']
# Validate all remaining RRO targets and overlay payloads before changing any idmaps.
lines += ['up; echo "t_orig_start=$UPN"']
for target,original in m['originals'].items():
 if any(item['target']==target for item in native): continue
 lines += ['rt_hash '+q(original['path'])+'; test "$RH" = '+q(original['sha256'])]
lines += ['up; echo "t_orig_done=$UPN"']
# Overlay APK paths come from the directory layout (/data/app/~~x/<package>-y/base.apk): a shell glob instead of
# `cmd package list` (a JVM start, ~0.35 s). If the layout gives a wrong path or hash, the package manager is asked.
OVERLAY_BLOCK=r'''ov_index() {
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
  for pk in @PKGS@; do eval "p=\${OV_${pk//[!A-Za-z0-9]/_}:-}"; k=${p#/}; OVFILES="$OVFILES $p /data/resource-cache/${k//\//@}@idmap"; done
  eval "$(stat -c "$SIGF" $OVFILES 2>/dev/null | mkvars SG_)"
}
ov_check() {
@CHECKS@
}
ov_cache_load() { if [ -f "$OVC" ]; then eval "$(awk '{k=$1; gsub(/[^A-Za-z0-9]/,"_",k); print "OV_" k "=\x27" $2 "\x27"}' "$OVC")"; fi; }
ov_cache_save() { for pk in @PKGS@; do eval "p=\${OV_${pk//[!A-Za-z0-9]/_}:-}"; echo "$pk $p"; done > "$OVC.new" && mv "$OVC.new" "$OVC"; chmod 600 "$OVC"; }
OVC=$ROOTDIR/ovpaths
OV_SOURCE=cache
ov_cache_load; ov_load; up; echo "t_ovload=$UPN"
if ! ov_check; then
  OV_SOURCE=glob; ov_index; ov_load
  if ! ov_check; then OV_SOURCE=pm; ov_index_pm; ov_load; ov_check; fi
  ov_cache_save
fi
echo "ov_source=$OV_SOURCE"'''
checks=[]
for item in m['overlays']:
 pk='OV_'+re.sub(r'[^A-Za-z0-9]','_',item['package'])
 checks.append('  eval "OVERLAY=\\${'+pk+':-}"; test -f "$OVERLAY" || return 1; check_hash2 "$OVERLAY" '+q(m['files'][item['file']])+' || return 1')
lines += [OVERLAY_BLOCK.replace('@PKGS@',' '.join(item['package'] for item in m['overlays'])).replace('@CHECKS@','\n'.join(checks))]
lines += ['up; echo "t_pkgs=$UPN"']
lines += ['up; S_OV=$UPN; echo "overlays_validated_uptime=$S_OV"',
 r'''ENABLED=$(cmd overlay list | awk '$1=="[x]"{print $2}')''','up; echo "t_enabled=$UPN"','IDMAP_DONE=0; IDMAP_SKIPPED=0']
for item in m['overlays']:
 tpath=m['originals'][item['target']]['path']; pkg=item['package']
 pk='OV_'+re.sub(r'[^A-Za-z0-9]','_',pkg)
 lines += ['eval "OVERLAY=\\${'+pk+'}"',
  'k=${OVERLAY#/}; CACHE=/data/resource-cache/${k//\\//@}@idmap',
  'sigv "$OVERLAY"; OSIG=$REPLY; sigv '+q(tpath)+'; OSIG="$OSIG|$REPLY"',
  'CK="idmap:${CACHE}_$OSIG"; eval "want=\\${HC_${CK//[!A-Za-z0-9]/_}:-}"',
  'sigv "$CACHE"; have=$REPLY',
  'case "$NL$ENABLED$NL" in *"${NL}'+pkg+'${NL}"*) EN=1;; *) EN=0;; esac',
  'if [ -n "$want" ] && [ "$want" = "$have" ] && [ "$EN" = 1 ]; then IDMAP_SKIPPED=$((IDMAP_SKIPPED+1)); else',
  '  idmap2 create --target-apk-path '+q(tpath)+' --overlay-apk-path "$OVERLAY" --idmap-path "$CACHE" --policy public --ignore-overlayable',
  '  chown system:system "$CACHE"','  chmod 644 "$CACHE"',
  '  cache_put "idmap:$CACHE" "$OSIG" "$(stat -c %s:%Y:%d:%i "$CACHE")"',
  '  cmd overlay enable --user 0 '+q(pkg),'  IDMAP_DONE=$((IDMAP_DONE+1))','fi']
# The OEM memory policy keeps this helper alive; a cloud update may replace the file, so check it on every run.
POLICY_BLOCK=r'''POLICY=/data/local/xgimi_gmui_manager/sys_pkg_adj.json
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
echo "restore=ok"'''
lines += ['up; echo "t_ov_loop=$UPN"']
lines += [POLICY_BLOCK]
script='\n'.join(lines)+'\n';(H/'apply.sh').write_text(script,encoding='utf-8',newline='\n')
digest=hashlib.sha256(script.encode('utf-8')).hexdigest()
skin_lines=lines[:lines.index('zyg=$(pidof zygote)')]
skin_lines=[line.replace('/system/bin/sh $D/apply.sh','/system/bin/sh $D/skin.sh') for line in skin_lines]
skin_lines += ['check_hash() { actual=$(sha256sum "$1" | cut -d " " -f 1); test "$actual" = "$2"; }',
 'check_hash "$D/skin.apk" '+q(m['files']['skin.apk']),
 'if [ "$(getprop persist.sys.xgimi.themeV2.url)" != "$D/skin.apk" ]; then',
 '  setprop persist.sys.xgimi.themeV2.url "$D/skin.apk"',
 '  am force-stop com.android.newsettings',
 'fi', 'test "$(getprop persist.sys.xgimi.themeV2.url)" = "$D/skin.apk"','echo "skin_restore=ok"']
skin_script='\n'.join(skin_lines)+'\n';(H/'skin.sh').write_text(skin_script,encoding='utf-8',newline='\n')
skin_digest=hashlib.sha256(skin_script.encode()).hexdigest()
constants=H/'app/src/com/beam/russifier/boot/RestoreConfig.java'
constants.write_text('package com.beam.russifier.boot;\nfinal class RestoreConfig {\n'
 'static final String FINGERPRINT = '+json.dumps(m['fingerprint'])+';\n'
 'static final String SCRIPT = '+json.dumps(D+'/apply.sh')+';\n'
 'static final String SHA256 = '+json.dumps(digest)+';\n'
 'static final String SKIN_SCRIPT = '+json.dumps(D+'/skin.sh')+';\n'
 'static final String SKIN_SHA256 = '+json.dumps(skin_digest)+';\n'
 'static final String SKIN = '+json.dumps(D+'/skin.apk')+';\n'
 'static final String DIRECTORY = '+json.dumps(D)+';\n}\n',encoding='utf-8')
generation={'directory':D,'files':{'apply.sh':digest,'skin.sh':skin_digest,
 'skin.apk':m['files']['skin.apk'],**{item['file']:m['files'][item['file']] for item in native}}}
(H/'generation.json').write_text(json.dumps(generation,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'scriptSha256':digest,'nativePatches':len(native),'overlays':len(m['overlays']),'directory':D}))
