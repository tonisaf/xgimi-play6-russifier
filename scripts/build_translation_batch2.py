"""Reviewed SystemUI notifications; preserve runtime code and existing translations."""
from pathlib import Path
import json, shutil
import build_photo_fixes as builder
from build_translation_batch1 import fmt
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'investigation/translation-batch2-2026-10-12'
TRANSLATIONS={
 'clean_all_task':'Память очищена',
 'mem_clean':'Освобождено: ',
 'mem_remain':'Доступно памяти: ',
 'recents_empty_message':'Нет запущенных приложений',
 'recents_stack_action_button_label':'Закрыть все',
 'recents_stack_notice':'Нажмите $, чтобы закрыть приложение',
 'screenshot_failed_to_capture_text':'Снимки экрана запрещены приложением или правилами организации',
 'screenshot_failed_to_save_text':'Недостаточно места для сохранения снимка экрана',
 'screenshot_success':'Снимок сохранён: внутренняя память/Pictures/Screenshots',
 'progress_wait_fail':'Ошибка сети',
 'progress_wait_loading':'Загрузка…',
 'peripheral_bluetooth':'Соединение с телефоном по Bluetooth разорвано',
 'peripheral_connect_success':'Подключено',
 'peripheral_connecting':'Подключение…',
 'peripheral_sound':'Колонка отключена',
 'peripheral_tip_microphone':'Микрофон отключён',
 'peripheral_tip_phone':'Соединение с приложением на телефоне разорвано',
}
def main():
 m=json.loads((ROOT/'russifier/manifest.json').read_text(encoding='utf-8'));assert m['version']=='1.19.17'
 data=json.loads((ROOT/'investigation/titan-2026-10-12/translation-table-1.19.17/table-data.json').read_text(encoding='utf-8'))
 rows={r['resource'].removeprefix('string/'):r for r in data['strings'] if r['package']=='com.xgimi.systemui'}
 for key,value in TRANSLATIONS.items():
  r=rows[key];assert r['status']=='Кандидат' and not r['ours'],key
  assert fmt(r['stock'])==fmt(value)==fmt(r['play6_default']),key
  assert r['stock'].count('$')==value.count('$'),key
 for name,digest in m['files'].items():assert builder.sha(ROOT/'russifier/payload'/name)==digest,name
 OUT.mkdir(exist_ok=True);(OUT/'before').mkdir(exist_ok=True)
 shutil.copyfile(ROOT/'russifier/manifest.json',OUT/'before/manifest.json')
 shutil.copyfile(ROOT/'russifier/payload/systemui.apk',OUT/'before/systemui.apk')
 builder.OUT=OUT;builder.WORK=Path('C:/android/translation-batch2-20261012');builder.VERSION='1.19.18';builder.VERSION_CODE=38
 builder.WORK.mkdir(exist_ok=True)
 new=builder.overlay('systemui.apk',TRANSLATIONS)
 shutil.copyfile(new,ROOT/'russifier/payload/systemui.apk')
 m['version']='1.19.18';m['files']['systemui.apk']=builder.sha(new);m['resourceChecks']['com.xgimi.systemui'].update(TRANSLATIONS)
 (ROOT/'russifier/manifest.json').write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 reviewed=[{**rows[k],'proposed':v,'decision':'Взять Titan' if v==rows[k]['titan'] else 'Редактировать','release':'1.19.18','deviceStatus':'Не проверено на устройстве'} for k,v in TRANSLATIONS.items()]
 (OUT/'reviewed.json').write_text(json.dumps(reviewed,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print('Built 1.19.18: 17 notification strings; native APKs unchanged.')
if __name__=='__main__':main()
