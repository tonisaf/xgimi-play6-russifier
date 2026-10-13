from pathlib import Path
import json, hashlib, zipfile, subprocess, os
H=Path(__file__).resolve().parent;ROOT=H.parents[1];W=Path(os.environ['TEMP'])/'beam-current-systemui-code'
M=ROOT/'russifier/manifest.json';m=json.loads(M.read_text(encoding='utf-8'))
original=Path(os.environ['TEMP'])/'beam-current-systemui.apk'
assert hashlib.sha256(original.read_bytes()).hexdigest()==m['originals']['com.xgimi.systemui']['sha256']
target=W/'smali_classes2/com/xgimi/systemui/battery/BatteryHelper.smali'
text=target.read_text(encoding='utf-8')
if r'\u63a5\u5165\u79fb' not in text and (H/'BatteryHelper.before.smali').exists():
 text=(H/'BatteryHelper.before.smali').read_text(encoding='utf-8')
before=text
lines=[line for line in text.splitlines() if 'const-string v2,' in line and r'\u63a5\u5165\u79fb' in line]
assert len(lines)==1
translation='Настройки → Общее\\n\\n· Для работы от внешней батареи или стороннего адаптера\\n  рекомендуется включить энергосбережение.\\n· В этом режиме снижаются яркость и качество звука.\\n· С оригинальным адаптером экорежим отключается автоматически.'
text=text.replace(lines[0],'    const-string v2, '+json.dumps(translation,ensure_ascii=False).replace('\\\\n','\\n'))
(H/'BatteryHelper.before.smali').write_text(before,encoding='utf-8')
(H/'BatteryHelper.after.smali').write_text(text,encoding='utf-8')
target.write_text(text,encoding='utf-8')
SP=Path(r'C:\Users\USER\AppData\Local\Temp\claude\C--Users-USER-TileLauncher\4a103049-a7f5-4062-923c-147b4e6834ae\scratchpad')
J=Path(r'C:\android\jdk\bin')
subprocess.run([str(J/'javac.exe'),'-cp',str(SP/'apktool.jar'),'-d',str(W),str(H.parent/'quick-panel-brightness-2026-10-08/BuildDex.java')],check=True)
subprocess.run([str(J/'java.exe'),'-Xmx2g','-cp',str(SP/'apktool.jar')+';'+str(W),'BuildDex',str(W/'smali_classes2'),str(W/'classes2-new.dex')],check=True)
out=ROOT/'russifier/payload/systemui-native.apk'
with zipfile.ZipFile(original) as src,zipfile.ZipFile(out,'w') as dst:
 for info in src.infolist():dst.writestr(info,(W/'classes2-new.dex').read_bytes() if info.filename=='classes2.dex' else src.read(info.filename))
with zipfile.ZipFile(original) as src,zipfile.ZipFile(out) as dst:
 changed=[n for n in src.namelist() if src.read(n)!=dst.read(n)]
assert changed==['classes2.dex']
m['files']['systemui-native.apk']=hashlib.sha256(out.read_bytes()).hexdigest()
m['runtimePatches']=[x for x in m['runtimePatches'] if x['target']!='com.xgimi.systemui']+[{'target':'com.xgimi.systemui','file':'systemui-native.apk','backing':'/data/local/tmp/beam-russifier-systemui-v1.apk'}]
M.write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(H/'native-build.json').write_text(json.dumps({'changedEntries':changed,'changedLiterals':1,'sha256':m['files']['systemui-native.apk']},indent=2),encoding='utf-8')
print(m['files']['systemui-native.apk'])
