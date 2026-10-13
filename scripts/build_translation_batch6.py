"""Sixth batch: thermal/power warnings, fan-mode conflicts and automatic mounting-mode notices."""
from pathlib import Path
import build_translation_batch2 as base
HIGH='Слишком высокая температура. Включён режим по умолчанию'
ABNORMAL='Аномальная температура. Включён режим по умолчанию'
TRANSLATIONS={
 'pref_colorful_mode_close_high_temp_tip':HIGH,
 'pref_colorful_mode_close_sensor_err_tip':ABNORMAL,
 'pref_colorful_mode_close_timout_tip':HIGH,
 'pref_mode_close_high_temp_tip':HIGH,
 'pref_mode_close_sensor_err_tip':ABNORMAL,
 'pref_mode_close_timout_tip':HIGH,
 'pref_high_temp_swfailed_error_tip':'Используйте устройство при рекомендуемой температуре окружающей среды',
 'pref_mode_close_adapter_tip':'Адаптер питания отключён',
 'fan_mutex_tips0':'Режим высокогорья отключает беззвучный режим',
 'fan_mutex_tips1':'Режим высокогорья отключает режим производительности',
 'fan_mutex_tips2':'Беззвучный режим отключает режим высокогорья',
 'fan_mutex_tips3':'Беззвучный режим отключает режим производительности',
 'fan_mutex_tips4':'Режим производительности отключает режим высокогорья',
 'fan_mutex_tips5':'Режим производительности отключает беззвучный режим',
 'inner_charger_lower_battery':'Низкий заряд аккумулятора',
 'warn_power_adapter_low':'Недостаточная мощность адаптера',
 'warn_power_adapter_low_desc':'Рекомендуется использовать оригинальный адаптер питания',
 'warn_power_battery_low':'Низкий заряд аккумулятора',
 'warn_power_battery_low_desc':'Подключите оригинальный адаптер питания для зарядки',
 # Titan says "economy"/"vertical" here, which contradicts the source (吊装 = ceiling mount, 正装 = normal mount).
 'vertical_turn_nagative':'Режим потолочной установки включён автоматически по положению устройства',
 'vertical_turn_positive':'Режим обычной установки включён автоматически по положению устройства',
}
def main():
 source=Path(base.__file__).read_text(encoding='utf-8')
 source=source.replace("assert m['version']=='1.19.17'", "assert m['version']=='1.19.21'")
 source=source.replace('translation-table-1.19.17','translation-table-1.19.21').replace('translation-batch2-','translation-batch6-')
 source=source.replace("builder.VERSION='1.19.18';builder.VERSION_CODE=38", "builder.VERSION='1.19.22';builder.VERSION_CODE=42")
 source=source.replace("m['version']='1.19.18'", "m['version']='1.19.22'").replace("'release':'1.19.18'", "'release':'1.19.22'")
 source=source.replace('Built 1.19.18: 17 notification strings','Built 1.19.22: 21 warning strings')
 source=source[:source.index('TRANSLATIONS={')]+'TRANSLATIONS='+repr(TRANSLATIONS)+'\n'+source[source.index('def main():'):]
 exec(compile(source,__file__,'exec'),{'__file__':__file__,'__name__':'__main__'})
if __name__=='__main__':main()
