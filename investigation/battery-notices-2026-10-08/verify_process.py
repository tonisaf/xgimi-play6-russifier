from pathlib import Path
from types import SimpleNamespace
import sys
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'russifier'))
from installer import Installer,MANIFEST,q
r=Installer(SimpleNamespace(device='192.168.1.100:5555'))
print(r.root('p=$(pidof com.xgimi.systemui)\ntest -n "$p"\necho process=$p\nhash=$(nsenter -t "$p" -m -- sha256sum /system/priv-app/SystemUI_release_838/SystemUI_release_838.apk | cut -d " " -f 1)\necho hash=$hash\ntest "$hash" = '+q(MANIFEST['files']['systemui-native.apk']),'verify-systemui-process'))
