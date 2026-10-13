"""Explicitly download the pinned upstream build tool; no APKs are changed."""
from pathlib import Path
import hashlib,json,os,tempfile,urllib.request

ROOT=Path(__file__).resolve().parents[1]
info=json.loads((ROOT/'remote-buttons/tools.json').read_text(encoding='utf-8'))
destination=ROOT/'.local/build-tools'/('apktool-'+info['apktoolVersion']+'.jar')
destination.parent.mkdir(parents=True,exist_ok=True)
if destination.exists():
    if hashlib.sha256(destination.read_bytes()).hexdigest()!=info['apktoolSha256']:
        raise RuntimeError('Existing APKTool has an unexpected SHA256')
else:
    fd,name=tempfile.mkstemp(dir=destination.parent)
    try:
        with os.fdopen(fd,'wb') as output,urllib.request.urlopen(info['apktoolUrl'],timeout=60) as response:
            while block:=response.read(1024*1024): output.write(block)
        if hashlib.sha256(Path(name).read_bytes()).hexdigest()!=info['apktoolSha256']:
            raise RuntimeError('Downloaded APKTool SHA256 mismatch')
        os.link(name,destination)
    finally: Path(name).unlink(missing_ok=True)
print(destination)
