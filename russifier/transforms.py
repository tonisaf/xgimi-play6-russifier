"""Only presentation fields are changed; no foreign catalog/database is imported."""
from pathlib import Path
import io
import sqlite3
import shutil
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent/'vendor'))
from javaobj.v2.core import JavaStreamParser
from javaobj.v2.transformers import DefaultObjectTransformer

QUICK = {
    3: ('artificial_correction', 'Ручная трапеция'), 4: ('scale', 'Масштаб'),
    5: ('auto_focus', 'Автофокус'), 8: ('signal_source', 'Источник'),
    9: ('network', 'Сеть'), 10: ('bluetooth', 'Bluetooth'),
    11: ('kid_model', 'Детский'), 12: ('xgimi_wall', 'Заставки'),
    14: ('u_disk', 'USB'), 16: ('xgimi_music', 'Музыка'),
    18: ('screen_rotation', 'Поворот'), 23: ('one_click_correction', 'Автокорр.'),
    34: ('energy_mode', 'Экорежим'),
}
GROUPS = {'9': 'Потолок', '3': 'Время и погода', '1': 'Атмосфера',
          '2': 'Галерея', '4': 'Авторы', '8': 'Коллаборации'}
SER_GROUPS = {**GROUPS, '-1': 'Авторы', 'collect_group': 'Избранное',
              'setting_group': 'Настройки'}
TRIGGER_PREFIXES = ('beam_quick_ru_', 'beam_hide_child_', 'beam_atmosphere_ru_')

def sql_quote(value):
    return "'"+str(value).replace("'", "''")+"'"

def check_db(db):
    if db.execute('pragma integrity_check').fetchone()[0] != 'ok':
        raise RuntimeError('Database integrity check failed')
    if db.execute('pragma foreign_key_check').fetchall():
        raise RuntimeError('Database foreign key check failed')

def put_trigger(db, name, sql):
    existing = db.execute('select sql from sqlite_master where type=? and name=?',
                          ('trigger', name)).fetchone()
    if existing and ' '.join(existing[0].split()) == ' '.join(sql.rstrip(';').split()):
        return
    db.execute('DROP TRIGGER IF EXISTS '+name)
    db.execute(sql)

def translate_db(src, dst, kind, rule_sql='', hide_child=True):
    shutil.copyfile(src, dst)
    db = sqlite3.connect(dst)
    try:
        check_db(db)
        if kind == 'quick':
            columns = {r[1] for r in db.execute('pragma table_info(MisckeyConfigFuncDB)')}
            if not {'id','icon','name','funcType'} <= columns:
                raise RuntimeError('Unexpected quick-panel schema')
            for ident, (icon, name) in QUICK.items():
                row = db.execute('select icon,name from MisckeyConfigFuncDB where id=?',(ident,)).fetchone()
                if row is None:
                    continue
                if row[0] != icon:
                    raise RuntimeError('Unexpected icon for quick-panel ID '+str(ident))
                if row[1] != name:
                    db.execute('update MisckeyConfigFuncDB set name=? where id=?',(name,ident))
            # Each statement is a whole CREATE TRIGGER, including the body semicolon.
            for sql in rule_sql.split('\n\n'):
                sql = sql.strip()
                if sql:
                    put_trigger(db, sql.split()[2], sql)
            if hide_child:
                for suffix,event in [('insert','INSERT'),('update','UPDATE OF funcType')]:
                    name = 'beam_hide_child_'+suffix
                    sql = (f"CREATE TRIGGER {name} AFTER {event} ON MisckeyConfigFuncDB "
                           "WHEN NEW.id=11 AND NEW.icon='kid_model' AND NEW.funcType!=-1 "
                           "BEGIN UPDATE MisckeyConfigFuncDB SET funcType=-1 WHERE id=NEW.id; END")
                    put_trigger(db,name,sql)
                db.execute("update MisckeyConfigFuncDB set funcType=-1 where id=11 and icon='kid_model' and funcType!=-1")
        elif kind == 'atmosphere':
            columns = {r[1] for r in db.execute('pragma table_info(groups)')}
            if not {'_id','group_id','name'} <= columns:
                raise RuntimeError('Unexpected Atmosphere schema')
            for ident,name in GROUPS.items():
                db.execute('update groups set name=? where group_id=? and name!=?',(name,ident,name))
            cases = ' '.join('WHEN '+sql_quote(i)+' THEN '+sql_quote(n) for i,n in GROUPS.items())
            ids = ','.join(map(sql_quote,GROUPS))
            value = 'CASE NEW.group_id '+cases+' ELSE NEW.name END'
            for suffix,event in [('insert','INSERT'),('update','UPDATE OF name,group_id')]:
                name = 'beam_atmosphere_ru_'+suffix
                put_trigger(db,name,f'CREATE TRIGGER {name} AFTER {event} ON groups '
                    f'WHEN NEW.group_id IN ({ids}) AND NEW.name != ({value}) BEGIN '
                    f'UPDATE groups SET name=({value}) WHERE _id=NEW._id; END')
        else:
            raise ValueError(kind)
        db.commit()
        check_db(db)
        verify_other_data(src,db,kind)
    finally:
        db.close()

