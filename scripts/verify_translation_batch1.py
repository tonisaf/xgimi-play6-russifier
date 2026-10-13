"""Check compiled first-batch values and preserved comparison workbook, offline."""
from pathlib import Path
import hashlib,json,re,subprocess,zipfile
import xml.etree.ElementTree as ET
from build_translation_batch1 import TRANSLATIONS
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'investigation/translation-batch1-2026-10-12'
current=json.loads((ROOT/'russifier/manifest.json').read_text(encoding='utf-8'))
before=json.loads((OUT/'before/manifest.json').read_text(encoding='utf-8'))
assert current['version']=='1.19.17'
assert [n for n in before['files'] if before['files'][n]!=current['files'][n]]==['systemui.apk']
for name,digest in current['files'].items():
    assert hashlib.sha256((ROOT/'russifier/payload'/name).read_bytes()).hexdigest()==digest,name
def dump(path):
    text=subprocess.check_output(['C:/android/sdk/build-tools/34.0.0/aapt2.exe','dump','resources',str(path)],encoding='utf-8')
    resources={};key=None
    for line in text.splitlines():
        match=re.search(r'resource 0x[0-9a-f]+ ([^ ]+)',line)
        if match:key=match[1];resources[key]=[]
        elif key and re.match(r'\s+\(',line):resources[key].append(line.strip())
    return resources
old=dump(OUT/'before/systemui.apk');new=dump(ROOT/'russifier/payload/systemui.apk')
assert not old.keys()-new.keys()
for key,values in old.items(): assert new[key]==values,(key,values,new[key])
for key,value in TRANSLATIONS.items():
    assert 'string/'+key in new,key
    assert all(value in line for line in new['string/'+key]),key
ns={'s':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
def workbook(path):
    with zipfile.ZipFile(path) as z:
        strings=[]
        if 'xl/sharedStrings.xml' in z.namelist():
            strings=[''.join(n.itertext()) for n in ET.fromstring(z.read('xl/sharedStrings.xml')).findall('s:si',ns)]
        sheets=[]
        for i in range(1,5):
            root=ET.fromstring(z.read(f'xl/worksheets/sheet{i}.xml'))
            values={}
            for c in root.findall('.//s:sheetData/s:row/s:c',ns):
                assert c.get('t')!='e',(i,c.attrib)
                v=c.find('s:v',ns)
                if c.get('t')=='s':value=strings[int(v.text)]
                elif c.get('t')=='inlineStr':value=''.join(c.find('s:is',ns).itertext())
                else:value=v.text if v is not None else None
                if value is not None:values[c.get('r')]=value
            sheets.append((root,values))
        tables=[ET.fromstring(z.read(n)) for n in z.namelist() if n.startswith('xl/tables/table') and n.endswith('.xml')]
        assert len(tables)==4
        return sheets,tables
baseline,tables0=workbook(ROOT/'outputs/translation-review-20261012/XGIMI-Play6-Titan-Translation-2026-10-12.xlsx')
edited,tables=workbook(ROOT/'outputs/translation-review-20261012/XGIMI-Play6-Titan-Translation-1.19.17.xlsx')
assert baseline[2][1]==edited[2][1],'Unrelated array sheet values changed'
assert edited[0][1]['B5']=='1.19.17'
assert [int(edited[0][1][f'E{i}']) for i in [4,5,6]]==[12001,2386,404]
data=json.loads((ROOT/'investigation/titan-2026-10-12/translation-table-1.19.17/table-data.json').read_text(encoding='utf-8'))
indexed={(r['package'],r['resource']):r for r in data['strings']}
v=edited[1][1];oldv=baseline[1][1]
added=deferred=photos=0
for row in range(6,12007):
    key=(v[f'N{row}'],v[f'B{row}']);r=indexed[key]
    for col in ['A','B','C','D','I','J','K','L','M','N']:
        assert oldv.get(f'{col}{row}')==v.get(f'{col}{row}'),(col,row)
    actual=v.get(f'E{row}')
    assert actual==r['ours'] or (isinstance(r['ours'],str) and r['ours'].startswith('=') and actual=="'"+r['ours']),(key,actual,r['ours'])
    if v.get(f'G{row}')=='Добавлено 1.19.17':
        added+=1;assert r['ours']==TRANSLATIONS[r['resource'].removeprefix('string/')]
        assert v[f'S{row}']=='1.19.17'
    if v.get(f'G{row}')=='Отложено':deferred+=1
    if v.get(f'R{row}'):photos+=1;assert 'требуется повторная проверка' in v[f'P{row}']
assert added==16 and deferred==2 and photos==13,(added,deferred,photos)
candidateCount=sum(v.get(f'G{i}')=='Кандидат' for i in range(6,12007))
assert sum(int(edited[0][1][f'H{i}']) for i in range(10,24))==candidateCount==372
for root,_ in edited[1:]:
    pane=root.find('.//s:pane',ns);assert pane.get('xSplit')=='2' and pane.get('ySplit')=='5'
assert edited[1][0].find('.//s:dataValidation',ns).get('sqref')=='O6:O12006'
for t in tables:
    if t.get('name')=='TranslationStrings':assert t.get('ref')=='A5:S12006'
    if t.get('name')!='CoverageSummary':assert t.find('s:autoFilter',ns) is not None
report={'version':'1.19.17','compiledNewStrings':16,'compiledOldResourcesPreserved':len(old),'nativeApksUnchanged':True,
        'workbookRows':[12001,2386,404],'reviewedAdded':added,'deferred':deferred,'photoEvidenceRows':photos,
        'remainingCandidates':candidateCount,'originalStockAndTitanPreserved':True,'arraySheetPreserved':True,
        'nativeTablesFiltersFreezePanesDecisionValidation':True,'deviceConnected':False}
(OUT/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report,ensure_ascii=False))
