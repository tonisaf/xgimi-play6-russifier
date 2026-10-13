"""Stage matching immutable scripts and native payload before updating the helper."""
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'russifier'))
from boot_update import main
if __name__=='__main__': main()
