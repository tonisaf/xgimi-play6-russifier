"""Make static (isStatic=true) copies of the dynamic RRO payloads for /vendor/overlay.
Patches only the isStatic boolean in the binary manifest, keeps every other entry byte-identical,
removes the old v1 signature, zipaligns and re-signs with the debug key (same as scripts/build_*.py)."""
import struct, zipfile, subprocess, sys, shutil, hashlib, json
from pathlib import Path
BT=Path(r'C:\android\sdk\build-tools\34.0.0')
KS=Path.home()/'.android'/'debug.keystore'
ATTR_ISSTATIC=0x0101055a
def patch_manifest(data: bytes) -> bytes:
    b=bytearray(data)
    assert struct.unpack_from('<HH',b,0)[0]==0x0003
    off=8; attr_idx=None; done=0
    while off<len(b):
        t,hs,size=struct.unpack_from('<HHI',b,off)
        if t==0x0180:  # resource map: list of attr ids
            ids=struct.unpack_from('<%dI'%((size-8)//4),b,off+8)
            attr_idx=ids.index(ATTR_ISSTATIC)
        elif t==0x0102 and attr_idx is not None:  # start element
            attrStart,attrSize,attrCount=struct.unpack_from('<HHH',b,off+16+8)
            base=off+16+attrStart
            for i in range(attrCount):
                a=base+i*attrSize
                ans,aname,araw,vsize,res0,vtype,vdata=struct.unpack_from('<IIIHBBI',b,a)
                if aname==attr_idx:
                    assert vtype==0x12, vtype
                    struct.pack_into('<I',b,a+16,0xFFFFFFFF); done+=1
        off+=size
    assert done==1, done
    return bytes(b)
def build(src: Path, out: Path, work: Path):
    work.mkdir(parents=True,exist_ok=True)
    tmp=work/(src.stem+'.unsigned.apk')
    with zipfile.ZipFile(src) as zi, zipfile.ZipFile(tmp,'w') as zo:
        for i in zi.infolist():
            if i.filename.startswith('META-INF/'): continue
            data=zi.read(i.filename)
            if i.filename=='AndroidManifest.xml': data=patch_manifest(data)
            ni=zipfile.ZipInfo(i.filename,date_time=(2009,1,1,0,0,0)); ni.compress_type=i.compress_type; ni.external_attr=i.external_attr
            zo.writestr(ni,data)
    al=work/(src.stem+'.aligned.apk')
    subprocess.run([str(BT/'zipalign.exe'),'-f','-p','4',str(tmp),str(al)],check=True)
    subprocess.run([str(BT/'apksigner.bat'),'sign','--ks',str(KS),'--ks-pass','pass:android','--key-pass','pass:android','--min-sdk-version','30','--out',str(out),str(al)],check=True,shell=True)
    subprocess.run([str(BT/'apksigner.bat'),'verify','--min-sdk-version','30',str(out)],check=True,shell=True)
if __name__=='__main__':
    payload=Path(sys.argv[1]); outdir=Path(sys.argv[2]); manifest=json.loads((payload.parent/'manifest.json').read_text(encoding='utf-8'))
    outdir.mkdir(parents=True,exist_ok=True); res=[]
    for o in manifest['overlays']:
        src=payload/o['file']; out=outdir/o['file']
        build(src,out,outdir/'_work')
        # resources.arsc must be unchanged
        a=zipfile.ZipFile(src).read('resources.arsc'); c=zipfile.ZipFile(out).read('resources.arsc')
        assert a==c, o['file']
        res.append({'file':o['file'],'package':o['package'],'target':o['target'],'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'size':out.stat().st_size})
    (outdir/'static-rro.json').write_text(json.dumps(res,indent=1),encoding='utf-8')
    shutil.rmtree(outdir/'_work')
    print(len(res),'static RRO built; total bytes',sum(r['size'] for r in res))
