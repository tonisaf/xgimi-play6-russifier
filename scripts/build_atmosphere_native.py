from pathlib import Path
import json,re,hashlib,subprocess,zipfile,argparse,shutil
parser=argparse.ArgumentParser(description="Patch only known Atmosphere display strings")
parser.add_argument('--original',type=Path,required=True)
parser.add_argument('--decoded',type=Path,required=True,help='Unmodified apktool -r decode')
parser.add_argument('--apktool',type=Path,required=True)
parser.add_argument('--work',type=Path,required=True,help='New build directory')
args=parser.parse_args()
ROOT=Path(__file__).resolve().parents[1];O=args.work.resolve();O.mkdir(exist_ok=False,parents=True)
S=O/'smali_classes2'
# apktool creates Kotlin filenames longer than the legacy Windows MAX_PATH.
def longpath(path):
    value=str(Path(path).resolve())
    return chr(92)*2+'?'+chr(92)+value if __import__('os').name=='nt' else value
shutil.copytree(longpath(args.decoded/'smali_classes2'),longpath(S))
shutil.copyfile(ROOT/'scripts/BuildAtmosphereDex.java',O/'BuildDex.java')
original=args.original
assert hashlib.sha256(original.read_bytes()).hexdigest()=='a0638a3db737357c619b60b43175b4c4bf31d614b172c548a82d5d855ff2d9eb'
setting=S/'com/xgimi/atmosphere/settings/widget/ScreensaverSettingView.smali'
data=setting.read_text(encoding='utf-8');needle='const-string v9, "\\u6c38\\u4e0d"'
assert data.count(needle)==1
setting.write_text(data.replace(needle,'const-string v9, "Никогда"'),encoding='utf-8')
bean=S/'com/xgimi/atmosphere/settings/data/introduce/IntroduceData.smali'
data=bean.read_text(encoding='utf-8')
for name in ['getTitle','getContent','getJumpButtonTitle']:
    pattern=r'(?ms)(\.method public final '+name+r'\(\)Ljava/lang/String;.*?)(    return-object v0)(.*?\.end method)'
    data,n=re.subn(pattern,lambda m:m[1]+'    invoke-static {v0}, Lcom/xgimi/atmosphere/settings/data/introduce/BeamText;->translate(Ljava/lang/String;)Ljava/lang/String;\n\n    move-result-object v0\n\n'+m[2]+m[3],data)
    assert n==1,name
bean.write_text(data,encoding='utf-8')
translations={'任意门':'Atmosphere','立即进入':'Открыть'}
for noun in ['内容','程序']:
    for sep in ['，','。',',','.', '， ']:translations['全新屏保'+noun+sep+'更多妙趣氛围']='Новые заставки для уютной атмосферы'
lines=['.class public final Lcom/xgimi/atmosphere/settings/data/introduce/BeamText;','.super Ljava/lang/Object;','.method public static translate(Ljava/lang/String;)Ljava/lang/String;','    .locals 2']
for i,(src,dst) in enumerate(translations.items()):
    lines += ['    const-string v0, '+json.dumps(src,ensure_ascii=False),'    invoke-virtual {v0, p0}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z','    move-result v1',f'    if-eqz v1, :next_{i}','    const-string v0, '+json.dumps(dst,ensure_ascii=False),'    return-object v0',f'    :next_{i}']
lines+=['    return-object p0','.end method']
(S/'com/xgimi/atmosphere/settings/data/introduce/BeamText.smali').write_text('\n'.join(lines)+'\n',encoding='utf-8')
shutil.copyfile(ROOT/'scripts/BeamIntro.smali',S/'com/xgimi/atmosphere/settings/data/introduce/BeamIntro.smali')
fallback=S/'com/xgimi/atmosphere/settings/ui/IntroduceActivity$defaultIntroduce$2.smali'
data=fallback.read_text(encoding='utf-8')
assert data.count('    return-object v0')==2
data=data.replace('    return-object v0','    invoke-static {v0}, Lcom/xgimi/atmosphere/settings/data/introduce/BeamIntro;->decorate(Lcom/xgimi/view/cell/Cell;)V\n\n    return-object v0',1)
fallback.write_text(data,encoding='utf-8')
# Geography translation is applied only to the list cell label, never to LocationInfo.
places=json.loads((ROOT/'scripts/place-names-ru.json').read_text(encoding='utf-8'))
lines=['.class public final Lcom/xgimi/atmosphere/settings/data/introduce/BeamPlace;', '.super Ljava/lang/Object;', '.method public static translate(Ljava/lang/String;)Ljava/lang/String;', '    .locals 2']
for i,(src,dst) in enumerate(places.items()):
    lines += ['    const-string v0, '+json.dumps(src,ensure_ascii=False),'    invoke-virtual {v0, p0}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z','    move-result v1',f'    if-eqz v1, :next_{i}','    const-string v0, '+json.dumps(dst,ensure_ascii=False),'    return-object v0',f'    :next_{i}']
