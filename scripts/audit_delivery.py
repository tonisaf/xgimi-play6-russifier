"""Read-only payload/hash, text and DEX candidate audit; does not connect to ADB."""
import argparse,collections,json,re,struct,zipfile
from pathlib import Path
import hashlib

ROOT=Path(__file__).resolve().parents[1]
CJK=re.compile('[\u3400-\u9fff]')
FORMAT=re.compile(r'%(?:(\d+)\$)?[-#+ 0,(<]*\d*(?:\.\d+)?([a-zA-Z%])')

def contract(text):
    implicit=0;result=[]
    for match in FORMAT.finditer(text):
        index,kind=match.groups()
        if kind in ('n','%'): continue
        if index: slot=int(index)
        else: implicit+=1;slot=implicit
        result.append((slot,kind.lower()))
    return sorted(result)

def dex_strings(data):
    if data[:4]!=b'dex\x0a': raise ValueError('Not a DEX')
    size,offset=struct.unpack_from('<II',data,0x38)
    for index in range(size):
        position=struct.unpack_from('<I',data,offset+index*4)[0]
        # Skip the ULEB128 UTF-16 length, then read modified UTF-8 bytes.
        for _ in range(5):
            byte=data[position];position+=1
            if byte<128: break
        end=data.index(0,position)
        yield data[position:end].replace(b'\xc0\x80',b'\x00').decode('utf-8',errors='replace')

def audit(output):
    manifest=json.loads((ROOT/'russifier/manifest.json').read_text(encoding='utf-8'))
    report={'version':manifest['version'],'payload':{},'formatCandidates':[],
            'nonRussianResourceCandidates':[],'dex':{},'limits':['DEX candidates include logs, protocols and unused UI; rendering is not tested.']}
    for name,expected in manifest['files'].items():
        path=ROOT/'russifier/payload'/name
        actual=hashlib.sha256(path.read_bytes()).hexdigest()
        report['payload'][name]={'sha256':actual,'matches':actual==expected,'bytes':path.stat().st_size}
    checks=manifest['resourceChecks']
    for target,strings in checks.items():
        for key,value in strings.items():
            if CJK.search(value): report['nonRussianResourceCandidates'].append({'target':target,'key':key,'value':value})
    cached=ROOT/'investigation/main-settings-native-2026-10-08/resources.json'
    if cached.exists():
        matched=0
        for item in json.loads(cached.read_text(encoding='utf-8')):
            key=item['key'];translated=checks.get('com.android.newsettings',{}).get(key)
            if translated is None: continue
            matched+=1
            if contract(item['original'])!=contract(translated):
                report['formatCandidates'].append({'key':key,'original':item['original'],'translation':translated})
        report['formatChecksAgainstCachedOriginal']=matched
    for name in ['panel.apk']+[item['file'] for item in manifest.get('runtimePatches',[])]:
        found=collections.Counter()
        with zipfile.ZipFile(ROOT/'russifier/payload'/name) as apk:
            for entry in apk.namelist():
                if re.fullmatch(r'classes\d*\.dex',entry):
                    for value in dex_strings(apk.read(entry)):
                        if CJK.search(value) and len(value)<=300: found[value]+=1
        # Candidates only, not an automatic patch list.
        report['dex'][name]={'uniqueShortCjkStrings':len(found),'samples':list(found)[:150],
                             'strings':[{'text':text,'occurrences':count} for text,count in found.items()]}
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    summary={'version':manifest['version'],'payloadFiles':len(report['payload']),
             'payloadMatch':all(x['matches'] for x in report['payload'].values()),
             'formatChecks':report.get('formatChecksAgainstCachedOriginal',0),
             'formatCandidates':len(report['formatCandidates']),
             'cjkResourceCandidates':len(report['nonRussianResourceCandidates']),
             'dexCjkCandidates':{name:x['uniqueShortCjkStrings'] for name,x in report['dex'].items()}}
    print(json.dumps(summary,ensure_ascii=False));return summary

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,default=ROOT/'investigation/offline-delivery-2026-10-09/text-audit.json')
    audit(parser.parse_args().output)
