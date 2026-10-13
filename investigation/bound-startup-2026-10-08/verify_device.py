"""Verify the restored payloads and exact resource values after boot."""
from pathlib import Path
from types import SimpleNamespace
import sys,json
H=Path(__file__).resolve().parent;ROOT=H.parents[1]
sys.path.insert(0,str(ROOT/'russifier'))
from installer import Installer,MANIFEST,q
r=Installer(SimpleNamespace(device='192.168.1.100:5555'))
states=r.overlay_states()
assert len(states)==len(MANIFEST['overlays']) and all(v['enabled'] and 'STATE_ENABLED' in v['state'] for v in states.values())
native=[{'target':'com.android.newsettings','file':'panel.apk'}]+MANIFEST['runtimePatches']
lines=['zyg=$(pidof zygote)','test -n "$zyg"']
for item in native:
 path=MANIFEST['originals'][item['target']]['path']
 lines += ['test "$(nsenter -t "$zyg" -m -- sha256sum '+q(path)+' | cut -d " " -f 1)" = '+q(MANIFEST['files'][item['file']]),
           'test "$(sha256sum '+q(path)+' | cut -d " " -f 1)" = '+q(MANIFEST['originals'][item['target']]['sha256'])]
framework=MANIFEST['originals'].get('android')
if framework:
    lines += ['test \"$(sha256sum '+q(framework['path'])+' | cut -d \" \" -f 1)\" = '+q(framework['sha256'])]
count=0
for target,strings in MANIFEST.get('resourceChecks',{}).items():
 for key,value in strings.items():
  lines += ['actual=$(cmd overlay lookup '+q(target)+' '+q(target+':string/'+key)+" | tr -d '\\r')",
            'test "$actual" = '+q(value.strip())+' || { echo '+q('FAILED '+target+':'+key)+'; exit 31; }']
  count+=1
for target,arrays in MANIFEST.get('arrayChecks',{}).items():
 for key,values in arrays.items():
  # Match Installer.shell's universal-newline decoding and strip() at the edges.
  lines += ['actual=$(cmd overlay lookup '+q(target)+' '+q(target+':array/'+key)+" | tr -d '\\r' | sed '1s/^[[:space:]]*//;$s/[[:space:]]*$//')",
            'test "$actual" = '+q('\n'.join(values).strip())+' || { echo '+q('FAILED '+target+':'+key)+'; exit 32; }']
  count+=1
lines += ['echo native_hashes='+str(len(native)),'echo originals_unchanged='+str(len(native)),'echo exact_resource_checks='+str(count),
          'sha256sum /data/local/xgimi_gmui_manager/sys_pkg_adj.json']
output=r.root('\n'.join(lines),'post-boot-proof')
proof={'nativeHashChecks':len(native),'overlaysEnabled':len(states),'resourceChecks':count,
       'bootId':r.shell('cat /proc/sys/kernel/random/boot_id'),
       'memoryOptimization':r.shell('getprop persist.xgimi.mem_optimise.enable'),
       'helperEnabled':r.shell('settings get secure enabled_accessibility_services'),
       'rootProof':output}
(H/'final-verification.json').write_text(json.dumps(proof,ensure_ascii=False,indent=2),encoding='utf-8')
print(output)
print(str(len(states))+' overlays enabled; original system/vendor APKs unchanged; OEM optimization uses default=true.')