def verify_other_data(src, after, kind):
    before = sqlite3.connect(src)
    for table, in before.execute("select name from sqlite_master where type='table'"):
        if table == 'groups' and kind == 'atmosphere':
            exclude = {'name'}
        elif table == 'MisckeyConfigFuncDB' and kind == 'quick':
            exclude = {'name','funcType'}
        else:
            exclude = set()
        cols = [r[1] for r in before.execute('pragma table_info('+sql_quote(table)+')') if r[1] not in exclude]
        query = 'select '+','.join('"'+c.replace('"','""')+'"' for c in cols)+' from "'+table.replace('"','""')+'"'
        if before.execute(query).fetchall() != after.execute(query).fetchall():
            raise RuntimeError('Unrelated database fields changed: '+table)
    if kind == 'quick':
        for ident, name, func in before.execute('select id,name,funcType from MisckeyConfigFuncDB'):
            current = after.execute('select name,funcType from MisckeyConfigFuncDB where id=?',(ident,)).fetchone()
            if ident not in QUICK and current != (name,func):
                raise RuntimeError('Unknown quick-panel row changed')
            if ident != 11 and current[1] != func:
                raise RuntimeError('Unexpected function type change')
    before.close()

class Parser(JavaStreamParser):
    def __init__(self, raw):
        self.fd = io.BytesIO(raw)
        self.strings = {}
        super().__init__(self.fd,[DefaultObjectTransformer()])
    def _read_new_string(self, code):
        start = self.fd.tell()
        obj = super()._read_new_string(code)
        if code in (0x74,0x7c):
            self.strings[obj.handle] = (start,self.fd.tell(),str(obj),code)
        return obj

def fields(obj):
    return {f.name:v for cls, data in obj.field_data.items() for f,v in data.items()}

def parse_catalog(raw):
    parser = Parser(raw)
    roots = parser.run()
    if len(roots) != 1 or parser.fd.tell() != len(raw):
        raise RuntimeError('Unexpected serialized catalog')
    return parser,roots[0]

def catalog_names(src):
    parser,root = parse_catalog(Path(src).read_bytes())
    return {str(fields(g)['id']):str(fields(g)['name']) for g in fields(root)['groups']}

def translate_catalog(src, dst, names=None):
    names = SER_GROUPS if names is None else names
    raw = Path(src).read_bytes()
    parser,root = parse_catalog(raw)
    changes = {}
    for group in fields(root)['groups']:
        values = fields(group)
        ident = str(values['id'])
        if ident not in names or str(values['name']) == names[ident]:
            continue
        handle = values['name'].handle
        start,end,old,code = parser.strings[handle]
        if code != 0x74:
            raise RuntimeError('Unexpected long group name')
        encoded = names[ident].encode('utf-8')
        changes[handle] = (start,end,len(encoded).to_bytes(2,'big')+encoded,names[ident])
    result = raw
    for start,end,value,name in sorted(changes.values(),reverse=True):
        result = result[:start]+value+result[end:]
    check,after = parse_catalog(result)
    if parser.strings.keys() != check.strings.keys():
        raise RuntimeError('Serialization handles changed')
    for handle,record in parser.strings.items():
        expected = changes[handle][3] if handle in changes else record[2]
        if check.strings[handle][2] != expected:
            raise RuntimeError('Unrelated serialized string changed')
    Path(dst).write_bytes(result)
    return len(changes)

def restore_db(current, baseline, installed, dst, kind):
    """Undo only our names, function type, and triggers, preserving later app data."""
    shutil.copyfile(current,dst)
    now = sqlite3.connect(dst)
    before = sqlite3.connect(baseline)
    ours = sqlite3.connect(installed)
    table,key,cols = ('MisckeyConfigFuncDB','id',['name','funcType']) if kind=='quick' else ('groups','group_id',['name'])
    old_rules = dict(before.execute("select name,sql from sqlite_master where type='trigger'"))
    for name,sql in ours.execute("select name,sql from sqlite_master where type='trigger'"):
        if not name.startswith(TRIGGER_PREFIXES):
            continue
        current_sql = now.execute("select sql from sqlite_master where type='trigger' and name=?",(name,)).fetchone()
        if current_sql and current_sql[0] == sql:
            now.execute('drop trigger '+name)
            if name in old_rules:
                now.execute(old_rules[name])
    # Remove matched triggers first, so the original names are not translated again.
    rules_to_restore = []
    for name,sql in old_rules.items():
        if name.startswith(TRIGGER_PREFIXES):
            current_sql = now.execute("select sql from sqlite_master where type='trigger' and name=?",(name,)).fetchone()
            if current_sql and current_sql[0] == sql:
                now.execute('drop trigger '+name)
                rules_to_restore.append(sql)
    for row in before.execute('select '+key+','+','.join(cols)+' from '+table):
        ident,*old = row
        if kind=='quick' and ident not in QUICK:
            continue
        if kind=='atmosphere' and str(ident) not in GROUPS:
            continue
        their = ours.execute('select '+','.join(cols)+' from '+table+' where '+key+'=?',(ident,)).fetchone()
        present = now.execute('select '+','.join(cols)+' from '+table+' where '+key+'=?',(ident,)).fetchone()
        if not their or not present:
            continue
        for col,expected,original,actual in zip(cols,their,old,present):
            if actual==expected and actual!=original:
                now.execute('update '+table+' set '+col+'=? where '+key+'=?',(original,ident))
    for sql in rules_to_restore:
        now.execute(sql)
    now.commit();check_db(now)
    now.close();before.close();ours.close()
