"""Verify compiled method scope and prior overlay resource preservation, offline."""
from pathlib import Path
import hashlib, json, subprocess, zipfile
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'investigation/photo-fixes-2026-10-12'
def methods(p): return {m['method']:m for m in map(json.loads,p.read_text(encoding='utf-8-sig').splitlines())}
report={}
for package,name,stem in [('com.android.newsettings','panel.apk','panel'),('com.xgimi.systemui','systemui-native.apk','systemui')]:
    old=methods(ROOT/'.local/table-20261012'/('ours-'+package+'-methods.jsonl'))
    new=methods(OUT/(stem+'-methods.jsonl'))
    assert not old.keys()-new.keys()
    changed=[key for key in old if old[key]!=new[key]]
    if stem=='panel':
        assert len(changed)==3,changed
        for key in changed:
            assert 'BluPairRequestReceiver;->handleNotNfcTouch(' in key or 'BluetoothDevicesPairDialog;->' in key,key
            assert old[key]['shape']==new[key]['shape'],key
        values=[s for key in changed for s in new[key]['strings']]
        assert '» запрашивает сопряжение по Bluetooth' in values
        assert 'Сопряжение' in values and 'Выполняется сопряжение' in values
        assert '” 请求蓝牙配对' not in values and '配对' not in values
        assert old.keys()==new.keys()
    else:
        assert not changed,changed # Existing opcode shapes/literals preserved; only title call references changed.
        added=list(new.keys()-old.keys())
        assert len(added)==2 and all('ExpandViewModel;->createBeamTitleCell' in key for key in added),added
    report[stem]={'existingMethods':len(old),'changedStringsMethods':changed,'addedMethods':list(new.keys()-old.keys())}
    with zipfile.ZipFile(OUT/'before'/name) as a,zipfile.ZipFile(ROOT/'russifier/payload'/name) as b:
        assert a.namelist()==b.namelist()
        assert [n for n in a.namelist() if a.read(n)!=b.read(n)]==['classes2.dex']
old=json.loads((OUT/'before/manifest.json').read_text(encoding='utf-8'))
new=json.loads((ROOT/'russifier/manifest.json').read_text(encoding='utf-8'))
assert new['version']=='1.19.16'
changed=[n for n in old['files'] if old['files'][n]!=new['files'][n]]
assert set(changed)=={'panel.apk','systemui-native.apk','systemui.apk','ambient.apk'},changed
systemui=next(p for p in new['runtimePatches'] if p['file']=='systemui-native.apk')
assert old['files']['systemui-native.apk'] in systemui['previousHashes']
generation=(ROOT/'investigation/bound-startup-2026-10-08/apply.sh').read_text(encoding='utf-8')
assert old['files']['systemui-native.apk'] in generation
decoded=Path('C:/android/photo-systemui-verified-20261012/smali_classes2/com/xgimi/systemui')
model=(decoded/'ui/dialog/ExpandViewModel.smali').read_text(encoding='utf-8')
start=model.index('.method public final createBeamTitleCell(')
body=model[start:model.index('.end method',start)]
assert 'const/high16 v3, 0x42400000' in body
assert 'const/16 v3, 0x1' in body and '->setMaxLine(I)' in body
factory=(decoded/'remote/RemoteDialogFactory.smali').read_text(encoding='utf-8')
assert factory.count('->createBeamTitleCell$default(')==2
assert (decoded/'ambientlight/AmbientLightStudyActivity.smali').read_text(encoding='utf-8').count('->createBeamTitleCell(')==1
report['layout']={'compiledTitleFontSize':48,'compiledTitleMaxLines':1,'targetScreens':3,'verifiedPreviousSystemuiAccepted':True}
for name,digest in new['files'].items():
    assert hashlib.sha256((ROOT/'russifier/payload'/name).read_bytes()).hexdigest()==digest,name
for name in ['systemui.apk','ambient.apk']:
    # Compare independent aapt2 dumps of the compiled output.
    def decode_values(p):
        import re
        text=subprocess.check_output(['C:/android/sdk/build-tools/34.0.0/aapt2.exe','dump','resources',str(p)],encoding='utf-8')
        resources={}; current=None
        for line in text.splitlines():
            match=re.search(r'resource 0x[0-9a-f]+ ([^ ]+)',line)
            if match: current=match.group(1);resources[current]=[]
            elif current and re.match(r'\s+\(',line): resources[current].append(line.strip())
        return resources
    before=decode_values(OUT/'before'/name);after=decode_values(ROOT/'russifier/payload'/name)
    updates=json.loads((OUT/'build-report.json').read_text(encoding='utf-8'))[name.removesuffix('.apk')]
    assert not before.keys()-after.keys()
    for key,values in before.items():
        if key.startswith('string/') and key[7:] not in updates: assert values==after[key],(name,key,values,after[key])
    report[name]={'beforeResources':len(before),'afterResources':len(after),'updatedStrings':len(updates)}
(OUT/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2))
