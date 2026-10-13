import pathlib,shutil,subprocess,tempfile,sys
OUT=pathlib.Path(__file__).resolve().parent
RRO=pathlib.Path(tempfile.mkdtemp(prefix='beam-systemui-rro-'))
BT=pathlib.Path(r'C:\android\sdk\build-tools\34.0.0')
for folder in ('drawable','xml','values','values-zh-rCN','values-en','values-ru'):
    (RRO/'res'/folder).mkdir(parents=True,exist_ok=True)
src=OUT.parent/'settings-popups-2026-10-07/blue-popup/app_icon_ak3-ru.xml'
shutil.copyfile(src,RRO/'res/drawable/ak_progress_ru.xml')
strings='<?xml version="1.0" encoding="utf-8"?>\n<resources><string name="focus_complete_ru">Фокусировка завершена. Удерживайте кнопку фокусировки для точной настройки</string><string name="ak_complete_ru">Коррекция изображения завершена. Нажмите @ для ручной коррекции</string></resources>\n'
for folder in ('values','values-zh-rCN','values-en','values-ru'):
    (RRO/'res'/folder/'strings.xml').write_text(strings,encoding='utf-8')
(RRO/'res/xml/overlays.xml').write_text('''<overlay xmlns:android="http://schemas.android.com/apk/res/android">
<item target="drawable/app_icon_ak3" value="@drawable/ak_progress_ru"/>
<item target="drawable/app_icon_ak4" value="@drawable/ak_progress_ru"/>
<item target="string/ak_end_toast_tips" value="@string/ak_complete_ru"/>
<item target="string/hall_focus_success" value="@string/focus_complete_ru"/>
</overlay>''',encoding='utf-8')
(RRO/'AndroidManifest.xml').write_text('''<manifest xmlns:android="http://schemas.android.com/apk/res/android" package="com.beam.translation.systemui" android:versionCode="2" android:versionName="1.1">
<uses-sdk android:minSdkVersion="30" android:targetSdkVersion="30"/>
<application android:hasCode="false" android:label="Beam: перевод фокусировки и коррекции"/>
<overlay android:targetPackage="com.xgimi.systemui" TARGETNAME android:resourcesMap="@xml/overlays" android:isStatic="false" android:priority="999"/>
</manifest>'''.replace('TARGETNAME','android:targetName="BeamTranslation"' if '--root-cache-test' in sys.argv else ''),encoding='utf-8')
def run(*args): subprocess.run([str(x) for x in args],check=True)
run(BT/'aapt2.exe','compile','--dir',RRO/'res','-o',RRO/'compiled.zip')
run(BT/'aapt2.exe','link','-o',RRO/'unsigned.apk','-I',r'C:\android\sdk\platforms\android-34\android.jar','--manifest',RRO/'AndroidManifest.xml','--no-resource-deduping','--no-resource-removal',RRO/'compiled.zip')
run(BT/'zipalign.exe','-f','4',RRO/'unsigned.apk',RRO/'aligned.apk')
run(BT/'apksigner.bat','sign','--ks',r'C:\Users\USER\.android\debug.keystore','--ks-pass','pass:android','--key-pass','pass:android','--out',RRO/'beam-systemui-ru.apk',RRO/'aligned.apk')
run(BT/'apksigner.bat','verify',RRO/'beam-systemui-ru.apk')
shutil.copytree(RRO,OUT/'rro-systemui',dirs_exist_ok=True)
print('RRO built and copied to investigation/system-access-2026-10-07/rro-systemui')
