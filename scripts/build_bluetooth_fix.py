"""Preserve existing payload, add Bluetooth translations and display-only name bounds."""
from pathlib import Path
import os,json,hashlib,shutil,subprocess,zipfile,re,xml.etree.ElementTree as E
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'investigation/bluetooth-fix-2026-10-10';OUT.mkdir(exist_ok=True)
BT=Path('C:/android/sdk/build-tools/34.0.0');J=Path('C:/android/jdk/bin');AJ=Path('C:/android/sdk/platforms/android-34/android.jar')
M=ROOT/'russifier/manifest.json';m=json.loads(M.read_text(encoding='utf-8'))
def run(*args):subprocess.run(list(map(str,args)),check=True,env={**os.environ,'JAVA_HOME':'C:/android/jdk'})
def build_overlay(base,work,name,changes,target):
    work=Path('C:/android/bluetooth-overlay-20261010')/work.name
    shutil.copytree(base/'res',work/'res',dirs_exist_ok=True)
    (work/'res/values/public.xml').unlink(missing_ok=True)
    for folder in (work/'res').glob('values*'):
        p=folder/'strings.xml'
        if not p.exists():continue
        tree=E.parse(p);root=tree.getroot()
        for key,value in changes.items():
            node=next((x for x in root if x.get('name')==key),None)
            if node is None:node=E.SubElement(root,'string',{'name':key,'formatted':'false'})
            node.text=value
        tree.write(p,encoding='utf-8',xml_declaration=True)
    p=work/'res/xml/overlays.xml';tree=E.parse(p);root=tree.getroot()
    for key in changes:
        if not any(x.get('target')=='string/'+key for x in root):E.SubElement(root,'item',{'target':'string/'+key,'value':'@string/'+key})
    tree.write(p,encoding='utf-8',xml_declaration=True)
    text=(base/'AndroidManifest.xml').read_text(encoding='utf-8')
    text=re.sub(r' android:versionCode="\d+"','',text)
    text=re.sub(r' android:versionName="[^"]+"','',text)
    text=text.replace('<manifest ','<manifest android:versionCode="26" android:versionName="1.19.6" ',1)
    if not any(x.tag=='uses-sdk' for x in E.fromstring(text)):
        text=text.replace('<application','<uses-sdk android:minSdkVersion="30" android:targetSdkVersion="30"/><application',1)
    (work/'AndroidManifest.xml').write_text(text,encoding='utf-8')
    run(BT/'aapt2.exe','compile','--dir',work/'res','-o',work/'compiled.zip')
    args=[BT/'aapt2.exe','link','-o',work/'unsigned.apk','-I',AJ]
    if target=='com.android.newsettings':args+=['-I','C:/android/panel-current-20261009-original.apk']
    run(*args,'--manifest',work/'AndroidManifest.xml','--package-id','0x80','--no-resource-deduping','--no-resource-removal',work/'compiled.zip')
    run(BT/'zipalign.exe','-f','4',work/'unsigned.apk',work/'aligned.apk')
    run(BT/'apksigner.bat','sign','--ks',Path.home()/'.android/debug.keystore','--ks-pass','pass:android','--key-pass','pass:android','--out',work/name,work/'aligned.apk')
    run(BT/'apksigner.bat','verify',work/name)
    badging=subprocess.check_output([str(BT/'aapt2.exe'),'dump','badging',str(work/name)]).decode('utf-8')
    assert "versionCode='26'" in badging and "sdkVersion:'30'" in badging and "targetSdkVersion:'30'" in badging
    shutil.copyfile(work/name,ROOT/'russifier/payload'/name)
    m['files'][name]=hashlib.sha256((work/name).read_bytes()).hexdigest()
    m['resourceChecks'].setdefault(target,{}).update(changes)
    shutil.copytree(work/'res',OUT/work.name/'res',dirs_exist_ok=True)
    shutil.copyfile(work/'AndroidManifest.xml',OUT/work.name/'AndroidManifest.xml')

settings={'bluetooth_device_connected':'Подключено','bluetooth_device_disconnected':'Отключено'}
notices={'audio_bt':'Bluetooth','sound_device_insert_tip':'%s подключено. Нажмите OK для смены выхода звука','sound_device_insert_tip1':'%s подключено. Нажмите','sound_device_pull_out_tip':'%s отключено. Нажмите OK для смены выхода звука','sound_device_pull_out_tip1':'%s отключено. Нажмите','sound_device_tip2':'для смены выхода звука','sound_device_usb_to_other_tip':'%s отключено. Включены динамики проектора'}
build_overlay(Path('C:/android/settings-gaps-build-20261009'),OUT/'settings','settings.apk',settings,'com.android.newsettings')
build_overlay(Path('C:/android/bluetooth-systemui-rro-base-20261010'),OUT/'systemui','systemui.apk',notices,'com.xgimi.systemui')

