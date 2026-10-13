from pathlib import Path
import os,re,json,shutil,subprocess,zipfile,hashlib
H=Path(__file__).resolve().parent;ROOT=H.parents[1];W=Path(os.environ['TEMP'])/'beam-gmservice-build';W.mkdir(exist_ok=True);S=Path(os.environ['TEMP'])/'beam-gmservice-code';SP=Path(r'C:\Users\USER\AppData\Local\Temp\claude\C--Users-USER-TileLauncher\4a103049-a7f5-4062-923c-147b4e6834ae\scratchpad');J=Path(r'C:\android\jdk\bin')
shutil.copytree(S/'smali_classes2',W/'smali_classes2',dirs_exist_ok=True)
d=json.loads((H/'display-translations.json').read_text(encoding='utf-8'));code=['.class public final Lcom/xgimi/xgimiservice/BeamRu;','.super Ljava/lang/Object;','','.method public static text(Ljava/lang/String;)Ljava/lang/String;','    .locals 3','    if-eqz p0, :fallback']
for i,(old,new) in enumerate(d.items()):
 code += ['    const-string v0, '+json.dumps(old,ensure_ascii=False),'    invoke-virtual {v0, p0}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z','    move-result v1',f'    if-eqz v1, :next_{i}','    const-string v0, '+json.dumps(new,ensure_ascii=False),'    return-object v0',f'    :next_{i}']
for i,old in enumerate(['当前保修服务到期时间: ','问题分类/','请完成']):
 new=d[old];new += ' ' if old=='请完成' else ''
 code += ['    const-string v0, '+json.dumps(old,ensure_ascii=False),'    invoke-virtual {p0, v0}, Ljava/lang/String;->startsWith(Ljava/lang/String;)Z','    move-result v1',f'    if-eqz v1, :prefix_{i}','    invoke-virtual {v0}, Ljava/lang/String;->length()I','    move-result v1','    invoke-virtual {p0, v1}, Ljava/lang/String;->substring(I)Ljava/lang/String;','    move-result-object v2','    const-string v0, '+json.dumps(new,ensure_ascii=False),'    invoke-virtual {v0, v2}, Ljava/lang/String;->concat(Ljava/lang/String;)Ljava/lang/String;','    move-result-object v0','    return-object v0',f'    :prefix_{i}']
