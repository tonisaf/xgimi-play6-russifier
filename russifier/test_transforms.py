from contextlib import closing
import tempfile
import unittest
import sqlite3
from pathlib import Path
from transforms import translate_db, translate_catalog, restore_db, catalog_names, QUICK

BASE = Path(__file__).resolve().parent
FIXTURES = BASE/'tests/fixtures'
RULES = (BASE/'payload/quick-rules.sql').read_text(encoding='utf-8')

class TransformTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.out = Path(self.temp.name)
    def tearDown(self):
        self.temp.cleanup()

    def test_quick_translation_is_idempotent_and_preserves_actions(self):
        first,second = self.out/'first.db',self.out/'second.db'
        translate_db(FIXTURES/'quick-original.db',first,'quick',RULES)
        translate_db(first,second,'quick',RULES)
        self.assertEqual(first.read_bytes(),second.read_bytes())
        with closing(sqlite3.connect(second)) as db, db:
            for ident,(icon,name) in QUICK.items():
                row = db.execute('select icon,name,funcType from MisckeyConfigFuncDB where id=?',(ident,)).fetchone()
                if row:
                    self.assertEqual(row[:2],(icon,name))
                    if ident==11:self.assertEqual(row[2],-1)
            db.execute("update MisckeyConfigFuncDB set name='自动对焦' where id=5")
            self.assertEqual(db.execute('select name from MisckeyConfigFuncDB where id=5').fetchone()[0],'Автофокус')

    def test_unknown_quick_icon_stops_before_device_write(self):
        src=self.out/'unknown.db';src.write_bytes((FIXTURES/'quick-original.db').read_bytes())
        with closing(sqlite3.connect(src)) as db, db:
            db.execute("update MisckeyConfigFuncDB set icon='different' where id=5")
        with self.assertRaisesRegex(RuntimeError,'Unexpected icon'):
            translate_db(src,self.out/'out.db','quick',RULES)

    def test_atmosphere_rules_and_repeated_install(self):
        first,second = self.out/'first.db',self.out/'second.db'
        translate_db(FIXTURES/'atmosphere-original.db',first,'atmosphere')
        translate_db(first,second,'atmosphere')
        self.assertEqual(first.read_bytes(),second.read_bytes())
        with closing(sqlite3.connect(second)) as db, db:
            db.execute("update groups set name='天花板' where group_id='9'")
            self.assertEqual(db.execute("select name from groups where group_id='9'").fetchone()[0],'Потолок')

    def test_catalog_only_changes_eight_name_handles_and_is_reversible(self):
        original=FIXTURES/'catalog-original.ser';translated=self.out/'ru.ser';second=self.out/'second.ser'
        self.assertEqual(translate_catalog(original,translated),8)
        self.assertEqual(translate_catalog(translated,second),0)
        self.assertEqual(translated.read_bytes(),second.read_bytes())
        restored=self.out/'original.ser';translate_catalog(translated,restored,catalog_names(original))
        self.assertEqual(original.read_bytes(),restored.read_bytes())

    def test_later_rollback_preserves_user_changes(self):
        original=FIXTURES/'atmosphere-original.db';installed=self.out/'installed.db'
        translate_db(original,installed,'atmosphere')
        current=self.out/'current.db';current.write_bytes(installed.read_bytes())
        with closing(sqlite3.connect(current)) as db, db:
            db.execute("update groups set tips='later user change' where group_id='9'")
            db.execute("insert into groups(group_id,name,tips) values('new-group','New name','new data')")
        restored=self.out/'restored.db';restore_db(current,original,installed,restored,'atmosphere')
        with closing(sqlite3.connect(restored)) as db, db:
            self.assertEqual(db.execute("select name,tips from groups where group_id='9'").fetchone(),('天花板','later user change'))
            self.assertEqual(db.execute("select name from groups where group_id='new-group'").fetchone()[0],'New name')
            self.assertFalse(db.execute("select 1 from sqlite_master where name like 'beam_atmosphere_ru_%'").fetchall())

if __name__=='__main__':
    unittest.main()
