from pathlib import Path
import json, shutil, subprocess, os, hashlib, xml.etree.ElementTree as E
H=Path(__file__).resolve().parent; ROOT=H.parents[1]
M=ROOT/'russifier/manifest.json'; m=json.loads(M.read_text(encoding='utf-8'))
data={'inner_battery_title':'Питание от встроенной батареи','eco_mode_button_confirm':'Понятно','eco_mode_subject_title':'Настройки → Общее','eco_mode_title_desc':'Подробнее','notice_press_guide_tips':'Нажмите OK для подробностей'}
orig={x.get('name') for x in E.parse(Path(os.environ['TEMP'])/'beam-current-systemui/res/values/strings.xml').getroot()}
assert all(k in orig for k in data)
m['resourceChecks']['com.xgimi.systemui'].update(data)
W=Path(os.environ['TEMP'])/'beam-battery-rro'; shutil.copytree(H.parent/'eco-mode-notices-2026-10-08/rro-systemui/res',W/'res',dirs_exist_ok=True)
mapping=E.parse(W/'res/xml/overlays.xml'); known={x.get('target') for x in mapping.getroot()}
strings=E.Element('resources')
for node in E.parse(W/'res/values/strings.xml').getroot():
 if node.get('name') not in m['resourceChecks']['com.xgimi.systemui']:strings.append(node)
for k,v in m['resourceChecks']['com.xgimi.systemui'].items():
 E.SubElement(strings,'string',{'name':k,'formatted':'false'}).text=v.replace('\n',r'\n')
 if 'string/'+k not in known:E.SubElement(mapping.getroot(),'item',{'target':'string/'+k,'value':'@string/'+k})
for folder in ('values','values-zh-rCN','values-en','values-ru'):
 E.indent(strings); E.ElementTree(strings).write(W/'res'/folder/'strings.xml',encoding='utf-8',xml_declaration=True)
E.indent(mapping);mapping.write(W/'res/xml/overlays.xml',encoding='utf-8',xml_declaration=True)
manifest=(H.parent/'eco-mode-notices-2026-10-08/rro-systemui/AndroidManifest.xml').read_text(encoding='utf-8').replace('versionCode="4"','versionCode="5"').replace('versionName="1.3"','versionName="1.4"')
(W/'AndroidManifest.xml').write_text(manifest,encoding='utf-8')
B=Path(r'C:\android\sdk\build-tools\34.0.0')
def run(*a):subprocess.run(list(map(str,a)),check=True,env={**os.environ,'JAVA_HOME':r'C:\android\jdk'})
run(B/'aapt2.exe','compile','--dir',W/'res','-o',W/'compiled.zip')
run(B/'aapt2.exe','link','-o',W/'unsigned.apk','-I',r'C:\android\sdk\platforms\android-34\android.jar','--manifest',W/'AndroidManifest.xml','--package-id','0x80','--no-resource-deduping','--no-resource-removal',W/'compiled.zip')
run(B/'zipalign.exe','-f','4',W/'unsigned.apk',W/'aligned.apk')
out=ROOT/'russifier/payload/systemui.apk'
run(B/'apksigner.bat','sign','--ks',r'C:\Users\USER\.android\debug.keystore','--ks-pass','pass:android','--key-pass','pass:android','--out',W/'signed.apk',W/'aligned.apk')
run(B/'apksigner.bat','verify',W/'signed.apk')
shutil.copy2(W/'signed.apk',out)
m['files']['systemui.apk']=hashlib.sha256(out.read_bytes()).hexdigest()
M.write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(H/'translations.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(m['files']['systemui.apk'])
