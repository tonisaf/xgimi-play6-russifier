from pathlib import Path
import sys, io, json, sqlite3, shutil, hashlib
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, r'C:\Users\USER\AppData\Local\Temp\beam-java-ser-libs')
from javaobj.v2.core import JavaStreamParser
from javaobj.v2.transformers import DefaultObjectTransformer

OUT = Path(__file__).resolve().parent
NAMES = {
    'collect_group': ('Favourite', 'Избранное'),
    '9': ('天花板', 'Потолок'),
    '3': ('时气', 'Время и погода'),
    '1': ('氛围', 'Атмосфера'),
    '2': ('艺术馆', 'Галерея'),
    '-1': ('创作家', 'Авторы'),
    '8': ('联名', 'Коллаборации'),
    'setting_group': ('Settings', 'Настройки'),
}

class Parser(JavaStreamParser):
    def __init__(self, data):
        self.fd = io.BytesIO(data)
        self.strings = {}
        super().__init__(self.fd, [DefaultObjectTransformer()])

    def _read_new_string(self, code):
        start = self.fd.tell()
        result = super()._read_new_string(code)
        if code in (0x74, 0x7c):
            self.strings[result.handle] = (start, self.fd.tell(), str(result), code)
        return result

def fields(obj):
    return {f.name: v for cls, fs in obj.field_data.items() for f, v in fs.items()}

raw = (OUT/'bottom-before.ser').read_bytes()
parser = Parser(raw)
root = parser.run()[0]
assert parser.fd.tell() == len(raw)
changes = []
for group in fields(root)['groups']:
    fs = fields(group)
    ident = str(fs['id'])
    old, new = NAMES[ident]
    assert str(fs['name']) == old, (ident, str(fs['name']))
    start, end, value, code = parser.strings[fs['name'].handle]
    assert value == old and code == 0x74
    encoded = new.encode('utf-8')
    changes.append((start, end, len(encoded).to_bytes(2, 'big')+encoded, fs['name'].handle, ident))
assert len(changes) == 8
result = raw
for start, end, value, handle, ident in sorted(changes, reverse=True):
    result = result[:start]+value+result[end:]
verify = Parser(result)
after = verify.run()[0]
assert verify.fd.tell() == len(result)
changed_handles = {c[3]: NAMES[c[4]][1] for c in changes}
assert parser.strings.keys() == verify.strings.keys()
for handle, value in parser.strings.items():
    assert verify.strings[handle][2] == changed_handles.get(handle, value[2])
before_fields, after_fields = fields(root), fields(after)
assert fields(before_fields['currentShow'])['id'] == fields(after_fields['currentShow'])['id']
assert fields(before_fields['currentGroup'])['id'] == fields(after_fields['currentGroup'])['id']
(OUT/'bottom-ru.ser').write_bytes(result)

shutil.copyfile(OUT/'bottom-before.db', OUT/'bottom-ru.db')
db = sqlite3.connect(OUT/'bottom-ru.db')
backup = sqlite3.connect(OUT/'bottom-before.db')
groups = dict(db.execute('select group_id,name from groups'))
assert len(groups) == 6
db_names = {gid: NAMES['-1' if gid == '4' else gid] for gid in groups}
for gid, (old, new) in db_names.items():
    assert groups[gid] == old
    db.execute('update groups set name=? where group_id=?', (new, gid))
cases = ' '.join("WHEN '%s' THEN '%s'" % (gid, name[1]) for gid,name in db_names.items())
ids = ','.join("'%s'" % gid for gid in db_names)
value = 'CASE NEW.group_id '+cases+' ELSE NEW.name END'
for suffix, event in [('insert', 'INSERT'), ('update', 'UPDATE OF name,group_id')]:
    db.execute('CREATE TRIGGER beam_atmosphere_ru_'+suffix+' AFTER '+event+' ON groups '
               'WHEN NEW.group_id IN ('+ids+') AND NEW.name != ('+value+') BEGIN '
               'UPDATE groups SET name=('+value+') WHERE _id=NEW._id; END')
db.commit()
assert db.execute('pragma integrity_check').fetchone() == ('ok',)
assert not db.execute('pragma foreign_key_check').fetchall()
for table, in backup.execute("select name from sqlite_master where type='table'"):
    if table == 'groups':
        columns = [row[1] for row in db.execute('pragma table_info(groups)') if row[1] != 'name']
        query = 'select '+','.join('"'+c+'"' for c in columns)+' from groups order by _id'
    else:
        query = 'select * from "'+table+'"'
    assert db.execute(query).fetchall() == backup.execute(query).fetchall(), table
# Trigger verification inside a rolled-back transaction.
db.execute('update groups set name=? where group_id=?', ('天花板', '9'))
assert db.execute("select name from groups where group_id='9'").fetchone()[0] == 'Потолок'
db.rollback()
db.close(); backup.close()
report = {'groups': NAMES, 'changedStringHandles': len(changes), 'unrelatedStringsPreserved': True,
          'currentSelectionPreserved': True, 'unrelatedDatabaseValuesPreserved': True,
          'integrityCheck': 'ok', 'triggers': 2,
          'sha256': {n: hashlib.sha256((OUT/n).read_bytes()).hexdigest() for n in ['bottom-ru.db','bottom-ru.ser']}}
(OUT/'bottom-local-verification.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(report, ensure_ascii=False, indent=2))
