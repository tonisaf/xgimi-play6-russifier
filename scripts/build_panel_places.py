from pathlib import Path
import shutil,json,hashlib,re,subprocess,zipfile
import argparse
args=argparse.ArgumentParser();args.add_argument('--base',type=Path,required=True);args.add_argument('--decoded',type=Path,required=True);args.add_argument('--work',type=Path,required=True);args=args.parse_args()
ROOT=Path(__file__).resolve().parents[1];out=args.work.resolve();out.mkdir(exist_ok=False,parents=True)
source=args.decoded/'smali_classes2'
# Source is the pristine decode of the current 1.16.2 panel.
def longpath(p):return chr(92)*2+'?'+chr(92)+str(p.resolve())
shutil.copytree(longpath(source),longpath(out/'smali_classes2'),dirs_exist_ok=True)
s=out/'smali_classes2';old=args.base;digest=hashlib.sha256(old.read_bytes()).hexdigest()
assert digest=='54cb31fae61e190777ab000c29e26353447b55d12150d4df2356dd77ed6c3969'
p=s/'com/xgimi/common/selector/LocationSelectorCell$adapter$1.smali';data=p.read_text(encoding='utf-8');needle='    invoke-virtual {v0, p1}, Lcom/xgimi/view/cell/component/TextComponent;->setText(Ljava/lang/String;)Lcom/xgimi/view/cell/component/TextComponent;';assert data.count(needle)==1
p.write_text(data.replace(needle,'    invoke-static {p1}, Lcom/xgimi/common/selector/BeamPlace;->translate(Ljava/lang/String;)Ljava/lang/String;\n    move-result-object p1\n'+needle),encoding='utf-8')
places=json.loads((ROOT/'scripts/place-names-ru.json').read_text(encoding='utf-8'))
lines=['.class public final Lcom/xgimi/common/selector/BeamPlace;', '.super Ljava/lang/Object;', '.method public static translate(Ljava/lang/String;)Ljava/lang/String;', '    .locals 2']
for i,(src,dst) in enumerate(places.items()):
    lines += ['    const-string v0, '+json.dumps(src,ensure_ascii=False),'    invoke-virtual {v0, p0}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z','    move-result v1',f'    if-eqz v1, :next_{i}','    const-string v0, '+json.dumps(dst,ensure_ascii=False),'    return-object v0',f'    :next_{i}']
lines+=['    return-object p0','.end method']
helper='\n'.join(lines)+'\n'
(s/'com/xgimi/common/selector/BeamPlace.smali').write_text(helper,encoding='utf-8')
p=s/'com/xgimi/common/dialog/LocationSelectorDialog$rootCell$2.smali';data=p.read_text(encoding='utf-8')
for a,b in {'按':'Нажмите OK для сохранения','保存':''}.items():
 a=json.dumps(a,ensure_ascii=True);assert data.count(a)==1;p.write_text(data.replace(a,json.dumps(b,ensure_ascii=False)),encoding='utf-8');data=p.read_text(encoding='utf-8')
# A single centered label avoids the original three-cell hint overlapping in Russian.
data=p.read_text(encoding='utf-8')
start=data.index('    .line 169\n')
end=data.index('    .line 164\n',start)
data=data[:start]+'    invoke-virtual {v1, v2}, Lcom/xgimi/view/cell/Cell;->addCell(Lcom/xgimi/view/cell/Cell;)Lcom/xgimi/view/cell/Cell;\n\n    move-result-object v1\n\n'+data[end:]
p.write_text(data,encoding='utf-8')
shutil.copyfile(ROOT/'scripts/BuildAtmosphereDex.java',out/'BuildDex.java')
jar=r'C:/Users/USER/AppData/Local/Temp/claude/C--Users-USER-TileLauncher/4a103049-a7f5-4062-923c-147b4e6834ae/scratchpad/apktool.jar'
subprocess.run([r'C:/android/jdk/bin/javac.exe','-cp',jar,'-d',str(out),str(out/'BuildDex.java')],check=True)
subprocess.run([r'C:/android/jdk/bin/java.exe','-Xmx2g','-cp',jar+';'+str(out),'BuildDex',str(s),str(out/'classes2.dex')],check=True)
new=out/'panel.apk'
with zipfile.ZipFile(old) as src,zipfile.ZipFile(new,'w') as dst:
 for i in src.infolist():dst.writestr(i,(out/'classes2.dex').read_bytes() if i.filename=='classes2.dex' else src.read(i.filename))
with zipfile.ZipFile(old) as a,zipfile.ZipFile(new) as b:assert [n for n in a.namelist() if a.read(n)!=b.read(n)]==['classes2.dex']
shutil.copyfile(new,ROOT/'russifier/payload/panel.apk')
print(hashlib.sha256(new.read_bytes()).hexdigest())
