"""Package a .NET Framework GUI beside an immutable, verified russifier ZIP."""
from pathlib import Path
import hashlib, json, shutil, subprocess, tempfile, zipfile

ROOT = Path(__file__).resolve().parents[1]
VERSION = json.loads((ROOT/'russifier/manifest.json').read_text(encoding='utf-8'))['version']
UI_VERSION = '1.16.0'
if 'перевод '+VERSION+' · установщик '+UI_VERSION.removesuffix('.0') not in (ROOT/'installer-ui/Program.cs').read_text(encoding='utf-8'):
    raise RuntimeError('GUI version label differs from manifest/build version')
archive = ROOT / 'dist' / f'beam-russifier-play6-v{VERSION}.zip'
expected = archive.with_name(archive.name+'.sha256').read_text(encoding='ascii').split()[0]
assert hashlib.sha256(archive.read_bytes()).hexdigest() == expected
destination = ROOT / 'dist' / f'XGIMI-Russifier-{VERSION}-Windows-Setup1.16'
if destination.exists():
    raise RuntimeError('Output already exists; preserve it or use a new package version')
with tempfile.TemporaryDirectory(prefix='xgimi-ui-') as directory:
    work = Path(directory)
    shutil.copyfile(ROOT/'installer-ui/Program.cs',work/'Program.cs')
    subprocess.run(['C:/Windows/Microsoft.NET/Framework64/v4.0.30319/csc.exe', '/nologo', '/target:winexe', '/out:'+str(work/'XgimiInstaller.exe'), '/reference:System.Windows.Forms.dll', '/reference:System.Drawing.dll', '/reference:System.Web.Extensions.dll', str(work/'Program.cs')],check=True)
    destination.mkdir()
    shutil.copyfile(work/'XgimiInstaller.exe',destination/'XgimiInstaller.exe')
with zipfile.ZipFile(archive) as source:
    for entry in source.infolist():
        path = Path(entry.filename)
        if path.parts[0] != 'Beam-Russifier-Play6' or '..' in path.parts or path.is_absolute():
            raise RuntimeError('Unsafe release member')
        target = destination/'kit'/Path(*path.parts[1:])
        if entry.is_dir():
            target.mkdir(parents=True,exist_ok=True)
        else:
            target.parent.mkdir(parents=True,exist_ok=True)
            target.write_bytes(source.read(entry))
(destination/'XgimiInstaller.exe.config').write_text('''<?xml version="1.0" encoding="utf-8"?>
<configuration><startup><supportedRuntime version="v4.0" sku=".NETFramework,Version=v4.8"/></startup></configuration>
''',encoding='utf-8')
shutil.copyfile(ROOT/'installer-ui/START-HERE.txt',destination/'START-HERE.txt')
# All runtime scripts come from the verified ZIP, never from a different tree.
shutil.copyfile(ROOT/'installer-ui/PREPARATION.md',destination/'PREPARATION.md')
files = {p.relative_to(destination).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in destination.rglob('*') if p.is_file()}
(destination/'package.json').write_text(json.dumps({'uiVersion':UI_VERSION,'translationVersion':VERSION,'sourceZipSha256':expected,'files':files},indent=2)+'\n',encoding='utf-8')
packed = shutil.make_archive(str(destination),'zip',root_dir=destination.parent,base_dir=destination.name)
from test_portable import check
check(Path(packed))
digest = hashlib.sha256(Path(packed).read_bytes()).hexdigest()
Path(packed+'.sha256').write_text(digest+'  '+Path(packed).name+'\n',encoding='ascii')
print(json.dumps({'folder':str(destination),'zip':packed,'sha256':digest},ensure_ascii=True))