lines+=['    return-object p0','.end method']
(S/'com/xgimi/atmosphere/settings/data/introduce/BeamPlace.smali').write_text('\n'.join(lines)+'\n',encoding='utf-8')
cell=S/'com/xgimi/atmosphere/widget/x$c.smali'
data=cell.read_text(encoding='utf-8')
needle='    invoke-virtual {v3, p1}, Lcom/xgimi/view/cell/component/TextComponent;->setText(Ljava/lang/String;)Lcom/xgimi/view/cell/component/TextComponent;'
assert data.count(needle)==1
data=data.replace(needle,'    invoke-static {p1}, Lcom/xgimi/atmosphere/settings/data/introduce/BeamPlace;->translate(Ljava/lang/String;)Ljava/lang/String;\n    move-result-object p1\n'+needle)
cell.write_text(data,encoding='utf-8')
for filename,replacements in {
    'LocationSelectorDialog$dialogTitle$2.smali': {'地理位置':'Местоположение'},
    'LocationSelectorDialog$rootCell$2.smali': {'按':'Нажмите OK для сохранения','键保存':''},
}.items():
    path=S/'com/xgimi/atmosphere/screensaver/weather'/filename
    data=path.read_text(encoding='utf-8')
    for source,dest in replacements.items():
        source=json.dumps(source,ensure_ascii=True);dest=json.dumps(dest,ensure_ascii=False)
        assert data.count(source)==1,(filename,source)
        data=data.replace(source,dest)
    path.write_text(data,encoding='utf-8')
# Replace the three overlapping hint cells with one complete Russian label.
path=S/'com/xgimi/atmosphere/screensaver/weather/LocationSelectorDialog$rootCell$2.smali'
data=path.read_text(encoding='utf-8');start=data.index('    .line 22\n');end=data.index('    .line 44\n',start)
data=data[:start]+'    invoke-virtual {v1, v2}, Lcom/xgimi/view/cell/Cell;->addCell(Lcom/xgimi/view/cell/Cell;)Lcom/xgimi/view/cell/Cell;\n\n    move-result-object v1\n\n'+data[end:]
path.write_text(data,encoding='utf-8')
shutil.copyfile(ROOT/'scripts/BeamEnergy.smali',S/'com/xgimi/atmosphere/settings/data/introduce/BeamEnergy.smali')
energy=S/'com/xgimi/atmosphere/screensaver/widget/enerty/a.smali'
data=energy.read_text(encoding='utf-8')
needle='    invoke-virtual {v0, v1, v2}, Lcom/xgimi/view/cell/Cell;->addCell(Lcom/xgimi/view/cell/Cell;Lcom/xgimi/view/cell/Layout$Params;)Lcom/xgimi/view/cell/Cell;'
assert data.count(needle)==1
data=data.replace(needle,'    invoke-static {v1}, Lcom/xgimi/atmosphere/settings/data/introduce/BeamEnergy;->decorate(Lcom/xgimi/view/cell/Cell;)V\n\n'+needle)
energy.write_text(data,encoding='utf-8')
# Translate known catalog text at TextComponent.setText, preserving network/cache models.
catalog=json.loads((ROOT/'russifier/payload/catalog-texts.json').read_text(encoding='utf-8'))
for source,value in list(catalog.items()):
    catalog.setdefault(source.strip(),value)
lines=['.class public final Lcom/xgimi/atmosphere/settings/data/introduce/BeamCatalog;', '.super Ljava/lang/Object;', '.method public static translate(Ljava/lang/String;)Ljava/lang/String;', '    .locals 2']
for i,(source,value) in enumerate(catalog.items()):
    lines += ['    const-string v0, '+json.dumps(source,ensure_ascii=False),'    invoke-virtual {v0, p0}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z','    move-result v1',f'    if-eqz v1, :next_{i}','    const-string v0, '+json.dumps(value,ensure_ascii=False),'    return-object v0',f'    :next_{i}']
