"""Disable this experiment before running the legacy INSTALL/ROLLBACK."""
from pathlib import Path
from types import SimpleNamespace
import sys,argparse
H=Path(__file__).resolve().parent;ROOT=H.parents[1]
sys.path.insert(0,str(ROOT/'russifier'))
from installer import Installer,q
parser=argparse.ArgumentParser()
parser.add_argument('--device',default='192.168.1.100:5555')
args=parser.parse_args();r=Installer(args)
# Remove only our component, leaving all other accessibility services enabled.
value=r.shell('settings get secure enabled_accessibility_services')
components=[] if value in ('','null') else value.split(':')
remaining=[c for c in components if not c.startswith('com.beam.russifier.boot/')]
if remaining!=components:
 if remaining:r.shell('settings put secure enabled_accessibility_services '+q(':'.join(remaining)))
 else:r.shell('settings delete secure enabled_accessibility_services')
if r.command('shell','pm path com.beam.russifier.boot',check=False).stdout.startswith('package:'):
 r.shell('pm disable-user --user 0 com.beam.russifier.boot')
 r.command('shell','cmd jobscheduler cancel -u 0 com.beam.russifier.boot 1400',check=False)
# This was created from the OEM default because the live override was absent.
# Refuse to delete it if an OEM update or another actor has since changed it.
print(r.root('''P=/data/local/xgimi_gmui_manager/sys_pkg_adj.json
if [ -f "$P" ]; then
  actual=$(sha256sum "$P" | cut -d ' ' -f 1)
  if [ "$actual" = 4959025327d1823b7d0e70ee63227bef5ff781a0b89177408e6a6a1cbf97da64 ]; then
    rm -f "$P"
    echo policy_removed=1
  else
    echo policy_changed_preserved=1
  fi
fi
''','disable-bound-policy'))
print('Autostart disabled. Current native mounts remain until reboot or legacy rollback.')
print('The OEM memory policy is reloaded at the next reboot.')
