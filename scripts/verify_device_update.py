"""Verify the shipped generation after helper completes; no reboot or UI navigation."""
from pathlib import Path
from types import SimpleNamespace
import argparse,json,sys,time
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'russifier'))
from installer import Installer,MANIFEST,q,sha,save
parser=argparse.ArgumentParser()
parser.add_argument('--device',required=True)
parser.add_argument('--update-log',type=Path,required=True)
args=parser.parse_args()
i=Installer(SimpleNamespace(device=args.device))
record=json.loads((args.update_log/'boot-update.json').read_text(encoding='utf-8'))
assert record['status']=='committed'
info=json.loads((ROOT/'investigation/bound-startup-2026-10-08/build-info.json').read_text(encoding='utf-8'))
assert record['generation']==info['directory']
assert record['newHelperSha256']==info['helperSha256']
directory=info['directory']
deadline=time.monotonic()+45
while True:
    done=i.command('shell','cat '+q(directory+'/done'),check=False).stdout.strip()
    command=i.shell('getprop vendor.xgimi.system.debug.cmd')
    if done and not command:break
    if time.monotonic()>=deadline:raise RuntimeError('Helper has not completed; root verification not started')
    time.sleep(2)
assert done.split()[-1]=='0',done
assert i.shell('getprop vendor.xgimi.system.debugserver')==''
log=i.shell('cat '+q(directory+'/last.log'))
assert 'restore=ok' in log,log
states=i.overlay_states()
assert len(states)==len(MANIFEST['overlays']) and all(s['enabled'] and 'STATE_ENABLED' in s['state'] for s in states.values())
old_services=set(record['oldServices'])
actual_services=set(i.shell('settings get secure enabled_accessibility_services').split(':'))
assert actual_services==old_services,(actual_services,old_services)
helper_path=i.shell('pm path com.beam.russifier.boot').removeprefix('package:')
assert i.shell('sha256sum '+q(helper_path)).split()[0]==info['helperSha256']
version=i.shell('dumpsys package com.beam.russifier.boot')
assert 'versionName='+MANIFEST['version'] in version
native=[{'target':'com.android.newsettings','file':'panel.apk'}]+MANIFEST['runtimePatches']
lines=['zyg=$(pidof zygote)','test -n "$zyg"']
for item in native:
    path=MANIFEST['originals'][item['target']]['path']
    lines += ['test "$(nsenter -t "$zyg" -m -- sha256sum '+q(path)+' | cut -d " " -f 1)" = '+q(MANIFEST['files'][item['file']]),
              'test "$(sha256sum '+q(path)+' | cut -d " " -f 1)" = '+q(MANIFEST['originals'][item['target']]['sha256'])]
for item in MANIFEST['overlays']:
    path=states[item['package']]['path']
    lines+=['test "$(sha256sum '+q(path)+' | cut -d " " -f 1)" = '+q(MANIFEST['files'][item['file']])]
photo=json.loads((ROOT/'investigation/photo-fixes-2026-10-12/build-report.json').read_text(encoding='utf-8'))
changes={**photo['systemui'],**photo['ambient']}
batch=json.loads((ROOT/'investigation/translation-batch1-2026-10-12/reviewed.json').read_text(encoding='utf-8'))
changes.update({r['resource'].removeprefix('string/'):r['proposed'] for r in batch if r['proposed']})
batch2=ROOT/'investigation/translation-batch2-2026-10-12/reviewed.json'
if batch2.exists() and MANIFEST['version'] in ('1.19.18','1.19.19','1.19.20'):
    changes.update({r['resource'].removeprefix('string/'):r['proposed'] for r in json.loads(batch2.read_text(encoding='utf-8')) if r['proposed']})
for number,versions in [(3,('1.19.19','1.19.20')),(4,('1.19.20',))]:
    if MANIFEST['version'] in versions:
        reviewed=ROOT/f'investigation/translation-batch{number}-2026-10-12/reviewed.json'
        changes.update({r['resource'].removeprefix('string/'):r['proposed'] for r in json.loads(reviewed.read_text(encoding='utf-8')) if r['proposed']})
for key,value in changes.items():
    lines+=['actual=$(cmd overlay lookup com.xgimi.systemui '+q('com.xgimi.systemui:string/'+key)+" | tr -d '\\r')",
            'test "$actual" = '+q(value)+' || { echo '+q('FAILED '+key)+'; exit 31; }']
lines+=['echo native_hashes=5','echo original_apks_unchanged=5','echo overlay_hashes='+str(len(states)),
        'echo exact_new_resource_values='+str(len(changes))]
proof=i.root('\n'.join(lines),'device-update-proof')
assert i.shell('getprop vendor.xgimi.system.debug.cmd')==''
assert i.shell('getprop vendor.xgimi.system.debugserver')==''
report={'version':MANIFEST['version'],'generation':directory,'updateLog':str(args.update_log.resolve()),'status':'verified',
        'helperExit':0,'helperHashVerified':True,'nativeHashes':len(native),'originalApksUnchanged':len(native),
        'overlaysEnabledAndHashes':len(states),'newResourceValuesVerified':len(changes),'allAccessibilityServicesPreserved':True,
        'helperPid':i.shell('pidof com.beam.russifier.boot'),'systemuiPid':i.shell('pidof com.xgimi.systemui'),
        'proof':proof,'helperApplyLog':log,'rebootPerformed':False,'screenVisualVerification':False,
        'verificationLog':str(i.logs)}
assert report['helperPid'] and report['systemuiPid']
save(args.update_log/'device-verification.json',report)
print(json.dumps({k:v for k,v in report.items() if k not in ('helperApplyLog','generation','updateLog','helperPid','systemuiPid')},ensure_ascii=False))
