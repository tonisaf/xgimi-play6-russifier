from pathlib import Path
import shutil, subprocess, zipfile, hashlib, json, sys
sys.stdout.reconfigure(encoding='utf-8')
SP=Path(r'C:\Users\USER\AppData\Local\Temp\claude\C--Users-USER-TileLauncher\4a103049-a7f5-4062-923c-147b4e6834ae\scratchpad')
OUT=Path(r'C:\Users\USER\AppData\Local\Temp\beam-brightness-apk')
PATCH=Path(__file__).resolve().parent
OUT.mkdir(exist_ok=True)
subprocess.run([r'C:\android\jdk\bin\javac.exe','-cp',str(SP/'apktool.jar'),'-d',str(OUT),str(PATCH/'BuildDex.java')],check=True)
num=4
dst=OUT/'smali_classes4'
shutil.copytree('\\\\?\\'+str(SP/'ns_smali'/dst.name),str(dst),dirs_exist_ok=True)
for name,rel in [('TopInfoAndFuncCell','com/xgimi/misckey/cell'),('DateUtil','com/xgimi/misckey/util'),('BleMusicCtrRowItem','com/xgimi/misckey/cell'),('MisckeyConfigCell','com/xgimi/misckey/cell')]:
    target=dst/rel/(name+'.smali')
    original=(PATCH/('original-'+name+'.smali')).read_bytes()
    assert target.read_bytes() in (original,(PATCH/('draft-'+name+'.smali')).read_bytes()),name
    shutil.copyfile(PATCH/('draft-'+name+'.smali'),target)
for extra in PATCH.glob('BeamBrightness*.smali'):
    shutil.copyfile(extra,dst/'com/xgimi/misckey/cell'/extra.name)
cmd=[r'C:\android\jdk\bin\java.exe','-Xmx2g','-cp',str(SP/'apktool.jar')+';'+str(OUT),'BuildDex',str(dst),str(OUT/'classes4.dex')]
subprocess.run(cmd,check=True)
orig=SP/'apps/com.android.newsettings.apk'
apk=OUT/'beam-newsettings-date-ru.apk'
with zipfile.ZipFile(orig) as src,zipfile.ZipFile(apk,'w') as dest:
    for info in src.infolist():
        data=src.read(info.filename)
        if info.filename=='classes4.dex': data=(OUT/info.filename).read_bytes()
        dest.writestr(info,data)
with zipfile.ZipFile(orig) as src,zipfile.ZipFile(apk) as dst:
    changed=[n for n in src.namelist() if src.read(n)!=dst.read(n)]
    assert changed==['classes4.dex'],changed
report={'original_sha256':hashlib.sha256(orig.read_bytes()).hexdigest(),'modified_sha256':hashlib.sha256(apk.read_bytes()).hexdigest(),'changed_entries':changed,'apk':str(apk),'note':'Signing metadata no longer valid; temporary cached-package bind mount experiment only.'}
(PATCH/'apk-build.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report))
