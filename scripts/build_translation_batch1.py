"""First reviewed Titan resource batch, on verified 1.19.16, without device writes."""
from pathlib import Path
import hashlib, json, re, shutil
import build_photo_fixes as builder

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'investigation/translation-batch1-2026-10-12'
TRANSLATIONS={
    'audio_arc':'Устройство HDMI ARC',
    'audio_headset':'Наушники',
    'audio_spdif':'Оптический выход',
    'audio_subwoofer':'Сабвуфер',
    'audio_usb_device':'USB-устройство',
    'delay_lighting_off':'Таймер подсветки',
    'delay_lighting_off_cancel_text':'Таймер подсветки отменён',
    'delay_lighting_off_time':'Подсветка выключится через %s мин.',
    'text_custom_delay_lighting_off':'Задать время',
    'text_invaid_delay_lighting_time':'Время вне допустимого диапазона',
    'focus_guide_ak':'Коррекция одним нажатием',
    'focus_guide_auto_focus':'Автофокусировка',
    'focus_guide_btn':'Понятно',
    'focus_guide_focus_man':'Ручная фокусировка',
    'focus_guide_misckey':'Другие функции фокусировки и коррекции',
    'focus_guide_title':'Коррекция изображения',
}
def fmt(text):
    return re.findall(r'%(?:\d+\$)?[-#+ 0,(<]*\d*(?:\.\d+)?[a-zA-Z]',text or '')
def main():
    m=json.loads((ROOT/'russifier/manifest.json').read_text(encoding='utf-8'))
    assert m['version']=='1.19.16'
    data=json.loads((ROOT/'investigation/titan-2026-10-12/translation-table-1.19.16/table-data.json').read_text(encoding='utf-8'))
    assert data['version']=='1.19.16'
    rows={r['resource'].removeprefix('string/'):r for r in data['strings'] if r['package']=='com.xgimi.systemui'}
    for key,value in TRANSLATIONS.items():
        r=rows[key]
        assert r['stock'] and r['titan'] and not r['ours'] and r['status']=='Кандидат',key
        assert re.search('[А-Яа-яЁё]',r['titan']) and not re.search('[А-Яа-яЁё]',r['stock']),key
        assert fmt(r['stock'])==fmt(value),key
        assert fmt(r['play6_default'])==fmt(value),key
    OUT.mkdir(exist_ok=False)
    (OUT/'before').mkdir()
    for name,digest in m['files'].items(): assert builder.sha(ROOT/'russifier/payload'/name)==digest,name
    shutil.copyfile(ROOT/'russifier/manifest.json',OUT/'before/manifest.json')
    shutil.copyfile(ROOT/'russifier/payload/systemui.apk',OUT/'before/systemui.apk')
    builder.OUT=OUT;builder.WORK=Path('C:/android/translation-batch1-20261012')
    builder.VERSION='1.19.17';builder.VERSION_CODE=37
    builder.WORK.mkdir(exist_ok=False)
    new=builder.overlay('systemui.apk',TRANSLATIONS)
    shutil.copyfile(new,ROOT/'russifier/payload/systemui.apk')
    m['files']['systemui.apk']=builder.sha(new)
    m['version']='1.19.17'
    m['resourceChecks']['com.xgimi.systemui'].update(TRANSLATIONS)
    (ROOT/'russifier/manifest.json').write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    reviewed=[]
    for key,value in TRANSLATIONS.items():
        reviewed.append({**rows[key],'proposed':value,'decision':'Взять Titan' if value==rows[key]['titan'] else 'Редактировать',
                         'release':'1.19.17','deviceStatus':'Не проверено на устройстве'})
    for key in ['focus_guide_desc','focus_guide_desc2']:
        reviewed.append({**rows[key],'proposed':None,'decision':'Проверить экран','release':None,
                         'reason':'Служебные маркеры focus/focus2 и два %s. В текущем SystemUI метод FocusGuideDialog.setDes возвращает без отображения. Перенос отложен.',
                         'deviceStatus':'Не проверено на устройстве'})
    (OUT/'reviewed.json').write_text(json.dumps(reviewed,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('Built 1.19.17: 16 additions in SystemUI RRO, 2 focus descriptions deferred; native APKs unchanged.')
if __name__=='__main__': main()
