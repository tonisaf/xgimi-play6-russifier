import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent
SOURCE = ROOT.parent / '2026-10-07'
sys.path.insert(0, str(SOURCE / 'python-libs'))
from fontTools.ttLib import TTFont
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.feaLib.builder import addOpenTypeFeaturesFromString

font = TTFont(SOURCE / 'HMSans-Regular-original.ttf')
cmap = font.getBestCmap()
translations = {
    '画面校正': 'Коррекция', '亮度与显示': 'Изображение', '网络': 'Сеть',
    '信号源': 'Источник', '蓝牙与配件': 'Bluetooth', '声音': 'Звук', '通用': 'Общие',
}
order = list(font.getGlyphOrder())
rules = []
for identity, (original, translated) in enumerate(translations.items()):
    glyph = f'beamMainRu{identity}'
    pen = TTGlyphPen(font.getGlyphSet())
    width = 0
    for char in translated:
        source_glyph = cmap[ord(char)]
        pen.addComponent(source_glyph, (1, 0, 0, 1, width, 0))
        width += font['hmtx'].metrics[source_glyph][0]
    font['glyf'].glyphs[glyph] = pen.glyph()
    font['hmtx'].metrics[glyph] = (width, 0)
    order.append(glyph)
    # Verify all unicode cmap variants agree on input glyphs.
    for char in original:
        variants = {table.cmap[ord(char)] for table in font['cmap'].tables if table.isUnicode() and ord(char) in table.cmap}
        assert variants == {cmap[ord(char)]}, (char, variants)
    rules.append('sub ' + ' '.join(cmap[ord(char)] for char in original) + f' by {glyph};')
font.setGlyphOrder(order)
feature = '\n'.join(f'languagesystem {script} {language};' for script, language in (
    ('DFLT', 'dflt'), ('hani', 'dflt'), ('hani', 'ZHS'), ('hani', 'ZHT'),
    ('hani', 'RUS'), ('latn', 'dflt'), ('cyrl', 'dflt'),
)) + '\nfeature rlig {\n' + '\n'.join(rules) + '\n} rlig;'
addOpenTypeFeaturesFromString(font, feature)
for record in font['GSUB'].table.ScriptList.ScriptRecord:
    language_systems = [record.Script.DefaultLangSys] + [entry.LangSys for entry in record.Script.LangSysRecord]
    for language_system in language_systems:
        if language_system is not None:
            language_system.ReqFeatureIndex = 0
for name_id, text in ((1, 'Beam Main RU Probe'), (4, 'Beam Main RU Probe Regular'), (6, 'BeamMainRUProbe-Regular')):
    font['name'].setName(text, name_id, 3, 1, 0x409)
out = ROOT / 'required-font'
out.mkdir(exist_ok=True)
font.save(out / 'HMSans-Regular.ttf')
(ROOT / 'required-feature.fea').write_text(feature, encoding='utf-8')
(ROOT / 'translations.json').write_text(json.dumps(translations, ensure_ascii=False, indent=2), encoding='utf-8')
print('Required feature font built; unicode cmap variants verified')
