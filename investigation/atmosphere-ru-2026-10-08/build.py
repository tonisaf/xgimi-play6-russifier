from pathlib import Path
import json,xml.etree.ElementTree as E,subprocess,os,shutil
out=Path(__file__).resolve().parent
p=Path(os.environ['TEMP'])/'beam-atmosphere-rro';p.mkdir(exist_ok=True)
shutil.copyfile(out/'translations.json',p/'translations.json')
bt=Path(r'C:\android\sdk\build-tools\34.0.0')
data=json.loads((p/'translations.json').read_text(encoding='utf-8'))
for folder in ['values','values-en','values-zh-rCN','values-ru','xml']:(p/'res'/folder).mkdir(parents=True,exist_ok=True)
r=E.Element('resources')
for k,v in data['strings'].items():E.SubElement(r,'string',{'name':k,'formatted':'false'}).text=v.replace(chr(39),chr(92)+chr(39)).replace(chr(34),chr(92)+chr(34))
for k,items in data['arrays'].items():
 a=E.SubElement(r,'string-array',{'name':k})
 for item in items:E.SubElement(a,'item').text=item
E.indent(r)
for folder in ['values','values-en','values-zh-rCN','values-ru']:E.ElementTree(r).write(p/'res'/folder/'strings.xml',encoding='utf-8',xml_declaration=True)
m=E.Element('overlay')
for kind,group in [('string','strings'),('array','arrays')]:
 for k in data[group]:E.SubElement(m,'item',{'target':kind+'/'+k,'value':'@'+kind+'/'+k})
E.indent(m);E.ElementTree(m).write(p/'res/xml/overlays.xml',encoding='utf-8',xml_declaration=True)
(p/'AndroidManifest.xml').write_text('<manifest xmlns:android="http://schemas.android.com/apk/res/android" package="com.beam.translation.atmosphere" android:versionCode="1" android:versionName="1.0"><uses-sdk android:minSdkVersion="30" android:targetSdkVersion="30"/><application android:hasCode="false" android:label="Beam: перевод заставок"/><overlay android:targetPackage="com.xgimi.atmosphere" android:targetName="BeamTranslation" android:resourcesMap="@xml/overlays" android:isStatic="false" android:priority="999"/></manifest>',encoding='utf-8')
def run(*a):subprocess.run(list(map(str,a)),check=True,env={**os.environ,'JAVA_HOME':r'C:\android\jdk'})
run(bt/'aapt2.exe','compile','--dir',p/'res','-o',p/'compiled.zip')
run(bt/'aapt2.exe','link','-o',p/'unsigned.apk','-I',r'C:\android\sdk\platforms\android-34\android.jar','--manifest',p/'AndroidManifest.xml','--package-id','0x80','--no-resource-deduping','--no-resource-removal',p/'compiled.zip')
run(bt/'zipalign.exe','-f','4',p/'unsigned.apk',p/'aligned.apk')
run(bt/'apksigner.bat','sign','--ks',r'C:\Users\USER\.android\debug.keystore','--ks-pass','pass:android','--key-pass','pass:android','--out',p/'beam-atmosphere-ru.apk',p/'aligned.apk')
run(bt/'apksigner.bat','verify',p/'beam-atmosphere-ru.apk')

shutil.copyfile(p/'beam-atmosphere-ru.apk',out/'beam-atmosphere-ru.apk')
