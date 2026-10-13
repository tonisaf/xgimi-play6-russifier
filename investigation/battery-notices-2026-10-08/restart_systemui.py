from pathlib import Path
from types import SimpleNamespace
import sys,time
H=Path(__file__).resolve().parent;ROOT=H.parents[1];sys.path.insert(0,str(ROOT/'russifier'))
from installer import Installer
r=Installer(SimpleNamespace(device='192.168.1.100:5555'))
print(r.root(r'''p=$(pidof com.xgimi.systemui)
test -n "$p"
test "${p#* }" = "$p"
echo old_pid=$p
nsenter -t "$p" -m -- sha256sum /system/priv-app/SystemUI_release_838/SystemUI_release_838.apk
test "$(tr '\000' '\n' < /proc/$p/cmdline | head -1)" = com.xgimi.systemui
kill -9 "$p"
''','restart-oem-systemui'))
time.sleep(3)
print('New PID:',r.shell('pidof com.xgimi.systemui'))
