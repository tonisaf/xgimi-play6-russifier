from pathlib import Path
import hashlib,json,shutil,subprocess,zipfile,xml.etree.ElementTree as E
ROOT=Path(__file__).resolve().parents[2]; HERE=Path(__file__).resolve().parent
SP=Path(r'C:\Users\USER\AppData\Local\Temp\claude\C--Users-USER-TileLauncher\4a103049-a7f5-4062-923c-147b4e6834ae\scratchpad')
WORK=Path(r'C:\Users\USER\AppData\Local\Temp\beam-network-theme');WORK.mkdir(exist_ok=True)
java=Path(r'C:\android\jdk\bin')
base=ROOT/'investigation/settings-literals-2026-10-08/beam-settings-panel-ru-v5.apk'
assert hashlib.sha256(base.read_bytes()).hexdigest()=='6b3b6ec5c7ef8c86ed1c04d1436b28242a2a50839f6f5c6166b2fe48de4fa11f'
dst=WORK/'smali_classes5'
shutil.copytree('\\\\?\\'+str(SP/'ns_smali/smali_classes5'),dst,dirs_exist_ok=True)
# Preserve the previous classes5 literal patches before rebuilding that dex.
for source in (ROOT/'investigation/settings-literals-2026-10-08/source').rglob('*.smali'):
    if source.name.endswith('.before.smali'):continue
    rel=source.relative_to(ROOT/'investigation/settings-literals-2026-10-08/source')
    if (dst/rel).exists():shutil.copyfile(source,dst/rel)
p=dst/'com/xgimi/newsettings/misckeyui/WifiDialog$cell$2.smali'
old=p.read_text(encoding='utf-8');literal=r'"\u66f4\u591a\u7f51\u7edc\u8bbe\u7f6e"'
assert old.count(literal)==1
new=old.replace(literal,'"Настройки сети"')
(HERE/'WifiDialog.before.smali').write_text(old,encoding='utf-8');(HERE/'WifiDialog.after.smali').write_text(new,encoding='utf-8');p.write_text(new,encoding='utf-8')
# Translate display names only; keep original getName() for generated action IDs.
entity_source=SP/'ns_smali/smali_classes6/com/xgimi/theme/ThemeEntity.smali'
dst6=WORK/'smali_classes6'
shutil.copytree('\\\\?\\'+str(SP/'ns_smali/smali_classes6'),dst6,dirs_exist_ok=True)
signal=ROOT/'investigation/settings-literals-2026-10-08/source/com/xgimi/signal/SignalRepository.smali'
shutil.copyfile(signal,dst6/'com/xgimi/signal/SignalRepository.smali')
entity=(dst6/'com/xgimi/theme/ThemeEntity.smali').read_text(encoding='utf-8')
method='.method public final getDisplayName()Ljava/lang/String;\n    .locals 3\n    iget-object v0, p0, Lcom/xgimi/theme/ThemeEntity;->name:Ljava/lang/String;\n'
for idx,(cn,ru) in enumerate([('浅色','Светлая'),('白色','Светлая'),('黑色','Тёмная'),('蓝色','Синяя')]):
    method+=f'    const-string v1, "{cn}"\n    invoke-virtual {{v1, v0}}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z\n    move-result v2\n    if-eqz v2, :beam_theme_{idx}\n    const-string v0, "{ru}"\n    return-object v0\n    :beam_theme_{idx}\n'
method+='    return-object v0\n.end method\n'
(dst6/'com/xgimi/theme/ThemeEntity.smali').write_text(entity+'\n'+method,encoding='utf-8')
repo=dst6/'com/xgimi/theme/ThemeRepository.smali';text=repo.read_text(encoding='utf-8')
calls=text.count('ThemeEntity;->getName()');assert calls==5
# The first call after .line 237 supplies the action ID; all others are labels.
text=text.replace('ThemeEntity;->getName()','ThemeEntity;->getDisplayName()')
text=text.replace('.line 237\n    invoke-virtual/range {v19 .. v19}, Lcom/xgimi/theme/ThemeEntity;->getDisplayName()', '.line 237\n    invoke-virtual/range {v19 .. v19}, Lcom/xgimi/theme/ThemeEntity;->getName()')
assert text.count('ThemeEntity;->getName()')==1
text=text.replace(r'const-string v1, "\u81ea\u52a8"','const-string v1, "Авто"')
repo.write_text(text,encoding='utf-8')
adapter=dst/'com/xgimi/newsettings/adatper/ThemeAdapter.smali';text=adapter.read_text(encoding='utf-8');assert text.count('ThemeEntity;->getName()')==2
adapter.write_text(text.replace('ThemeEntity;->getName()','ThemeEntity;->getDisplayName()'),encoding='utf-8')
for name in ['ThemeEntity','ThemeRepository']:
    shutil.copyfile(dst6/f'com/xgimi/theme/{name}.smali',HERE/f'{name}.after.smali')
