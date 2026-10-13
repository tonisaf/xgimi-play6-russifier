"""Seventh batch: button label of the zoom/shift screen, read through a custom view attribute (not covered by the skin)."""
from pathlib import Path
import json, re, shutil
import build_photo_fixes as builder
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'investigation/translation-batch7-2026-10-13'
# ZoomIconTxtView gets this through app:attr_name, i.e. plain Resources; the skin does not apply, so the RRO must carry it.
TARGET=Path('C:/android/panel-current-20261009-original.apk')  # Play 6 Settings APK with its resources exposed; the layouts in this RRO reference them (as in build_reset_buttons.py)
PRIVATE=re.compile('(["(])([@?])(com[.]android[.]newsettings:)')
_run=builder.run
def _link_with_target(*args):
 args=list(args)
 if len(args)>1 and str(args[1])=='link': args[args.index('--manifest'):args.index('--manifest')]=['-I',str(TARGET)]
 return _run(*args)
builder.run=_link_with_target
TRANSLATIONS={'reset_key_stone':'Сбросить изображение'}
def main():
 m=json.loads((ROOT/'russifier/manifest.json').read_text(encoding='utf-8'));assert m['version']=='1.19.23'
 for name,digest in m['files'].items():assert builder.sha(ROOT/'russifier/payload'/name)==digest,name
 base=ROOT/'.local/table-20261012/overlays/settings-complete'
 assert (base/'payload-sha256.txt').read_text(encoding='utf-8').strip()==m['files']['settings.apk']
 OUT.mkdir(exist_ok=True);(OUT/'before').mkdir(exist_ok=True)
 shutil.copyfile(ROOT/'russifier/manifest.json',OUT/'before/manifest.json')
 shutil.copyfile(ROOT/'russifier/payload/settings.apk',OUT/'before/settings.apk')
 # apktool decodes private references as @com.android.newsettings:...; aapt2 needs the @* form to link against the stock APK.
 fixed=ROOT/'.local/table-20261012/overlays/settings-fixed'
 if fixed.exists():shutil.rmtree(fixed)
 shutil.copytree(base,fixed)
 for layout in (fixed/'res/layout').glob('*.xml'):
  text=layout.read_text(encoding='utf-8');text=PRIVATE.sub(lambda m:m.group(1)+m.group(2)+'*'+m.group(3),text);layout.write_text(text,encoding='utf-8')
 builder.OUT=OUT;builder.WORK=Path('C:/android/translation-batch7-20261013');builder.VERSION='1.19.24';builder.VERSION_CODE=43
 builder.WORK.mkdir(exist_ok=True)
 built=builder.overlay('settings-fixed.apk',TRANSLATIONS)
 new=OUT/'settings.apk';shutil.copyfile(built,new)
 shutil.copyfile(new,ROOT/'russifier/payload/settings.apk')
 m['version']='1.19.24';m['files']['settings.apk']=builder.sha(new)
 m['resourceChecks']['com.android.newsettings'].update(TRANSLATIONS)
 (ROOT/'russifier/manifest.json').write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print('Built 1.19.24: 1 settings string; native APKs unchanged.')
if __name__=='__main__':main()
