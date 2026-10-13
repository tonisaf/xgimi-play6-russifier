"""Fifth batch: projection environment detection and wall memory."""
from pathlib import Path
import build_translation_batch2 as base
TRANSLATIONS={
 'apply_to_screen_memory':'Сохранённые настройки стены применены',
 'apply_to_smart_space':'Динамическая стена включена',
 'env_adapt_desc':'Изображение будет автоматически подстраиваться под изменения условий проекции',
 'env_anim_dialog_desc':'Автоматическое обнаружение препятствий и проекционного экрана',
 'env_anim_dialog_desc_ak4':'Автоматическое обнаружение препятствий, проекционного экрана и цвета стены',
 'env_anim_dialog_item_block':'Препятствия',
 'env_anim_dialog_item_curtain':'Проекционный экран',
 'env_anim_dialog_item_have_block':'Есть',
 'env_anim_dialog_item_have_curtain':'Есть',
 'env_anim_dialog_item_no_block':'Нет',
 'env_anim_dialog_item_no_curtain':'Нет',
 'env_anim_dialog_item_wall_not_white':'Требуется адаптация',
 'env_anim_dialog_item_wall_white':'Адаптация не требуется',
 'env_anim_dialog_title':'Проверка условий проекции…',
 'notice_smart_space_desc':'Настройки стены обновлены',
 'screen_memory_desc':'Параметры изображения обновлены',
 'screen_memory_title':'Память настроек стены',
}
def main():
 source=Path(base.__file__).read_text(encoding='utf-8')
 source=source.replace("assert m['version']=='1.19.17'", "assert m['version']=='1.19.20'")
 source=source.replace('translation-table-1.19.17','translation-table-1.19.20').replace('translation-batch2-','translation-batch5-')
 source=source.replace("builder.VERSION='1.19.18';builder.VERSION_CODE=38", "builder.VERSION='1.19.21';builder.VERSION_CODE=41")
 source=source.replace("m['version']='1.19.18'", "m['version']='1.19.21'").replace("'release':'1.19.18'", "'release':'1.19.21'")
 source=source.replace('Built 1.19.18: 17 notification strings','Built 1.19.21: 17 environment/wall-memory strings')
 source=source[:source.index('TRANSLATIONS={')]+'TRANSLATIONS='+repr(TRANSLATIONS)+'\n'+source[source.index('def main():'):]
 exec(compile(source,__file__,'exec'),{'__file__':__file__,'__name__':'__main__'})
if __name__=='__main__':main()
