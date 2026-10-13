"""Third reviewed batch: correction controls and system warning dialogs."""
import build_translation_batch2 as base
from pathlib import Path
TRANSLATIONS={
 'help_adj':'Настроить',
 'help_back':'Назад',
 'help_ok':'Выбрать точку',
 'update_finish_shutdown':'Обновление приложений. Не отключайте питание',
 'warning_window_fan_error_tip':'Ошибка вентилятора. Выключение через %s с.',
 'warning_window_fan_error_tip_text':'Обнаружена неисправность вентилятора. Обратитесь в службу поддержки: 400–002–8960',
 'warning_window_temperature_exception_tip':'Ошибка контроля температуры. Выключение через %s с.',
 'warning_window_temperature_high_tip':'Перегрев. Выключение через %s с.',
 'warning_window_temperature_high_tip_text':'Попробуйте перезапустить устройство. Если ошибка повторяется, обратитесь в службу поддержки: 400–002–8960',
}
def main():
 source=Path(base.__file__).read_text(encoding='utf-8')
 source=source.replace("assert m['version']=='1.19.17'", "assert m['version']=='1.19.18'")
 source=source.replace('translation-table-1.19.17','translation-table-1.19.18').replace('translation-batch2-','translation-batch3-')
 source=source.replace("builder.VERSION='1.19.18';builder.VERSION_CODE=38", "builder.VERSION='1.19.19';builder.VERSION_CODE=39")
 source=source.replace("m['version']='1.19.18'", "m['version']='1.19.19'").replace("'release':'1.19.18'", "'release':'1.19.19'")
 source=source.replace('Built 1.19.18: 17 notification strings','Built 1.19.19: 9 control/warning strings')
 source=source[:source.index('TRANSLATIONS={')]+ 'TRANSLATIONS='+repr(TRANSLATIONS)+'\n'+source[source.index('def main():'):]
 exec(compile(source,__file__,'exec'),{'__file__':__file__,'__name__':'__main__'})
if __name__=='__main__':main()
