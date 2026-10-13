"""Validate four original literals, then reassemble their unchanged smali instructions."""
from pathlib import Path
import hashlib,struct,zlib,json,zipfile,shutil,subprocess,os

OUT=Path(__file__).resolve().parent
SP=Path(r'C:\Users\USER\AppData\Local\Temp\claude\C--Users-USER-TileLauncher\4a103049-a7f5-4062-923c-147b4e6834ae\scratchpad')
base=SP/'apps/com.xgimi.wirelessscreen.apk'
assert hashlib.sha256(base.read_bytes()).hexdigest()=='061191874aa6aca4e747b27b25a5c3bb8937451572fb36d9f8e76c82ec63785a'
patches={'安卓手机 - ':'Android - ',' - 无线镜像':' — Wi-Fi','网络：':'Wi-Fi:','设备：':'Имя:'}
def read_uleb(data,offset):
    result=0;shift=0
    while True:
        b=data[offset];offset+=1;result|=(b&127)<<shift
        if b<128:return result,offset
        shift+=7
def encode_uleb(value):
    out=bytearray()
    while value>=128:out.append((value&127)|128);value>>=7
    out.append(value);return out

with zipfile.ZipFile(base) as src:
    original=src.read('classes3.dex');dex=bytearray(original)
    assert dex[:8]==b'dex\n035\x00' or dex[:4]==b'dex\n'
    count,table=struct.unpack_from('<II',dex,0x38);found={}
    for i in range(count):
        offset=struct.unpack_from('<I',dex,table+4*i)[0]
        length,start=read_uleb(dex,offset);end=dex.index(0,start)
        text=bytes(dex[start:end]).decode('utf-8',errors='replace')
        if text not in patches:continue
        value=patches[text];encoded=encode_uleb(len(value.encode('utf-16-le'))//2)+value.encode('utf-8')+b'\0'
        assert len(encoded)<=end+1-offset,(text,'replacement too long')
        assert text not in found,text
        dex[offset:end+1]=encoded+b'\0'*(end+1-offset-len(encoded))
        found[text]={'value':value,'offset':offset,'end':end+1}
    assert set(found)==set(patches),found
    dex[12:32]=hashlib.sha1(dex[32:]).digest()
    struct.pack_into('<I',dex,8,zlib.adler32(dex[12:])&0xffffffff)
    assert len(dex)==len(original)
    allowed=set(range(8,32))
    for x in found.values():allowed.update(range(x['offset'],x['end']))
    assert all(i in allowed for i,(a,b) in enumerate(zip(original,dex)) if a!=b)
    assert hashlib.sha1(dex[32:]).digest()==dex[12:32]
    assert struct.unpack_from('<I',dex,8)[0]==zlib.adler32(dex[12:])&0xffffffff
    # Reassemble to keep the DEX string_ids table sorted after replacing literals.
    # The in-place prototype above proves the four expected original strings exist.
    work=Path(os.environ['TEMP'])/'beam-wireless-native'
    work.mkdir(exist_ok=True)
    smali=work/'smali_classes3'
    shutil.copytree('\\\\?\\'+str(SP/'smali_wirelessscreen/smali_classes3'),smali,dirs_exist_ok=True)
    relative=Path('com/xgimi/wirelessscreen/activity/CastDetailActivity.smali')
    target=smali/relative;text=target.read_text(encoding='utf-8')
    (OUT/'CastDetailActivity.before.smali').write_text(text,encoding='utf-8')
    for old,value in patches.items():
        escaped=''.join('\\u%04x'%ord(c) if ord(c)>127 else c for c in old)
        assert text.count('"'+escaped+'"')==1,old
        text=text.replace('"'+escaped+'"','"'+value+'"')
    target.write_text(text,encoding='utf-8')
    (OUT/'CastDetailActivity.after.smali').write_text(text,encoding='utf-8')
    java=Path(r'C:\android\jdk\bin');builder=OUT.parent/'quick-panel-brightness-2026-10-08/BuildDex.java'
    subprocess.run([str(java/'javac.exe'),'-cp',str(SP/'apktool.jar'),'-d',str(work),str(builder)],check=True)
    subprocess.run([str(java/'java.exe'),'-Xmx2g','-cp',str(SP/'apktool.jar')+';'+str(work),'BuildDex',str(smali),str(work/'classes3.dex')],check=True)
    dex=(work/'classes3.dex').read_bytes()
    apk=OUT/'wirelessscreen-native.apk'
    with zipfile.ZipFile(apk,'w') as dst:
        for info in src.infolist():dst.writestr(info,dex if info.filename=='classes3.dex' else src.read(info.filename))
with zipfile.ZipFile(base) as src,zipfile.ZipFile(apk) as dst:
    changed=[n for n in src.namelist() if src.read(n)!=dst.read(n)]
    assert changed==['classes3.dex']
report={'sha256':hashlib.sha256(apk.read_bytes()).hexdigest(),'changedEntries':changed,'stringPatches':found,'smaliInstructionsPreservedExceptFourStringLiterals':True,'dexStringTableRebuiltAndSorted':True,'resourcesAndOriginalSignatureEntriesPreserved':True,'notForPackageManagerInstall':True}
(OUT/'native-build.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'sha256':report['sha256'],'strings':len(found)}))