shutil.copyfile(adapter,HERE/'ThemeAdapter.after.smali')
builder=ROOT/'investigation/quick-panel-brightness-2026-10-08/BuildDex.java' 
subprocess.run([str(java/'javac.exe'),'-cp',str(SP/'apktool.jar'),'-d',str(WORK),str(builder)],check=True)
subprocess.run([str(java/'java.exe'),'-Xmx2g','-cp',str(SP/'apktool.jar')+';'+str(WORK),'BuildDex',str(dst),str(WORK/'classes5.dex')],check=True)
subprocess.run([str(java/'java.exe'),'-Xmx2g','-cp',str(SP/'apktool.jar')+';'+str(WORK),'BuildDex',str(dst6),str(WORK/'classes6.dex')],check=True)
apk=HERE/'panel.apk'
with zipfile.ZipFile(base) as src,zipfile.ZipFile(apk,'w') as dest:
    for info in src.infolist():dest.writestr(info,(WORK/info.filename).read_bytes() if info.filename in ('classes5.dex','classes6.dex') else src.read(info.filename))
with zipfile.ZipFile(base) as src,zipfile.ZipFile(apk) as dest:
    assert [n for n in src.namelist() if src.read(n)!=dest.read(n)]==['classes5.dex','classes6.dex']
# Extend the exact current RRO, retaining all previous strings and both layouts.
rro=ROOT/'investigation/main-settings-native-2026-10-08/rro'
shutil.copytree(rro/'res',WORK/'res',dirs_exist_ok=True)
strings=E.parse(WORK/'res/values/strings.xml');mapping=E.parse(WORK/'res/xml/overlays.xml')
add={'theme_advanced_settings_subtitle_text':'Дополнительно','theme_auto_day_text':'Дневная тема','theme_auto_night_text':'Ночная тема','theme_display_black':'Тёмная','theme_display_white':'Светлая','theme_display_text':'Стиль темы','toast_auto_theme_not_network':'Для смены темы по расписанию нужен интернет'}
existing={s.get('name'):s for s in strings.getroot()}
for k,v in add.items():
    assert k not in existing
    E.SubElement(strings.getroot(),'string',{'name':k}).text=v
    E.SubElement(mapping.getroot(),'item',{'target':'string/'+k,'value':'@string/'+k})
for tree,path in [(strings,'values/strings.xml'),(mapping,'xml/overlays.xml')]:E.indent(tree);tree.write(WORK/'res'/path,encoding='utf-8',xml_declaration=True)
manifest=(rro/'AndroidManifest.xml').read_text(encoding='utf-8').replace('versionCode="8"','versionCode="9"').replace('versionName="1.7"','versionName="1.8"');(WORK/'AndroidManifest.xml').write_text(manifest,encoding='utf-8')
bt=Path(r'C:\android\sdk\build-tools\34.0.0')
def run(*args):subprocess.run(list(map(str,args)),check=True,env={**__import__('os').environ,'JAVA_HOME':r'C:\android\jdk'})
run(bt/'aapt2.exe','compile','--dir',WORK/'res','-o',WORK/'compiled.zip')
run(bt/'aapt2.exe','link','-o',WORK/'unsigned.apk','-I',r'C:\android\sdk\platforms\android-34\android.jar','-I',SP/'apps/com.android.newsettings.apk','--manifest',WORK/'AndroidManifest.xml','--package-id','0x80','--no-resource-deduping','--no-resource-removal',WORK/'compiled.zip')
run(bt/'zipalign.exe','-f','4',WORK/'unsigned.apk',WORK/'aligned.apk')
run(bt/'apksigner.bat','sign','--ks',r'C:\Users\USER\.android\debug.keystore','--ks-pass','pass:android','--key-pass','pass:android','--out',HERE/'settings.apk',WORK/'aligned.apk')
run(bt/'apksigner.bat','verify',HERE/'settings.apk')
shutil.copytree(WORK/'res',HERE/'rro/res',dirs_exist_ok=True);shutil.copyfile(WORK/'AndroidManifest.xml',HERE/'rro/AndroidManifest.xml')
(HERE/'additions.json').write_text(json.dumps(add,ensure_ascii=False,indent=2),encoding='utf-8')
(HERE/'build.json').write_text(json.dumps({'panelSha256':hashlib.sha256(apk.read_bytes()).hexdigest(),'settingsSha256':hashlib.sha256((HERE/'settings.apk').read_bytes()).hexdigest(),'strings':len(strings.getroot()),'layouts':2,'changedDex':'classes5.dex'},indent=2),encoding='utf-8')
print((HERE/'build.json').read_text())
