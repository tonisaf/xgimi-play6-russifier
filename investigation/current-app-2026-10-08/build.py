from pathlib import Path
import json,os,re,shutil,subprocess,hashlib,xml.etree.ElementTree as E
H=Path(__file__).resolve().parent;ROOT=H.parents[1];W=Path(os.environ['TEMP'])/'beam-manager-rro';W.mkdir(exist_ok=True)
source=json.loads((H/'chinese-strings.json').read_text(encoding='utf-8'));translations=json.loads((H/'translations.json').read_text(encoding='utf-8'))
strings=E.Element('resources');mapping=E.Element('overlay')
for k,v in translations.items():
 old=source[k];assert re.findall(r'%\d*\$?[sd]',old)==re.findall(r'%\d*\$?[sd]',v),k
 node=E.SubElement(strings,'string',{'name':k});node.text=v
 E.SubElement(mapping,'item',{'target':'string/'+k,'value':'@string/'+k})
for elem,name in [(strings,'values/strings.xml'),(mapping,'xml/overlays.xml')]:
 p=W/'res'/name;p.parent.mkdir(exist_ok=True,parents=True);E.indent(elem);E.ElementTree(elem).write(p,encoding='utf-8',xml_declaration=True)
shutil.copy(H/'manager-original.apk',W/'target.apk')
manifest='<manifest xmlns:android="http://schemas.android.com/apk/res/android" package="com.beam.translation.manager" android:versionCode="1" android:versionName="1.0"><uses-sdk android:minSdkVersion="30" android:targetSdkVersion="30"/><application android:hasCode="false" android:label="Beam: обслуживание XGIMI"/><overlay android:targetPackage="com.xgimi.manager" android:targetName="BeamTranslation" android:resourcesMap="@xml/overlays" android:isStatic="false" android:priority="999"/></manifest>'
(W/'AndroidManifest.xml').write_text(manifest,encoding='utf-8');bt=Path(r'C:\android\sdk\build-tools\34.0.0')
def run(*args):subprocess.run(list(map(str,args)),check=True,env={**os.environ,'JAVA_HOME':r'C:\android\jdk'})
run(bt/'aapt2.exe','compile','--dir',W/'res','-o',W/'compiled.zip');run(bt/'aapt2.exe','link','-o',W/'unsigned.apk','-I',r'C:\android\sdk\platforms\android-34\android.jar','-I',W/'target.apk','--manifest',W/'AndroidManifest.xml','--package-id','0x80','--no-resource-deduping','--no-resource-removal',W/'compiled.zip')
run(bt/'zipalign.exe','-f','4',W/'unsigned.apk',W/'aligned.apk');run(bt/'apksigner.bat','sign','--ks',r'C:\Users\USER\.android\debug.keystore','--ks-pass','pass:android','--key-pass','pass:android','--out',H/'manager.apk',W/'aligned.apk');run(bt/'apksigner.bat','verify',H/'manager.apk')
shutil.copytree(W/'res',H/'rro/res',dirs_exist_ok=True);shutil.copy(W/'AndroidManifest.xml',H/'rro/AndroidManifest.xml');shutil.copy(H/'manager.apk',ROOT/'russifier/payload/manager.apk')
p=ROOT/'russifier/manifest.json';m=json.loads(p.read_text(encoding='utf-8'));m['version']='1.11.0';m['originals']['com.xgimi.manager']={'path':'/vendor/priv-app/XgimiManager_release838/XgimiManager_release838.apk','sha256':hashlib.sha256((H/'manager-original.apk').read_bytes()).hexdigest()};m['files']['manager.apk']=hashlib.sha256((H/'manager.apk').read_bytes()).hexdigest();m['overlays']=[i for i in m['overlays'] if i['target']!='com.xgimi.manager']+[{'package':'com.beam.translation.manager','target':'com.xgimi.manager','file':'manager.apk'}];m['resourceChecks']['com.xgimi.manager']=translations;p.write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
report={'strings':len(translations),'original':m['originals']['com.xgimi.manager'],'rroSha256':m['files']['manager.apk'],'dexChanged':False,'stringChecks':sum(map(len,m['resourceChecks'].values()))};(H/'build.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report,indent=2))
