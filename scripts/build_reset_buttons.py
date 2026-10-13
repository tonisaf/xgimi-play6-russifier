"""Translate factory reset buttons while retaining the Bluetooth separator."""
from pathlib import Path
import os,shutil,subprocess,json,hashlib,re,xml.etree.ElementTree as E
ROOT=Path(__file__).resolve().parents[1];work=Path('C:/android/factory-reset-buttons-20261010')
base=Path('C:/android/bluetooth-separator-20261010')
shutil.copytree(base/'res',work/'res',dirs_exist_ok=True)
for p in (work/'res').glob('values*/strings.xml'):
    tree=E.parse(p)
    translations={'data_restore_setting_title':'Сбросить','data_restore_text':'Сбросить','restore_factory_setting':'Сбросить','data_restore_cancel':'Отмена','dialog_cancel':'Отмена','btn_cancel':'Отмена','btn_cancle':'Отмена','cancel':'Отмена'}
    for name,value in translations.items():
        node=next((x for x in tree.getroot() if x.get('name')==name),None)
        if node is None:node=E.SubElement(tree.getroot(),'string',{'name':name})
        node.text=value
    tree.write(p,encoding='utf-8',xml_declaration=True)
text=(base/'AndroidManifest.xml').read_text(encoding='utf-8').replace('versionCode="27"','versionCode="28"').replace('versionName="1.19.7"','versionName="1.19.8"')
(work/'AndroidManifest.xml').write_text(text,encoding='utf-8')
bt=Path('C:/android/sdk/build-tools/34.0.0')
def run(*a):subprocess.run(list(map(str,a)),check=True,env={**os.environ,'JAVA_HOME':'C:/android/jdk'})
run(bt/'aapt2.exe','compile','--dir',work/'res','-o',work/'compiled.zip')
run(bt/'aapt2.exe','link','-o',work/'unsigned.apk','-I','C:/android/sdk/platforms/android-34/android.jar','-I','C:/android/panel-current-20261009-original.apk','--manifest',work/'AndroidManifest.xml','--package-id','0x80','--no-resource-deduping','--no-resource-removal',work/'compiled.zip')
run(bt/'zipalign.exe','-f','4',work/'unsigned.apk',work/'aligned.apk')
run(bt/'apksigner.bat','sign','--ks',Path.home()/'.android/debug.keystore','--ks-pass','pass:android','--key-pass','pass:android','--out',work/'settings.apk',work/'aligned.apk')
run(bt/'apksigner.bat','verify',work/'settings.apk')
dump=subprocess.check_output([str(bt/'aapt2.exe'),'dump','resources',str(work/'settings.apk')]).decode('utf-8')
assert '" подключено"' in dump
badging=subprocess.check_output([str(bt/'aapt2.exe'),'dump','badging',str(work/'settings.apk')]).decode('utf-8')
assert "versionCode='28'" in badging and "targetSdkVersion:'30'" in badging
shutil.copyfile(work/'settings.apk',ROOT/'russifier/payload/settings.apk')
p=ROOT/'russifier/manifest.json';m=json.loads(p.read_text(encoding='utf-8'))
m['version']='1.19.8';m['files']['settings.apk']=hashlib.sha256((work/'settings.apk').read_bytes()).hexdigest()
m['resourceChecks']['com.android.newsettings'].update(translations)
p.write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Factory reset button resources compiled; Bluetooth separator preserved')
