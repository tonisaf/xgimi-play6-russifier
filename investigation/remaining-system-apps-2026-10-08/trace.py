from pathlib import Path
import json,re,xml.etree.ElementTree as E

OUT=Path(__file__).resolve().parent
SP=Path(r'C:\Users\USER\AppData\Local\Temp\claude\C--Users-USER-TileLauncher\4a103049-a7f5-4062-923c-147b4e6834ae\scratchpad')
data=json.loads((OUT/'translations.json').read_text(encoding='utf-8'))
report={}
for app,values in data.items():
    ids={x.get('id'):x.get('name') for x in E.parse(SP/'res6'/app/'res/values/public.xml').getroot() if x.get('type')=='string' and x.get('name') in values}
    found={k:[] for k in values}
    for f in (SP/('smali_'+app)).glob('smali*/com/xgimi/**/*.smali'):
        if f.name.startswith('R$'):continue
        try:lines=f.read_text(encoding='utf-8').splitlines()
        except OSError:continue
        for i,line in enumerate(lines):
            matches=[ids.get(resource) for resource in re.findall(r'0x7f[0-9a-f]{6}',line)]
            matches+=re.findall(r'R\$string;->(\w+):I',line)
            for key in matches:
                if key in found and len(found[key])<3:
                    found[key].append({'file':str(f.relative_to(SP/('smali_'+app))), 'line':i+1,'context':'\n'.join(lines[max(0,i-3):i+14])})
    for f in (SP/'res6'/app/'res').rglob('*.xml'):
        if f.parent.name.startswith('values'):continue
        text=f.read_text(encoding='utf-8')
        for key in values:
            if '@string/'+key in text and len(found[key])<3:found[key].append({'file':str(f.relative_to(SP/'res6'/app)),'layout':True})
    report[app]=found
    print(app,'referenced',sum(bool(v) for v in found.values()),'of',len(values))
(OUT/'source-evidence.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
