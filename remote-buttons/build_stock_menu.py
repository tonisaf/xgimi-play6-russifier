from pathlib import Path
import shutil,subprocess,zipfile,hashlib,json,os
root=Path(__file__).resolve().parents[1]
import argparse
parser=argparse.ArgumentParser()
parser.add_argument('--work',type=Path,required=True)
parser.add_argument('--base',type=Path,required=True,help='Verified panel APK from release 1.19.10')
parser.add_argument('--apktool',type=Path,default=root/'.local/build-tools/apktool-2.10.0.jar')
args=parser.parse_args()
base=args.base.resolve()
expected='a901619a3559e19bf62764b89816eb0d026db6fbc4cde453b54cb0cf52a97e2f'
if hashlib.sha256(base.read_bytes()).hexdigest()!=expected:
 raise RuntimeError('Requires verified panel 1.19.10; input is never overwritten')
tool=json.loads((root/'remote-buttons/tools.json').read_text(encoding='utf-8'))
jar=args.apktool.resolve()
if not jar.is_file() or hashlib.sha256(jar.read_bytes()).hexdigest()!=tool['apktoolSha256']:
 raise RuntimeError('Pinned APKTool missing/corrupt; run python scripts/fetch_apktool.py')
j=Path(os.environ.get('JAVA_HOME','C:/android/jdk'))/'bin'
w=args.work.resolve();w.mkdir(exist_ok=False,parents=True)
s=w/'decoded/smali_classes5'
subprocess.run([str(j/'java.exe'),'-jar',str(jar),'decode','--no-res','-o',str(w/'decoded'),str(base)],check=True)
before={p.relative_to(s).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in s.rglob('*.smali')}
p=s/'com/xgimi/newsettings/widget/settingtree/pages/Page2Cell.smali';t=p.read_text(encoding='utf-8')
needle='    .line 346\n    :cond_2\n'
assert t.count(needle)==1
insert='''    invoke-virtual {p1}, Lcom/xgimi/core/bean/PageNode;->getNodeId()Ljava/lang/String;
    move-result-object v2
    iget-object v3, p0, Lcom/xgimi/newsettings/widget/settingtree/pages/Page2Cell;->cellFactory:Lcom/xgimi/newsettings/CellFactory;
    iget-object v4, p0, Lcom/xgimi/newsettings/widget/settingtree/pages/Page2Cell;->owner:Landroidx/lifecycle/LifecycleOwner;
    invoke-static {v0, v2, v3, v4}, Lcom/xgimi/newsettings/widget/BeamRemoteEntry;->append(Lcom/xgimi/view/cell/Cell;Ljava/lang/String;Lcom/xgimi/newsettings/CellFactory;Landroidx/lifecycle/LifecycleOwner;)V
'''
p.write_text(t.replace(needle,needle+insert),encoding='utf-8')
helper='''.class public final Lcom/xgimi/newsettings/widget/BeamRemoteEntry;
.super Ljava/lang/Object;
.implements Lcom/xgimi/view/cell/CellEvent$OnClickListener;
.method public constructor <init>()V
 .locals 0
 invoke-direct {p0}, Ljava/lang/Object;-><init>()V
 return-void
.end method
.method public static append(Lcom/xgimi/view/cell/Cell;Ljava/lang/String;Lcom/xgimi/newsettings/CellFactory;Landroidx/lifecycle/LifecycleOwner;)V
 .locals 3
 const-string v0, "general_v2"
 invoke-virtual {v0, p1}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z
 move-result v0
 if-eqz v0, :done
 :try_start
 new-instance v0, Lcom/xgimi/contract/entity/BaseEntity;
 invoke-direct {v0}, Lcom/xgimi/contract/entity/BaseEntity;-><init>()V
 const-string v1, "Кнопки пульта"
 invoke-virtual {v0, v1}, Lcom/xgimi/contract/entity/BaseEntity;->setText(Ljava/lang/String;)V
 const-string v1, "beam.remote.buttons"
 invoke-virtual {v0, v1}, Lcom/xgimi/contract/entity/BaseEntity;->setAction(Ljava/lang/String;)V
 invoke-virtual {p2, p3, v0}, Lcom/xgimi/newsettings/CellFactory;->buildPage2ItemCell(Landroidx/lifecycle/LifecycleOwner;Lcom/xgimi/contract/entity/BaseEntity;)Lcom/xgimi/view/cell/Cell;
 move-result-object v0
 if-eqz v0, :done
 new-instance v1, Lcom/xgimi/newsettings/widget/BeamRemoteEntry;
 invoke-direct {v1}, Lcom/xgimi/newsettings/widget/BeamRemoteEntry;-><init>()V
 invoke-virtual {v0, v1}, Lcom/xgimi/view/cell/Cell;->setOnClickListener(Lcom/xgimi/view/cell/CellEvent$OnClickListener;)Lcom/xgimi/view/cell/Cell;
 invoke-virtual {p0, v0}, Lcom/xgimi/view/cell/Cell;->addCell(Lcom/xgimi/view/cell/Cell;)Lcom/xgimi/view/cell/Cell;
 :try_end
 .catch Ljava/lang/Exception; {:try_start .. :try_end} :error
 goto :done
 :error
 move-exception v0
 const-string v1, "BeamRemoteEntry"
 const-string v2, "append failed"
 invoke-static {v1, v2, v0}, Landroid/util/Log;->e(Ljava/lang/String;Ljava/lang/String;Ljava/lang/Throwable;)I
 :done
 return-void
.end method
.method public onClick(Lcom/xgimi/view/cell/Cell;)V
 .locals 4
 invoke-static {}, Lcom/xgimi/view/cell/Supports;->getContext()Landroid/app/Application;
 move-result-object v0
 :try_start
 new-instance v1, Landroid/content/Intent;
 invoke-direct {v1}, Landroid/content/Intent;-><init>()V
 const-string v2, "com.beam.remote"
 const-string v3, "com.beam.remote.RemoteActivity"
 invoke-virtual {v1, v2, v3}, Landroid/content/Intent;->setClassName(Ljava/lang/String;Ljava/lang/String;)Landroid/content/Intent;
 const/high16 v2, 0x10000000
 invoke-virtual {v1, v2}, Landroid/content/Intent;->addFlags(I)Landroid/content/Intent;
 invoke-virtual {v0, v1}, Landroid/content/Context;->startActivity(Landroid/content/Intent;)V
 :try_end
 .catch Ljava/lang/Exception; {:try_start .. :try_end} :error
 return-void
 :error
 move-exception v1
 const-string v1, "Установите модуль «Кнопки пульта»"
 const/4 v2, 0x0
 invoke-static {v0, v1, v2}, Landroid/widget/Toast;->makeText(Landroid/content/Context;Ljava/lang/CharSequence;I)Landroid/widget/Toast;
 move-result-object v0
 invoke-virtual {v0}, Landroid/widget/Toast;->show()V
 return-void
.end method
'''
(s/'com/xgimi/newsettings/widget/BeamRemoteEntry.smali').write_text(helper,encoding='utf-8')
shutil.copyfile(root/'scripts/BuildAtmosphereDex.java',w/'BuildDex.java')
after={p.relative_to(s).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in s.rglob('*.smali')}
changed=sorted(n for n in set(before)|set(after) if before.get(n)!=after.get(n))
assert changed==['com/xgimi/newsettings/widget/BeamRemoteEntry.smali','com/xgimi/newsettings/widget/settingtree/pages/Page2Cell.smali']
subprocess.run([str(j/'javac.exe'),'-cp',str(jar),'-d',str(w),str(w/'BuildDex.java')],check=True)
subprocess.run([str(j/'java.exe'),'-Xmx2g','-cp',str(jar)+os.pathsep+str(w),'BuildDex',str(s),str(w/'classes5.dex')],check=True)
shutil.copyfile(base,w/'panel-before.apk')
with zipfile.ZipFile(base) as a,zipfile.ZipFile(w/'panel.apk','w') as b:
 for i in a.infolist():b.writestr(i,(w/'classes5.dex').read_bytes() if i.filename=='classes5.dex' else a.read(i.filename))
with zipfile.ZipFile(base) as a,zipfile.ZipFile(w/'panel.apk') as b:assert [n for n in a.namelist() if a.read(n)!=b.read(n)]==['classes5.dex']
(w/'build-info.json').write_text(json.dumps({'baseSha256':expected,'apktoolSha256':tool['apktoolSha256'],'changedSmali':changed,'outputSha256':hashlib.sha256((w/'panel.apk').read_bytes()).hexdigest()},indent=2)+'\n',encoding='utf-8')
print(hashlib.sha256((w/'panel.apk').read_bytes()).hexdigest())
