"""Patch the verified 1.12.0 panel, retaining every other ZIP entry."""
from pathlib import Path
import hashlib, json, os, shutil, subprocess, zipfile

H = Path(__file__).resolve().parent
ROOT = H.parents[1]
SDK = Path(os.environ.get('ANDROID_HOME', r'C:\android\sdk'))
JDK = Path(os.environ.get('JAVA_HOME', r'C:\android\jdk')) / 'bin'
SP = Path(os.environ.get('BEAM_SCRATCHPAD', r'C:\Users\USER\AppData\Local\Temp\claude\C--Users-USER-TileLauncher\4a103049-a7f5-4062-923c-147b4e6834ae\scratchpad'))
W = Path(os.environ['TEMP']) / 'beam-quick-status-build'
W.mkdir(exist_ok=True)
BASELINE = H / 'baseline-panel.apk'
if not BASELINE.exists():
    shutil.copy2(ROOT / 'russifier/payload/panel.apk', BASELINE)
assert hashlib.sha256(BASELINE.read_bytes()).hexdigest() == '5166aab4c90b061d038c3ee18832e161421dccdc234d100d428c3d9d2d1f70cd'
with zipfile.ZipFile(BASELINE) as z:
    dex = z.read('classes4.dex')
assert hashlib.sha256(dex).hexdigest() == 'aa0f0b65991c32d89c517b028d92a652aa94f31074388ddacbb5f7005a5589d5'
(W / 'baseline.dex').write_bytes(dex)
java = str(JDK / 'java.exe')
jar = SP / 'apktool.jar'
smali = W / 'smali'
subprocess.run([str(JDK / 'javac.exe'), '-cp', str(jar), '-d', str(W), str(H / 'DisassembleDex.java')], check=True)
subprocess.run([java, '-cp', str(jar) + ';' + str(W), 'DisassembleDex', str(W / 'baseline.dex'), str(smali)], check=True)

def patch_method(path, signature, mode, code):
    text = path.read_text(encoding='utf-8')
    start = text.index(signature)
    end = text.index('.end method', start)
    method = text[start:end]
    if mode == 'start':
        marker = '    .line 177\n'
        assert method.count(marker) == 1
        method = method.replace(marker, code + '\n' + marker)
    else:
        pos = method.rindex('    return-void')
        method = method[:pos] + code + '\n' + method[pos:]
    path.write_text(text[:start] + method + text[end:], encoding='utf-8')

cell = smali / 'com/xgimi/misckey/cell'
patch_method(cell / 'NormalRowItem.smali', '.method private final dealDataToUIData(', 'start',
    '    invoke-static {p1}, Lcom/xgimi/misckey/cell/BeamQuickStatus;->augment(Ljava/util/List;)Ljava/util/List;\n    move-result-object p1')
for signature in ('.method public final setFuncData(', '.method private final changeViewByFocus('):
    patch_method(cell / 'NormalFuncItem.smali', signature, 'end',
        '    invoke-static {p0}, Lcom/xgimi/misckey/cell/BeamQuickStatus;->refresh(Ljava/lang/Object;)V')
for method, helper in (('onAttach', 'attach'), ('onDetached', 'detach')):
    patch_method(cell / 'NormalFuncItem$2.smali', '.method public ' + method + '(', 'end',
        '    iget-object v0, p0, Lcom/xgimi/misckey/cell/NormalFuncItem$2;->this$0:Lcom/xgimi/misckey/cell/NormalFuncItem;\n'
        '    invoke-static {v0}, Lcom/xgimi/misckey/cell/BeamQuickStatus;->' + helper + '(Ljava/lang/Object;)V')

classes = W / 'classes'
classes.mkdir(exist_ok=True)
subprocess.run([str(JDK / 'javac.exe'), '-encoding', 'UTF-8', '-source', '8', '-target', '8', '-cp', str(SDK / 'platforms/android-34/android.jar'), '-d', str(classes), str(H / 'BeamQuickStatus.java')], check=True)
helper = W / 'helper'
helper.mkdir(exist_ok=True)
subprocess.run([java, '-cp', str(SDK / 'build-tools/34.0.0/lib/d8.jar'), 'com.android.tools.r8.D8', '--min-api', '30', '--lib', str(SDK / 'platforms/android-34/android.jar'), '--output', str(helper)] + [str(p) for p in classes.rglob('*.class')], check=True)
subprocess.run([java, '-cp', str(jar) + ';' + str(W), 'DisassembleDex', str(helper / 'classes.dex'), str(W / 'helper-smali')], check=True)
for p in (W / 'helper-smali').rglob('*.smali'):
    target = smali / p.relative_to(W / 'helper-smali')
    assert not target.exists() or target.name.startswith('BeamQuickStatus'), target
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(p, target)
subprocess.run([str(JDK / 'javac.exe'), '-cp', str(jar), '-d', str(W), str(ROOT / 'investigation/quick-panel-brightness-2026-10-08/BuildDex.java')], check=True)
subprocess.run([java, '-Xmx2g', '-cp', str(jar) + ';' + str(W), 'BuildDex', str(smali), str(W / 'classes4.dex')], check=True)
output = H / 'panel-audio-bluetooth.apk'
with zipfile.ZipFile(BASELINE) as source, zipfile.ZipFile(output, 'w') as target:
    for info in source.infolist():
        target.writestr(info, (W / 'classes4.dex').read_bytes() if info.filename == 'classes4.dex' else source.read(info.filename))
with zipfile.ZipFile(BASELINE) as source, zipfile.ZipFile(output) as target:
    changed = [n for n in source.namelist() if source.read(n) != target.read(n)]
    assert changed == ['classes4.dex'], changed
report = {'originalBaseline': hashlib.sha256(BASELINE.read_bytes()).hexdigest(), 'sha256': hashlib.sha256(output.read_bytes()).hexdigest(), 'changedEntries': changed}
(H / 'build.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
print(json.dumps(report))