lines+=['    return-object p0','.end method', '.method public static setText(Lcom/xgimi/view/cell/component/TextComponent;Ljava/lang/String;)Lcom/xgimi/view/cell/component/TextComponent;', '    .locals 1','    invoke-static {p1}, Lcom/xgimi/atmosphere/settings/data/introduce/BeamCatalog;->translate(Ljava/lang/String;)Ljava/lang/String;', '    move-result-object v0','    invoke-virtual {p0, v0}, Lcom/xgimi/view/cell/component/TextComponent;->setText(Ljava/lang/String;)Lcom/xgimi/view/cell/component/TextComponent;','    move-result-object v0','    return-object v0','.end method']
pattern=r'invoke-virtual(\/range)? (\{[^}]+\}), Lcom/xgimi/view/cell/component/TextComponent;->setText\(Ljava/lang/String;\)Lcom/xgimi/view/cell/component/TextComponent;'
catalog_sites=[]
for path in (S/'com/xgimi/atmosphere').rglob('*.smali'):
    if path.name.startswith('Beam'):continue
    data=path.read_text(encoding='utf-8')
    data,count=re.subn(pattern,lambda m:'invoke-static'+(m[1] or '')+' '+m[2]+', Lcom/xgimi/atmosphere/settings/data/introduce/BeamCatalog;->setText(Lcom/xgimi/view/cell/component/TextComponent;Ljava/lang/String;)Lcom/xgimi/view/cell/component/TextComponent;',data)
    if count:
        path.write_text(data,encoding='utf-8');catalog_sites.append({'file':str(path.relative_to(S)),'calls':count})
assert sum(x['calls'] for x in catalog_sites)>=60
(S/'com/xgimi/atmosphere/settings/data/introduce/BeamCatalog.smali').write_text('\n'.join(lines)+'\n',encoding='utf-8')
(O/'catalog-display-sites.json').write_text(json.dumps(catalog_sites,indent=2),encoding='utf-8')
# Screensaver title uses a separate spannable component; input is a String UI argument.
info=S/'com/xgimi/atmosphere/screensaver/widget/ScreensaverInfoCell.smali'
data=info.read_text(encoding='utf-8')
needle='    invoke-virtual {v0, p1}, Lcom/xgimi/widget/launcher/component/SpannableTextComponent2;->setText(Ljava/lang/CharSequence;)Lcom/xgimi/widget/launcher/component/SpannableTextComponent2;'
assert data.count(needle)==1
data=data.replace(needle,'    invoke-static {p1}, Lcom/xgimi/atmosphere/settings/data/introduce/BeamCatalog;->translate(Ljava/lang/String;)Ljava/lang/String;\n    move-result-object p1\n'+needle)
info.write_text(data,encoding='utf-8')
jar=args.apktool.resolve()
subprocess.run([r'C:\android\jdk\bin\javac.exe','-cp',str(jar),'-d',str(O),str(O/'BuildDex.java')],check=True)
subprocess.run([r'C:\android\jdk\bin\java.exe','-Xmx2g','-cp',str(jar)+';'+str(O),'BuildDex',str(S),str(O/'classes2.dex')],check=True)
apk=ROOT/'russifier/payload/atmosphere-native.apk'
with zipfile.ZipFile(original) as src,zipfile.ZipFile(apk,'w') as dst:
    for info in src.infolist():dst.writestr(info,(O/'classes2.dex').read_bytes() if info.filename=='classes2.dex' else src.read(info.filename))
with zipfile.ZipFile(original) as a,zipfile.ZipFile(apk) as b:
    assert a.namelist()==b.namelist()
    changed=[n for n in a.namelist() if a.read(n)!=b.read(n)]
    assert changed==['classes2.dex'],changed
report={'apkSha256':hashlib.sha256(apk.read_bytes()).hexdigest(),'changedEntries':changed,'translatedGetters':['getTitle','getContent','getJumpButtonTitle'],'translations':translations,'placeLabels':len(places),'locationInfoModified':False,'catalogStrings':len(catalog),'catalogDisplayCalls':sum(x['calls'] for x in catalog_sites),'catalogModelsModified':False}
(O/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=True))
