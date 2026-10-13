"""Check third batch resources and preserved workbook against 1.19.18."""
from pathlib import Path
source=(Path(__file__).parent/'verify_translation_batch1.py').read_text(encoding='utf-8')
source=source.replace('build_translation_batch1','build_translation_batch5').replace('translation-batch1-','translation-batch5-')
source=source.replace('1.19.17','1.19.21').replace('Translation-2026-10-12.xlsx','Translation-1.19.20.xlsx')
source=source.replace("'требуется повторная проверка' in v[f'P{row}']","'Проверено пользователем' in v[f'P{row}']")
source=source.replace('added==16','added==17').replace('==372','==312').replace("'compiledNewStrings':16","'compiledNewStrings':17")
source=source.replace("actual=v.get(f'E{row}')", "actual=v.get(f'E{row}')\n    if key[0]=='com.xgimi.systemui' and key[1] in ['string/mem_clean','string/mem_remain']:\n        assert r['ours']=='\\\"'+actual+'\\\"'\n        r={**r,'ours':actual}")
exec(compile(source,__file__,'exec'))
for row in range(6,12007):
    is_new=edited[1][1].get(f'G{row}')=='Добавлено 1.19.21'
    for col in ['E','F','G','H','O','P','Q','R','S']:
        if is_new and col in ['E','F','G','H','O','P','S']:continue
        assert baseline[1][1].get(f'{col}{row}')==edited[1][1].get(f'{col}{row}'),('prior decision/check changed',col,row)
print('All prior decisions and device check fields preserved.')
