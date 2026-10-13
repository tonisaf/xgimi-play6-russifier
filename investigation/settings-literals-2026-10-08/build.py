from pathlib import Path
import hashlib, json, shutil, subprocess, zipfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SP = Path(r'C:\Users\USER\AppData\Local\Temp\claude\C--Users-USER-TileLauncher\4a103049-a7f5-4062-923c-147b4e6834ae\scratchpad')
WORK = Path(r'C:\Users\USER\AppData\Local\Temp\beam-settings-literals')
WORK.mkdir(exist_ok=True)
JAVA = Path(r'C:\android\jdk\bin')
base = ROOT/'russifier/payload/panel.apk'
assert hashlib.sha256(base.read_bytes()).hexdigest() == '3c60e71c641cd319ae7353c8d1565c4282c59996dd362a58e83d833f4c36c859'
patches = {
    5: {
        'com/xgimi/newsettings/ui/UIFactory.smali': (r'"\u89c6\u9891"', '"Видео"'),
        'com/xgimi/picture/PictureRepository.smali': (r'"\u89c6\u9891"', '"Видео"'),
        'com/xgimi/newsettings/widget/ImageModeTwoTitleCell.smali': (r'"\u5728\u7ebf/\u672c\u5730\u89c6\u9891"', '"Онлайн / локальное видео"'),
    },
    6: {},
}
signal = 'com/xgimi/signal/SignalRepository.smali'
old = '    invoke-virtual {v8, v2}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;\n\n    const-string v2, " \\u8bbe\\u7f6e"\n\n    invoke-virtual {v8, v2}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;'
new = '    move-object/16 v38, v2\n\n    const-string v2, "Настройки "\n\n    invoke-virtual {v8, v2}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;\n\n    move-object/from16 v2, v38\n\n    invoke-virtual {v8, v2}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;'
patches[6][signal] = (old, new)
builder = ROOT/'investigation/quick-panel-brightness-2026-10-08/BuildDex.java'
subprocess.run([str(JAVA/'javac.exe'), '-cp', str(SP/'apktool.jar'), '-d', str(WORK), str(builder)], check=True)
for num, files in patches.items():
    dst = WORK/f'smali_classes{num}'
    shutil.copytree('\\\\?\\'+str(SP/'ns_smali'/dst.name), dst, dirs_exist_ok=True)
    for name, (old, new) in files.items():
        p = dst/name
        text = p.read_text(encoding='utf-8')
        assert text.count(old) == 1, name
        out = HERE/'source'/name
        out.parent.mkdir(parents=True, exist_ok=True)
        (out.with_suffix('.before.smali')).write_text(text, encoding='utf-8')
        text = text.replace(old, new)
        p.write_text(text, encoding='utf-8')
        out.write_text(text, encoding='utf-8')
    subprocess.run([str(JAVA/'java.exe'), '-Xmx2g', '-cp', str(SP/'apktool.jar')+';'+str(WORK), 'BuildDex', str(dst), str(WORK/f'classes{num}.dex')], check=True)
apk = HERE/'beam-settings-panel-ru-v5.apk'
with zipfile.ZipFile(base) as src, zipfile.ZipFile(apk, 'w') as dest:
    for info in src.infolist():
        data = (WORK/info.filename).read_bytes() if info.filename in ('classes5.dex','classes6.dex') else src.read(info.filename)
        dest.writestr(info, data)
with zipfile.ZipFile(base) as src, zipfile.ZipFile(apk) as dest:
    changed = [n for n in src.namelist() if src.read(n) != dest.read(n)]
    assert set(changed) == {'classes5.dex','classes6.dex'}
    assert src.read('classes4.dex') == dest.read('classes4.dex')
report = {'sha256': hashlib.sha256(apk.read_bytes()).hexdigest(), 'baseSha256':hashlib.sha256(base.read_bytes()).hexdigest(), 'changedEntries': changed, 'preservedBrightnessDateBluetoothDex':True}
(HERE/'build.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
print(json.dumps(report))
