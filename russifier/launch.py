from pathlib import Path
import sys
if hasattr(sys.stdout,'reconfigure'): sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr,'reconfigure'): sys.stderr.reconfigure(encoding='utf-8')
sys.path.insert(0,str(Path(__file__).resolve().parent))
if len(sys.argv)>1 and sys.argv[1] in ('install-remote','enable-remote','disable-remote','recover-remote'):
    from remote_setup import main
elif len(sys.argv)>1 and sys.argv[1] in ('list-launchers','restore-launchers'):
    from beam_setup import launcher_cli as main
elif len(sys.argv)>1 and sys.argv[1] in ('prepare','prepare-install','undo-prepare'):
    from preparation import main
elif len(sys.argv)>1 and sys.argv[1] in ('install-autostart','remove-autostart','recover-autostart'):
    from boot_setup import main
elif len(sys.argv)>1 and sys.argv[1]=='update-boot':
    sys.argv.pop(1)
    from boot_update import main
elif len(sys.argv)>1 and sys.argv[1]=='finish-setup':
    sys.argv.pop(1)
    from finish_setup import main
else:
    from installer import main
raise SystemExit(main())
