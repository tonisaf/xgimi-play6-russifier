from pathlib import Path
import json,xml.etree.ElementTree as E,subprocess,shutil,os,sys
sys.stdout.reconfigure(encoding='utf-8')
out=Path('investigation/main-settings-native-2026-10-08').resolve()
sp=Path(r'C:\Users\USER\AppData\Local\Temp\claude\C--Users-USER-TileLauncher\4a103049-a7f5-4062-923c-147b4e6834ae\scratchpad\ns\res')
skin={x.get('name'):x for x in E.parse(r'C:\Users\USER\TileLauncher\skin\res\values\strings.xml').getroot()}
orig={x.get('name'):''.join(x.itertext()) for x in E.parse(sp/'values/strings.xml').getroot()}
for k,v in {'head_picture_correction_text':'Коррекция','head_screen_setting_text':'Коррекция','head_image_setting_text':'Изображение','head_bluetooth_setting_text':'Bluetooth'}.items():skin[k].text=v
rows=json.loads((out/'resources.json').read_text(encoding='utf-8'))
keys={r['key'] for r in rows}
keys.update(['zoom_and_displacement_text','digital_zoom_txt','keystone_for_990c_remote','back_txt','digital_displacement'])
for k,v in {'digital_zoom_txt':'Масштаб','digital_displacement':'Сдвиг','keystone_for_990c_remote':'Удерживайте для меню'}.items():skin[k].text=v
keys.update(['image_set_mode_bright_text','image_set_mode_constrast_ratio_text','image_set_mode_saturation_text','image_set_mode_sharpness_text'])
keys.update(r['key'] for r in json.loads((out/'tips-candidates.json').read_text(encoding='utf-8')))
for k in skin:
 if k.startswith(('led_','boot_source_','signal_source_setting_boot_')) and k in orig and any('\u4e00'<=c<='\u9fff' for c in orig[k]):keys.add(k)
rows=[{'key':k,'original':orig[k],'translation':''.join(skin[k].itertext())} for k in sorted(keys)]
(out/'resources.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
work=Path(os.environ['TEMP'])/'beam-settings-native-rro-v7';work.mkdir(exist_ok=True)
for folder in ['values','xml','layout']:(work/'res'/folder).mkdir(parents=True,exist_ok=True)
shutil.copyfile(out/'zoom-layout-ru.xml',work/'res/layout/beam_zoom_displacement.xml')
r=E.Element('resources')
for k in sorted(keys):r.append(skin[k])
E.indent(r);E.ElementTree(r).write(work/'res/values/strings.xml',encoding='utf-8',xml_declaration=True)
root=E.Element('overlay',{'xmlns:android':'http://schemas.android.com/apk/res/android'})
for k in sorted(keys):E.SubElement(root,'item',{'target':'string/'+k,'value':'@string/'+k})
E.SubElement(root,'item',{'target':'layout/dialog_keystone_view_zoom_displacement','value':'@layout/beam_zoom_displacement'})
E.indent(root);E.ElementTree(root).write(work/'res/xml/overlays.xml',encoding='utf-8',xml_declaration=True)
(work/'AndroidManifest.xml').write_text('''<manifest xmlns:android="http://schemas.android.com/apk/res/android" package="com.beam.translation.settings" android:versionCode="7" android:versionName="1.6"><uses-sdk android:minSdkVersion="30" android:targetSdkVersion="30"/><application android:hasCode="false" android:label="Beam: русский перевод настроек"/><overlay android:targetPackage="com.android.newsettings" android:targetName="BeamTranslation" android:resourcesMap="@xml/overlays" android:isStatic="false" android:priority="999"/></manifest>''',encoding='utf-8')
bt=Path(r'C:\android\sdk\build-tools\34.0.0')
def run(*args):subprocess.run(list(map(str,args)),check=True,env={**os.environ,'JAVA_HOME':r'C:\android\jdk'})
run(bt/'aapt2.exe','compile','--dir',work/'res','-o',work/'compiled.zip')
run(bt/'aapt2.exe','link','-o',work/'unsigned.apk','-I',r'C:\android\sdk\platforms\android-34\android.jar','-I',sp.parent.parent/'apps/com.android.newsettings.apk','--manifest',work/'AndroidManifest.xml','--package-id','0x80','--no-resource-deduping','--no-resource-removal',work/'compiled.zip')
run(bt/'zipalign.exe','-f','4',work/'unsigned.apk',work/'aligned.apk')
run(bt/'apksigner.bat','sign','--ks',r'C:\Users\USER\.android\debug.keystore','--ks-pass','pass:android','--key-pass','pass:android','--out',work/'beam-settings-ru.apk',work/'aligned.apk')
run(bt/'apksigner.bat','verify',work/'beam-settings-ru.apk')
shutil.copytree(work,out/'rro',dirs_exist_ok=True)
print('strings:',len(keys))