code += ['    :fallback','    return-object p0','.end method','','.method public static setText(Lcom/xgimi/view/cell/component/TextComponent;Ljava/lang/String;)Lcom/xgimi/view/cell/component/TextComponent;','    .locals 1','    invoke-static {p1}, Lcom/xgimi/xgimiservice/BeamRu;->text(Ljava/lang/String;)Ljava/lang/String;','    move-result-object v0','    invoke-virtual {p0, v0}, Lcom/xgimi/view/cell/component/TextComponent;->setText(Ljava/lang/String;)Lcom/xgimi/view/cell/component/TextComponent;','    move-result-object v0','    return-object v0','.end method','']
code += ['.method public static chars(Ljava/lang/CharSequence;)Ljava/lang/CharSequence;', '    .locals 1', '    instance-of v0, p0, Ljava/lang/String;', '    if-eqz v0, :end', '    check-cast p0, Ljava/lang/String;', '    invoke-static {p0}, Lcom/xgimi/xgimiservice/BeamRu;->text(Ljava/lang/String;)Ljava/lang/String;', '    move-result-object p0', '    :end', '    return-object p0', '.end method', '']
code += ['.method public static viewText(Landroid/widget/TextView;Ljava/lang/CharSequence;)V', '    .locals 1', '    invoke-static {p1}, Lcom/xgimi/xgimiservice/BeamRu;->chars(Ljava/lang/CharSequence;)Ljava/lang/CharSequence;', '    move-result-object v0', '    invoke-virtual {p0, v0}, Landroid/widget/TextView;->setText(Ljava/lang/CharSequence;)V', '    return-void', '.end method', '']
code += ['.method public static toast(Landroid/content/Context;Ljava/lang/CharSequence;I)Landroid/widget/Toast;', '    .locals 1', '    invoke-static {p1}, Lcom/xgimi/xgimiservice/BeamRu;->chars(Ljava/lang/CharSequence;)Ljava/lang/CharSequence;', '    move-result-object v0', '    invoke-static {p0, v0, p2}, Landroid/widget/Toast;->makeText(Landroid/content/Context;Ljava/lang/CharSequence;I)Landroid/widget/Toast;', '    move-result-object v0', '    return-object v0', '.end method', '']
code += ['.method public static showToast(Lcom/xgimi/utils/common/ToastUtil;Landroid/content/Context;Ljava/lang/String;I)V', '    .locals 1', '    invoke-static {p2}, Lcom/xgimi/xgimiservice/BeamRu;->text(Ljava/lang/String;)Ljava/lang/String;', '    move-result-object v0', '    invoke-virtual {p0, p1, v0, p3}, Lcom/xgimi/utils/common/ToastUtil;->showToast(Landroid/content/Context;Ljava/lang/String;I)V', '    return-void', '.end method', '']
helper=W/'smali_classes2/com/xgimi/xgimiservice/BeamRu.smali';helper.write_text('\n'.join(code),encoding='utf-8');changed={}
pattern=r'invoke-virtual (\{[^}]+\}), Lcom/xgimi/view/cell/component/TextComponent;->setText\(Ljava/lang/String;\)Lcom/xgimi/view/cell/component/TextComponent;'
for p in (W/'smali_classes2/com/xgimi/xgimiservice').rglob('*.smali'):
 if p==helper:continue
 s=p.read_text(encoding='utf-8');out,n=re.subn(pattern,r'invoke-static \1, Lcom/xgimi/xgimiservice/BeamRu;->setText(Lcom/xgimi/view/cell/component/TextComponent;Ljava/lang/String;)Lcom/xgimi/view/cell/component/TextComponent;',s)
 for old,new in [
  ('invoke-virtual','Landroid/widget/TextView;->setText(Ljava/lang/CharSequence;)V'),
  ('invoke-static','Landroid/widget/Toast;->makeText(Landroid/content/Context;Ljava/lang/CharSequence;I)Landroid/widget/Toast;'),
  ('invoke-virtual','Lcom/xgimi/utils/common/ToastUtil;->showToast(Landroid/content/Context;Ljava/lang/String;I)V')]:
  destination={'Landroid/widget/TextView;->setText(Ljava/lang/CharSequence;)V':'viewText(Landroid/widget/TextView;Ljava/lang/CharSequence;)V',
   'Landroid/widget/Toast;->makeText(Landroid/content/Context;Ljava/lang/CharSequence;I)Landroid/widget/Toast;':'toast(Landroid/content/Context;Ljava/lang/CharSequence;I)Landroid/widget/Toast;',
   'Lcom/xgimi/utils/common/ToastUtil;->showToast(Landroid/content/Context;Ljava/lang/String;I)V':'showToast(Lcom/xgimi/utils/common/ToastUtil;Landroid/content/Context;Ljava/lang/String;I)V'}[new]
  out,count=re.subn(old+r' (\{[^}]+\}), '+re.escape(new),lambda m:'invoke-static '+m[1]+', Lcom/xgimi/xgimiservice/BeamRu;->'+destination,out);n+=count
 if p.name=='GMExtendedWarranty.smali':
  old='const/high16 p4, 0x41e00000    # 28.0f';assert out.count(old)==1;out=out.replace(old,'const/high16 p4, 0x41b00000    # 22.0f')
 if n:
  rel=p.relative_to(W/'smali_classes2');changed[str(rel)]=n;p.write_text(out,encoding='utf-8');dest=H/'native-source'/rel;dest.parent.mkdir(exist_ok=True,parents=True);dest.write_text(out,encoding='utf-8');dest.with_suffix('.before.smali').write_text(s,encoding='utf-8')
shutil.copy(helper,H/'native-source/BeamRu.smali');assert sum(changed.values())>=35,sum(changed.values())
subprocess.run([str(J/'javac.exe'),'-cp',str(SP/'apktool.jar'),'-d',str(W),str(ROOT/'investigation/quick-panel-brightness-2026-10-08/BuildDex.java')],check=True)
subprocess.run([str(J/'java.exe'),'-Xmx2g','-cp',str(SP/'apktool.jar')+';'+str(W),'BuildDex',str(W/'smali_classes2'),str(W/'classes2.dex')],check=True)
base=H/'gmservice-original.apk';out=H/'gmservice-native.apk'
with zipfile.ZipFile(base) as src,zipfile.ZipFile(out,'w') as dest:
 for info in src.infolist():dest.writestr(info,(W/'classes2.dex').read_bytes() if info.filename=='classes2.dex' else src.read(info.filename))
with zipfile.ZipFile(base) as src,zipfile.ZipFile(out) as dest:assert [n for n in src.namelist() if src.read(n)!=dest.read(n)]==['classes2.dex']
shutil.copy(out,ROOT/'russifier/payload/gmservice-native.apk');report={'displayTranslations':len(d),'displayCalls':sum(changed.values()),'changedClasses':changed,'changedEntries':['classes2.dex'],'originalSha256':hashlib.sha256(base.read_bytes()).hexdigest(),'nativeSha256':hashlib.sha256(out.read_bytes()).hexdigest()};(H/'native-build.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report,indent=2))
