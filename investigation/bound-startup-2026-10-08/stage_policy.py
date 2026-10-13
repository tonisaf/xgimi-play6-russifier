"""Add only the experiment's process to the OEM's supported data policy."""
from pathlib import Path
from types import SimpleNamespace
import sys,json,hashlib
H=Path(__file__).resolve().parent;ROOT=H.parents[1]
sys.path.insert(0,str(ROOT/'russifier'))
from installer import Installer,q
r=Installer(SimpleNamespace(device='192.168.1.100:5555'))
raw=r.shell('cat /vendor/etc/xgimisys/sys_pkg_adj.json')
baseline=json.loads(raw)
assert not any(x['pkg']=='com.beam.russifier.boot' for x in baseline['oomadjLimit'])
data=json.loads(raw)
data['oomadjLimit'].append({'pkg':'com.beam.russifier.boot','start':200,'min':500,'max':800})
assert data['oomadjLimit'][:-1]==baseline['oomadjLimit']
assert all(data[k]==v for k,v in baseline.items() if k!='oomadjLimit')
out=H/'sys_pkg_adj-test.json'
out.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
digest=hashlib.sha256(out.read_bytes()).hexdigest()
(H/'policy-state.json').write_text(json.dumps({'previousExists':False,'sha256':digest,'baselineSha256':hashlib.sha256(raw.encode()).hexdigest()},indent=2))
r.command('push',out,'/data/local/tmp/beam-bound-adj.json')
print(r.root('''P=/data/local/xgimi_gmui_manager/sys_pkg_adj.json
test ! -e "$P"
test "$(sha256sum /data/local/tmp/beam-bound-adj.json | cut -d ' ' -f 1)" = '''+q(digest)+'''
cp /data/local/tmp/beam-bound-adj.json "$P.beam-stage"
chown system:system "$P.beam-stage"
chmod 600 "$P.beam-stage"
restorecon "$P.beam-stage"
mv "$P.beam-stage" "$P"
sha256sum "$P"
''','stage-oem-policy'))
r.shell('rm -f /data/local/tmp/beam-bound-adj.json')
a=r.shell('settings get secure enabled_accessibility_services')
a='' if a=='null' else a
service='com.beam.russifier.boot/com.beam.russifier.boot.StartupBridge'
if service not in a.split(':'):
 r.shell('settings put secure enabled_accessibility_services '+q(a+(':' if a else '')+service))
r.shell('pm enable com.beam.russifier.boot')
print('Targeted OEM policy staged; becomes active after system_server restart/reboot.')
