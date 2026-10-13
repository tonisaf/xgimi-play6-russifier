from pathlib import Path
import json,xml.etree.ElementTree as E,subprocess,os,hashlib,re,zipfile,shutil
OUT=Path(__file__).resolve().parent
SP=Path(r'C:\Users\USER\AppData\Local\Temp\claude\C--Users-USER-TileLauncher\4a103049-a7f5-4062-923c-147b4e6834ae\scratchpad')
BT=Path(r'C:\android\sdk\build-tools\34.0.0')
data=json.loads((OUT/'translations.json').read_text(encoding='utf-8'))
report={}
for app,strings in data.items():
    pkg='com.xgimi.'+app
    overlay='com.beam.translation.'+app.replace('.','')
    original={x.attrib['name']:''.join(x.itertext()) for x in E.parse(SP/'res6'/app/'res/values/strings.xml').getroot() if x.tag=='string'}
    for k,v in strings.items():
        assert k in original,k
        assert re.findall(r'%(?:\d+\$)?[sd]',original[k])==re.findall(r'%(?:\d+\$)?[sd]',v),k
    work=Path(os.environ['TEMP'])/('beam-rro-'+app);work.mkdir(exist_ok=True)
    root=E.Element('resources')
    for k,v in strings.items(): E.SubElement(root,'string',{'name':k,'formatted':'false'}).text=v.replace('\n',r'\n')
    E.indent(root)
    for folder in ['values','values-en','values-ru','values-zh-rCN']:
        (work/'res'/folder).mkdir(parents=True,exist_ok=True)
        E.ElementTree(root).write(work/'res'/folder/'strings.xml',encoding='utf-8',xml_declaration=True)
    (work/'res/xml').mkdir(exist_ok=True)
    mapping=E.Element('overlay')
    for k in strings:E.SubElement(mapping,'item',{'target':'string/'+k,'value':'@string/'+k})
    E.ElementTree(mapping).write(work/'res/xml/overlays.xml',encoding='utf-8',xml_declaration=True)
    (work/'AndroidManifest.xml').write_text(f'<manifest xmlns:android="http://schemas.android.com/apk/res/android" package="{overlay}" android:versionCode="1" android:versionName="1.0"><uses-sdk android:minSdkVersion="30" android:targetSdkVersion="30"/><application android:hasCode="false" android:label="Beam: перевод аксессуаров"/><overlay android:targetPackage="{pkg}" android:targetName="BeamTranslation" android:resourcesMap="@xml/overlays" android:isStatic="false" android:priority="999"/></manifest>',encoding='utf-8')
    def run(*args):subprocess.run(list(map(str,args)),check=True,env={**os.environ,'JAVA_HOME':r'C:\android\jdk'})
    run(BT/'aapt2.exe','compile','--dir',work/'res','-o',work/'compiled.zip')
    run(BT/'aapt2.exe','link','-o',work/'unsigned.apk','-I',r'C:\android\sdk\platforms\android-34\android.jar','--manifest',work/'AndroidManifest.xml','--package-id','0x80','--no-resource-deduping','--no-resource-removal',work/'compiled.zip')
    run(BT/'zipalign.exe','-f','4',work/'unsigned.apk',work/'aligned.apk')
    dest=OUT/(app+'.apk')
    run(BT/'apksigner.bat','sign','--ks',r'C:\Users\USER\.android\debug.keystore','--ks-pass','pass:android','--key-pass','pass:android','--out',work/'signed.apk',work/'aligned.apk')
    run(BT/'apksigner.bat','verify',work/'signed.apk')
    shutil.copyfile(work/'signed.apk',dest)
    with zipfile.ZipFile(dest) as z:assert not any(n.endswith('.dex') for n in z.namelist())
    report[app]={'package':overlay,'target':pkg,'strings':len(strings),'sha256':hashlib.sha256(dest.read_bytes()).hexdigest()}
(OUT/'build.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report))
