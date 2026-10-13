"""Build the preserved settings RRO with five additional display labels."""
from pathlib import Path
import shutil,subprocess,os
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'investigation/translation-gaps-2026-10-09/settings'
WORK=Path(r'C:/android/settings-gaps-recipe')
WORK.mkdir(exist_ok=True)
shutil.copytree(SOURCE/'res',WORK/'res',dirs_exist_ok=True)
shutil.copyfile(SOURCE/'AndroidManifest.xml',WORK/'AndroidManifest.xml')
shutil.copyfile(ROOT/'russifier/payload/panel.apk',WORK/'target.apk')
BT=Path(r'C:/android/sdk/build-tools/34.0.0')
def run(*args):subprocess.run(list(map(str,args)),check=True,env={**os.environ,'JAVA_HOME':r'C:/android/jdk'})
run(BT/'aapt2.exe','compile','--dir',WORK/'res','-o',WORK/'compiled.zip')
run(BT/'aapt2.exe','link','-o',WORK/'unsigned.apk','-I',r'C:/android/sdk/platforms/android-34/android.jar','-I',WORK/'target.apk','--manifest',WORK/'AndroidManifest.xml','--package-id','0x80','--no-resource-deduping','--no-resource-removal',WORK/'compiled.zip')
run(BT/'zipalign.exe','-f','4',WORK/'unsigned.apk',WORK/'aligned.apk')
run(BT/'apksigner.bat','sign','--ks',str(Path.home()/'.android/debug.keystore'),'--ks-pass','pass:android','--key-pass','pass:android','--out',WORK/'settings.apk',WORK/'aligned.apk')
run(BT/'apksigner.bat','verify',WORK/'settings.apk')
shutil.copyfile(WORK/'settings.apk',ROOT/'russifier/payload/settings.apk')
