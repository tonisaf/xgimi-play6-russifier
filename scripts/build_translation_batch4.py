"""Fourth batch: wall color matching and screen alignment resources."""
from pathlib import Path
import build_translation_batch2 as base
TRANSLATIONS={
 'ambient_light_stability_failed':'Не удалось выполнить адаптацию. Дождитесь стабильного освещения и повторите попытку',
 'camera_initialization_failed':'Не удалось запустить камеру. Повторите попытку',
 'dialog_adapt_curtain_btn':'Начать коррекцию изображения',
 'dialog_adapt_curtain_desc':'Переместите проектор так, чтобы рамка экрана находилась в серой области. Это поможет точно совместить изображение с экраном',
 'dialog_adapt_curtain_title':'Выравнивание по экрану',
 'env_anim_dialog_item_wall_color':'Цвет стены',
 'wall_color_3d_mode_not':'Не поддерживается в режиме 3D',
 'wall_color_3d_mode_not_enable_ak':'Перед автоматической коррекцией изображения отключите адаптацию к цвету стены',
 'wall_color_confirm_save_color_desc':'Цвета настроены для оптимального изображения на этой стене',
 'wall_color_confirm_save_color_title':'Сохранить результат адаптации?',
 'wall_color_custom_not':'Адаптация к цвету стены недоступна в пользовательском цветовом режиме',
 'wall_color_distance_failed':'Не удалось выполнить адаптацию. Измените расстояние или угол проекции',
 'wall_color_filt_tip':'Не удалось выполнить адаптацию. Цвет стены вне диапазона калибровки',
 'wall_color_initialization_failed':'Не удалось запустить адаптацию к цвету стены. Обратитесь в службу поддержки',
 'wall_color_over_new_btn':'Использовать настроенные цвета',
 'wall_color_over_reset_btn':'Использовать исходные цвета',
 'wall_color_over_tip':'Цвета настроены для оптимального изображения',
}
def main():
 source=Path(base.__file__).read_text(encoding='utf-8')
 source=source.replace("assert m['version']=='1.19.17'", "assert m['version']=='1.19.19'")
 source=source.replace('translation-table-1.19.17','translation-table-1.19.19').replace('translation-batch2-','translation-batch4-')
 source=source.replace("builder.VERSION='1.19.18';builder.VERSION_CODE=38", "builder.VERSION='1.19.20';builder.VERSION_CODE=40")
 source=source.replace("m['version']='1.19.18'", "m['version']='1.19.20'").replace("'release':'1.19.18'", "'release':'1.19.20'")
 source=source.replace('Built 1.19.18: 17 notification strings','Built 1.19.20: 17 wall-color/alignment strings')
 source=source[:source.index('TRANSLATIONS={')]+'TRANSLATIONS='+repr(TRANSLATIONS)+'\n'+source[source.index('def main():'):]
 exec(compile(source,__file__,'exec'),{'__file__':__file__,'__name__':'__main__'})
if __name__=='__main__':main()
