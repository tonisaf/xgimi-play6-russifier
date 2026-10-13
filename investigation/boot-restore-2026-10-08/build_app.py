from pathlib import Path
import os, secrets, subprocess, shutil, zipfile, hashlib, json
H=Path(__file__).resolve().parent;ROOT=H.parents[1]
W=Path(os.environ['TEMP'])/'beam-boot-app-build';W.mkdir(exist_ok=True)
J=Path(r'C:\android\jdk\bin');SDK=Path(r'C:\android\sdk');BT=SDK/'build-tools/34.0.0';AJ=SDK/'platforms/android-34/android.jar'
signing=ROOT/'.local/boot-signing';signing.mkdir(exist_ok=True,parents=True)
password=signing/'password.txt';key=signing/'key.p12'
if not password.exists():password.write_text(secrets.token_urlsafe(32),encoding='ascii')
pw=password.read_text(encoding='ascii')
if not key.exists():
 subprocess.run([str(J/'keytool.exe'),'-genkeypair','-keystore',str(key),'-storepass:file',str(password),'-keypass:file',str(password),'-alias','russifier','-keyalg','RSA','-keysize','2048','-validity','36500','-dname','CN=XGIMI Russifier'],check=True,capture_output=True)
shutil.copy2(H/'app/AndroidManifest.xml',W/'AndroidManifest.xml')
subprocess.run([str(BT/'aapt2.exe'),'link','-o',str(W/'base.apk'),'--manifest',str(W/'AndroidManifest.xml'),'-I',str(AJ)],check=True)
(W/'classes').mkdir(exist_ok=True)
subprocess.run([str(J/'javac.exe'),'-encoding','UTF-8','-source','8','-target','8','-cp',str(AJ),'-d',str(W/'classes')]+[str(p) for p in (H/'app/src').rglob('*.java')],check=True)
(W/'dex').mkdir(exist_ok=True)
subprocess.run([str(J/'java.exe'),'-cp',str(BT/'lib/d8.jar'),'com.android.tools.r8.D8','--min-api','30','--lib',str(AJ),'--output',str(W/'dex')]+[str(p) for p in (W/'classes').rglob('*.class')],check=True)
with zipfile.ZipFile(W/'base.apk') as src,zipfile.ZipFile(W/'unsigned.apk','w') as dst:
 for info in src.infolist():dst.writestr(info,src.read(info.filename))
 dst.writestr('classes.dex',(W/'dex/classes.dex').read_bytes())
subprocess.run([str(BT/'zipalign.exe'),'-f','4',str(W/'unsigned.apk'),str(W/'aligned.apk')],check=True)
subprocess.run([str(J/'java.exe'),'-jar',str(BT/'lib/apksigner.jar'),'sign','--ks',str(key),'--ks-key-alias','russifier','--ks-pass','file:'+str(password),'--out',str(W/'signed.apk'),str(W/'aligned.apk')],check=True)
subprocess.run([str(J/'java.exe'),'-jar',str(BT/'lib/apksigner.jar'),'verify',str(W/'signed.apk')],check=True)
output=H/'boot-helper.apk';shutil.copy2(W/'signed.apk',output)
print(json.dumps({'file':str(output),'sha256':hashlib.sha256(output.read_bytes()).hexdigest()}))
