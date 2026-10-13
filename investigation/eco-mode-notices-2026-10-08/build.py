from pathlib import Path
import shutil,subprocess,tempfile,os,json,re,hashlib,zipfile,xml.etree.ElementTree as E
OUT=Path(__file__).resolve().parent
SP=Path(r'C:\Users\USER\AppData\Local\Temp\claude\C--Users-USER-TileLauncher\4a103049-a7f5-4062-923c-147b4e6834ae\scratchpad')
BT=Path(r'C:\android\sdk\build-tools\34.0.0')
RRO=Path(tempfile.mkdtemp(prefix='beam-system-notices-'))
original={x.attrib['name']:''.join(x.itertext()) for x in E.parse(SP/'res6/systemui/res/values/strings.xml').getroot() if x.tag=='string'}
data=json.loads((OUT/'translations.json').read_text(encoding='utf-8'))
tokens=lambda v:re.findall(r'%%|%(?:\d+\$)?[-+0 #]*\d*(?:\.\d+)?[sdf]',v)
for key,value in data.items():
    assert key in original,key
    assert tokens(original[key])==tokens(value),(key,original[key],value)
previous=OUT.parent/'focus-popup-ru-2026-10-08/rro-systemui'
root=E.parse(previous/'res/values/strings.xml').getroot()
mapping=E.parse(previous/'res/xml/overlays.xml').getroot()
old_map=[dict(x.attrib) for x in mapping]
for key,value in data.items():
    E.SubElement(root,'string',{'name':key,'formatted':'false'}).text=value.replace('\n',r'\n')
    E.SubElement(mapping,'item',{'target':'string/'+key,'value':'@string/'+key})
assert [dict(x.attrib) for x in mapping][:4]==old_map
assert len({x.attrib['target'] for x in mapping})==len(mapping)
E.indent(root);E.indent(mapping)
for folder in ('values','values-zh-rCN','values-en','values-ru'):
    (RRO/'res'/folder).mkdir(parents=True,exist_ok=True)
    E.ElementTree(root).write(RRO/'res'/folder/'strings.xml',encoding='utf-8',xml_declaration=True)
(RRO/'res/drawable').mkdir();(RRO/'res/xml').mkdir()
shutil.copyfile(previous/'res/drawable/ak_progress_ru.xml',RRO/'res/drawable/ak_progress_ru.xml')
E.ElementTree(mapping).write(RRO/'res/xml/overlays.xml',encoding='utf-8',xml_declaration=True)
(RRO/'AndroidManifest.xml').write_text('<manifest xmlns:android="http://schemas.android.com/apk/res/android" package="com.beam.translation.systemui" android:versionCode="4" android:versionName="1.3"><uses-sdk android:minSdkVersion="30" android:targetSdkVersion="30"/><application android:hasCode="false" android:label="Beam: системные уведомления"/><overlay android:targetPackage="com.xgimi.systemui" android:targetName="BeamTranslation" android:resourcesMap="@xml/overlays" android:isStatic="false" android:priority="999"/></manifest>',encoding='utf-8')
def run(*args):subprocess.run(list(map(str,args)),check=True,env={**os.environ,'JAVA_HOME':r'C:\android\jdk'})
run(BT/'aapt2.exe','compile','--dir',RRO/'res','-o',RRO/'compiled.zip')
run(BT/'aapt2.exe','link','-o',RRO/'unsigned.apk','-I',r'C:\android\sdk\platforms\android-34\android.jar','--manifest',RRO/'AndroidManifest.xml','--package-id','0x80','--no-resource-deduping','--no-resource-removal',RRO/'compiled.zip')
run(BT/'zipalign.exe','-f','4',RRO/'unsigned.apk',RRO/'aligned.apk')
run(BT/'apksigner.bat','sign','--ks',r'C:\Users\USER\.android\debug.keystore','--ks-pass','pass:android','--key-pass','pass:android','--out',RRO/'beam-systemui-ru.apk',RRO/'aligned.apk')
run(BT/'apksigner.bat','verify',RRO/'beam-systemui-ru.apk')
with zipfile.ZipFile(RRO/'beam-systemui-ru.apk') as z:assert not any(n.endswith('.dex') for n in z.namelist())
shutil.copytree(RRO,OUT/'rro-systemui',dirs_exist_ok=True)
report={'newStrings':len(data),'totalMappings':len(mapping),'previousMappingsPreserved':True,'formatMarkersPreserved':True,'containsDex':False,'sha256':hashlib.sha256((RRO/'beam-systemui-ru.apk').read_bytes()).hexdigest()}
(OUT/'build.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report))