work=Path('C:/android/bluetooth-panel-code-20261010');smali=work/'smali_classes5'
p=smali/'com/xgimi/newsettings/adatper/BluetoothAdapter.smali';text=p.read_text(encoding='utf-8')
text=re.sub(r'    invoke-static \{v[14]\}, Lcom/xgimi/newsettings/widget/BeamBluetoothName;->display\(Ljava/lang/String;\)Ljava/lang/String;\n    move-result-object v[14]\n','',text)
# Only the two device-name bindings; retain the original full Bluetooth model/name.
for receiver,argument in [('v5','v4'),('p1','v1')]:
    needle='    invoke-virtual {'+receiver+', '+argument+'}, Lcom/xgimi/newsettings/widget/ArrowTextCellView;->setText(Ljava/lang/String;)V'
    if receiver=='p1':
        assert text.count(needle)==2
        text=text.replace(needle,'    invoke-static {'+argument+'}, Lcom/xgimi/newsettings/widget/BeamBluetoothName;->display(Ljava/lang/String;)Ljava/lang/String;\n    move-result-object '+argument+'\n'+needle,1)
    else:
        assert text.count(needle)==1
        text=text.replace(needle,'    invoke-static {'+argument+'}, Lcom/xgimi/newsettings/widget/BeamBluetoothName;->display(Ljava/lang/String;)Ljava/lang/String;\n    move-result-object '+argument+'\n'+needle)
p.write_text(text,encoding='utf-8')
helper='''.class public final Lcom/xgimi/newsettings/widget/BeamBluetoothName;
.super Ljava/lang/Object;
.method public static display(Ljava/lang/String;)Ljava/lang/String;
    .locals 4
    if-nez p0, :name
    const-string p0, ""
    return-object p0
    :name
    new-instance v0, Landroid/text/TextPaint;
    invoke-direct {v0}, Landroid/text/TextPaint;-><init>()V
    const/high16 v1, 0x41d00000
    invoke-virtual {v0, v1}, Landroid/text/TextPaint;->setTextSize(F)V
    const-string v1, "sans-serif-medium"
    const/4 v2, 0x0
    invoke-static {v1, v2}, Landroid/graphics/Typeface;->create(Ljava/lang/String;I)Landroid/graphics/Typeface;
    move-result-object v1
    invoke-virtual {v0, v1}, Landroid/text/TextPaint;->setTypeface(Landroid/graphics/Typeface;)Landroid/graphics/Typeface;
    const/high16 v1, 0x430c0000
    sget-object v2, Landroid/text/TextUtils$TruncateAt;->END:Landroid/text/TextUtils$TruncateAt;
    invoke-static {p0, v0, v1, v2}, Landroid/text/TextUtils;->ellipsize(Ljava/lang/CharSequence;Landroid/text/TextPaint;FLandroid/text/TextUtils$TruncateAt;)Ljava/lang/CharSequence;
    move-result-object v3
    invoke-interface {v3}, Ljava/lang/CharSequence;->toString()Ljava/lang/String;
    move-result-object v3
    return-object v3
.end method
'''
(smali/'com/xgimi/newsettings/widget/BeamBluetoothName.smali').write_text(helper,encoding='utf-8')
jar=Path(os.environ['TEMP'])/'claude/C--Users-USER-TileLauncher/4a103049-a7f5-4062-923c-147b4e6834ae/scratchpad/apktool.jar'
shutil.copyfile(ROOT/'scripts/BuildAtmosphereDex.java',work/'BuildDex.java')
run(J/'javac.exe','-cp',jar,'-d',work,work/'BuildDex.java')
run(J/'java.exe','-Xmx2g','-cp',str(jar)+';'+str(work),'BuildDex',smali,work/'classes5-new.dex')
old=ROOT/'russifier/payload/panel.apk'
if not (OUT/'panel-before.apk').exists():shutil.copyfile(old,OUT/'panel-before.apk')
with zipfile.ZipFile(old) as src,zipfile.ZipFile(OUT/'panel.apk','w') as dst:
    for i in src.infolist():dst.writestr(i,(work/'classes5-new.dex').read_bytes() if i.filename=='classes5.dex' else src.read(i.filename))
with zipfile.ZipFile(old) as a,zipfile.ZipFile(OUT/'panel.apk') as b:
    assert [n for n in a.namelist() if a.read(n)!=b.read(n)]==['classes5.dex']
previous=hashlib.sha256(old.read_bytes()).hexdigest()
if previous not in m['previousPanelHashes']:m['previousPanelHashes'].append(previous)
shutil.copyfile(OUT/'panel.apk',old);m['files']['panel.apk']=hashlib.sha256(old.read_bytes()).hexdigest()
m['version']='1.19.6';M.write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(OUT/'translations.json').write_text(json.dumps({'settings':settings,'systemui':notices,'nameWidth':140,'fontSize':26,'changedDex':'classes5.dex'},ensure_ascii=False,indent=2),encoding='utf-8')
print('Bluetooth payload built; manifest updated to 1.19.6')
