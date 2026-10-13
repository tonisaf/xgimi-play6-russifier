"""Eighth batch: toast-style messages of Settings that exist only in the skin.

Toast.makeText(context, resId, ...) reads plain Resources, which the skin does not replace, so the
Russian wording (already reviewed in the skin) must also be carried by the Settings RRO."""
from pathlib import Path
import json, re, shutil
import xml.etree.ElementTree as ET
import build_photo_fixes as builder
import build_translation_batch7 as b7
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'investigation/translation-batch8-2026-10-13'
EXTRA={'brightness_adaption_off_tips','brightness_adaption_on_tips','env_adaption_off_tips','env_adaption_on_tips',
 'network_ap_close_tip','network_ap_failed_tip','network_ap_open_tip','network_save_ap_tip',
 'network_wifi_con_hide_error_tip','network_wifi_con_none_error_tip','wifi_con_hide_error_tip',
 'wifi_add_other_ssid_error_tip','min_wifi_pass_msg_tip','picture_light_max','picture_light_min',
 'picture_zoom_max','picture_zoom_min','focus_max','level_keystone_max','displacement_end_tip','exit_boost_on_tips'}
def selection(table):
 rro=set(table['rro']);skin=table['skin']
 names=[]
 for n,zh in table['zh'].items():
  if n in skin and n not in rro and re.search(r'[\u4e00-\u9fff]',zh) and ('toast' in n.lower() or n in EXTRA): names.append(n)
 return sorted(names)
def main():
 m=json.loads((ROOT/'russifier/manifest.json').read_text(encoding='utf-8'));assert m['version']=='1.19.24'
 for name,digest in m['files'].items():assert builder.sha(ROOT/'russifier/payload'/name)==digest,name
 data=json.loads((ROOT/'investigation/titan-2026-10-12/translation-table-1.19.21/table-data.json').read_text(encoding='utf-8'))
 zh={r['resource'].removeprefix('string/'):(r.get('stock') or '') for r in data['strings'] if r['package']=='com.android.newsettings'}
 skin={n.get('name'):n.text for n in ET.parse(ROOT/'skin/res/values/strings.xml').getroot()}
 import subprocess
 dump=subprocess.check_output([str(builder.BT/'aapt2.exe'),'dump','resources',str(ROOT/'russifier/payload/settings.apk')]).decode('utf-8')
 rro=set(re.findall(r'string/(\S+)',dump))
 names=selection({'zh':zh,'skin':skin,'rro':rro})
 changes={n:skin[n] for n in names}
 # builder asserts that every value appears verbatim in the compiled table: keep plain strings only
 plain={n:v for n,v in changes.items() if v and not re.search(r'[\\n"<&]',v)}
 # The skin keeps escaped quotes (\"@\"); the RRO uses typographic quotes for the same text.
 SPECIAL={'displacement_end_tip':'Сдвиг может размыть изображение; нажмите «@» для ручной фокусировки'}
 plain.update({n:v for n,v in SPECIAL.items() if n in changes})
 skipped=sorted(set(changes)-set(plain))
 TRANSLATIONS={**b7.TRANSLATIONS,**plain}
 OUT.mkdir(exist_ok=True);(OUT/'before').mkdir(exist_ok=True)
 shutil.copyfile(ROOT/'russifier/manifest.json',OUT/'before/manifest.json');shutil.copyfile(ROOT/'russifier/payload/settings.apk',OUT/'before/settings.apk')
 base=ROOT/'.local/table-20261012/overlays/settings-complete'
 fixed=ROOT/'.local/table-20261012/overlays/settings-fixed'
 if fixed.exists():shutil.rmtree(fixed)
 shutil.copytree(base,fixed)
 for layout in (fixed/'res/layout').glob('*.xml'):
  layout.write_text(b7.PRIVATE.sub(lambda x:x.group(1)+x.group(2)+'*'+x.group(3),layout.read_text(encoding='utf-8')),encoding='utf-8')
 builder.OUT=OUT;builder.WORK=Path('C:/android/translation-batch8-20261013');builder.VERSION='1.19.25';builder.VERSION_CODE=44
 builder.WORK.mkdir(exist_ok=True)
 built=builder.overlay('settings-fixed.apk',TRANSLATIONS)
 new=OUT/'settings.apk';shutil.copyfile(built,new);shutil.copyfile(new,ROOT/'russifier/payload/settings.apk')
 m['version']='1.19.25';m['files']['settings.apk']=builder.sha(new)
 m['resourceChecks']['com.android.newsettings'].update(TRANSLATIONS)
 (ROOT/'russifier/manifest.json').write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 (OUT/'reviewed.json').write_text(json.dumps([{'name':n,'stock':zh[n],'ru':plain[n]} for n in sorted(plain)],ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print('Built 1.19.25:',len(plain),'toast-style strings (+reset_key_stone); skipped (need escaping):',skipped)
if __name__=='__main__':main()
