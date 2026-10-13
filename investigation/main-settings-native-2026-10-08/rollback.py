from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'system-access-2026-10-07'))
from root_run import run
if __name__=='__main__':
 sys.stdout.reconfigure(encoding='utf-8')
 result=run('cmd overlay disable --user 0 com.beam.translation.settings\ncmd overlay dump com.beam.translation.settings','settings-rro-disable')
 print(result['exit'],result['log']['out'])
