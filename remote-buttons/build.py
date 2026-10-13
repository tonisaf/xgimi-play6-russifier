"""Build an isolated diagnostic APK; does not deploy or change the russifier payload."""
from pathlib import Path
import os,subprocess,tempfile,zipfile,hashlib,shutil,json,argparse,xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[1];APP=Path(__file__).resolve().parent/'app'
SDK=Path(os.environ.get('ANDROID_HOME','C:/android/sdk'));J=Path(os.environ.get('JAVA_HOME','C:/android/jdk'))/'bin';BT=SDK/'build-tools/34.0.0';AJ=SDK/'platforms/android-34/android.jar'
key=ROOT/'.local/boot-signing/key.p12';password=key.with_name('password.txt')
if not key.is_file() or not password.is_file():raise RuntimeError('Local signing key not configured: .local/boot-signing/key.p12 + password.txt')
parser=argparse.ArgumentParser();parser.add_argument('--stage',action='store_true',help='Include verified APK in the next russifier release');args=parser.parse_args()
manifest=ET.parse(APP/'AndroidManifest.xml').getroot();android='{http://schemas.android.com/apk/res/android}'
version=manifest.get(android+'versionName');code=manifest.get(android+'versionCode')
out=ROOT/'dist'/('xgimi-remote-buttons-'+version+'.apk')
out.parent.mkdir(parents=True,exist_ok=True)
if out.exists() or out.with_suffix('.apk.sha256').exists():raise RuntimeError('Module version already built; preserve it and bump versionCode/versionName')
def run(*args):subprocess.run(list(map(str,args)),check=True)
with tempfile.TemporaryDirectory(prefix='beam-remote-') as tmp:
 w=Path(tmp);shutil.copytree(APP,w/'app')
 for p in (w/'app').rglob('*'):
  if p.suffix in ('.xml','.java'):p.write_text(p.read_text(encoding='utf-8-sig'),encoding='utf-8')
 run(BT/'aapt2.exe','compile','--dir',w/'app/res','-o',w/'resources.zip')
 run(BT/'aapt2.exe','link','-o',w/'base.apk','--manifest',w/'app/AndroidManifest.xml','-I',AJ,w/'resources.zip')
 (w/'classes').mkdir();(w/'dex').mkdir()
 run(J/'javac.exe','-encoding','UTF-8','-source','8','-target','8','-cp',AJ,'-d',w/'classes',*sorted((w/'app/src').rglob('*.java')))
 run(J/'java.exe','-cp',BT/'lib/d8.jar','com.android.tools.r8.D8','--min-api','30','--lib',AJ,'--output',w/'dex',*sorted((w/'classes').rglob('*.class')))
 with zipfile.ZipFile(w/'base.apk') as src,zipfile.ZipFile(w/'unsigned.apk','w') as dst:
  for info in src.infolist():dst.writestr(info,src.read(info.filename))
  dst.writestr('classes.dex',(w/'dex/classes.dex').read_bytes())
 run(BT/'zipalign.exe','-f','4',w/'unsigned.apk',w/'aligned.apk')
 signed=w/'signed.apk'
 run(J/'java.exe','-jar',BT/'lib/apksigner.jar','sign','--ks',key,'--ks-key-alias','russifier','--ks-pass','file:'+str(password),'--out',signed,w/'aligned.apk')
 run(J/'java.exe','-jar',BT/'lib/apksigner.jar','verify',signed)
 with out.open('xb') as target:target.write(signed.read_bytes())
 digest=hashlib.sha256(out.read_bytes()).hexdigest()
 with out.with_suffix('.apk.sha256').open('x',encoding='ascii') as target:target.write(digest+'  '+out.name+'\n')
 if args.stage:
  path=ROOT/'russifier/manifest.json';data=json.loads(path.read_text(encoding='utf-8'))
  shutil.copyfile(out,ROOT/'russifier/payload/remote-buttons.apk')
  data['remoteModule']={'package':manifest.get('package'),'file':'remote-buttons.apk','version':version,'versionCode':int(code),'sha256':digest}
  path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print(out)
