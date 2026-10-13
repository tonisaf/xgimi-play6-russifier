"""Reboot, then observe only: the PC does not trigger restoration."""
from pathlib import Path
import subprocess,time,json,sys
H=Path(__file__).resolve().parent;ROOT=H.parents[1]
A=[str(ROOT/'russifier/tools/adb.exe'),'-P','5038','-s','192.168.1.100:5555']
def read(script):
 p=subprocess.run(A+['shell',script],capture_output=True,timeout=8)
 return p.returncode,p.stdout.decode('utf-8','replace')
_,before=read('cat /proc/sys/kernel/random/boot_id')
before=before.strip();assert len(before)==36
label=sys.argv[1] if len(sys.argv)>1 else 'boot1'
(H/(label+'-before.json')).write_text(json.dumps({'boot':before,'time':time.time()}))
try:subprocess.run(A+['reboot'],timeout=10,check=True)
except subprocess.TimeoutExpired:pass
begin=time.monotonic();print('Reboot requested. Read-only monitoring.',flush=True)
for i in range(36):
 time.sleep(5)
 try:
  code,output=read('cat /proc/sys/kernel/random/boot_id; cat /data/local/beam-russifier-boot/last.log; cat /data/local/beam-russifier-boot/done; getprop sys.boot_completed; getprop vendor.xgimi.system.debug.cmd; getprop persist.xgimi.mem_optimise.enable')
  if code or not output:
   subprocess.run(A[:3]+['connect','192.168.1.100:5555'],capture_output=True,timeout=5)
   continue
  boot=output.splitlines()[0].strip()
  if boot!=before and 'boot='+boot in output and 'restore=ok' in output:
   (H/(label+'-proof.txt')).write_text(output,encoding='utf-8')
   print('Autorestore detected monitor_seconds='+str(round(time.monotonic()-begin))+'\n'+output,flush=True)
   _,log=read('logcat -d -b all -v monotonic')
   (H/(label+'-logcat.txt')).write_text(log,encoding='utf-8')
   _,acc=read('dumpsys accessibility')
   (H/(label+'-accessibility.txt')).write_text(acc,encoding='utf-8')
   break
  if i%6==0:print('Waiting monitor_seconds='+str(round(time.monotonic()-begin)),flush=True)
 except subprocess.TimeoutExpired:pass
else:raise SystemExit('Autorestore not observed within bounded monitoring')
