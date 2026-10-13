"""Build a resource-only overlay for XGIMI framework shutdown/restart labels."""
from pathlib import Path
import os, subprocess, shutil, xml.etree.ElementTree as E

ROOT = Path(__file__).resolve().parents[1]
WORK = Path('C:/android/framework-power-rro-20261009')
BT = Path('C:/android/sdk/build-tools/34.0.0')
LABELS = {
    'xgimi_warn_turnoff': 'Выключение…',
    'xgimi_warn_restart': 'Перезагрузка…',
}
WORK.mkdir(parents=True, exist_ok=True)
for folder in ['values', 'values-ru', 'values-en', 'values-zh-rCN', 'xml']:
    (WORK / 'res' / folder).mkdir(parents=True, exist_ok=True)
resources = E.Element('resources')
for key, text in LABELS.items():
    E.SubElement(resources, 'string', {'name': key}).text = text
E.indent(resources)
for folder in ['values', 'values-ru', 'values-en', 'values-zh-rCN']:
    E.ElementTree(resources).write(WORK / 'res' / folder / 'strings.xml', encoding='utf-8', xml_declaration=True)
mapping = E.Element('overlay')
for key in LABELS:
    E.SubElement(mapping, 'item', {'target': 'string/' + key, 'value': '@string/' + key})
E.indent(mapping)
E.ElementTree(mapping).write(WORK / 'res/xml/overlays.xml', encoding='utf-8', xml_declaration=True)
(WORK / 'AndroidManifest.xml').write_text('''<manifest xmlns:android="http://schemas.android.com/apk/res/android" package="com.beam.translation.frameworkpower" android:versionCode="1" android:versionName="1.0">
<uses-sdk android:minSdkVersion="30" android:targetSdkVersion="30"/>
<application android:hasCode="false" android:label="XGIMI: выключение и перезагрузка"/>
<overlay android:targetPackage="android" android:targetName="BeamTranslation" android:resourcesMap="@xml/overlays" android:isStatic="false" android:priority="999"/>
</manifest>''', encoding='utf-8')
def run(*args):
    subprocess.run(list(map(str, args)), check=True, env={**os.environ, 'JAVA_HOME': 'C:/android/jdk'})
run(BT/'aapt2.exe', 'compile', '--dir', WORK/'res', '-o', WORK/'compiled.zip')
run(BT/'aapt2.exe', 'link', '-o', WORK/'unsigned.apk', '-I', 'C:/android/sdk/platforms/android-34/android.jar', '--manifest', WORK/'AndroidManifest.xml', '--package-id', '0x80', '--no-resource-deduping', '--no-resource-removal', WORK/'compiled.zip')
run(BT/'zipalign.exe', '-f', '4', WORK/'unsigned.apk', WORK/'aligned.apk')
run(BT/'apksigner.bat', 'sign', '--ks', Path.home()/'.android/debug.keystore', '--ks-pass', 'pass:android', '--key-pass', 'pass:android', '--out', WORK/'framework-power.apk', WORK/'aligned.apk')
run(BT/'apksigner.bat', 'verify', WORK/'framework-power.apk')
shutil.copyfile(WORK/'framework-power.apk', ROOT/'russifier/payload/framework-power.apk')
print('Built framework-power.apk (two display strings only)')
