import unittest,tempfile,shutil,sqlite3
from contextlib import closing
from pathlib import Path
from catalog_metadata import apply_db,apply_catalog,restore_db_metadata,restore_catalog_metadata,entries,values_of
from transforms import translate_catalog,parse_catalog

FIXTURES=Path(__file__).resolve().parent/'tests/fixtures'

class MetadataTests(unittest.TestCase):
    def test_server_refresh_with_mixed_duplicate_names(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);baseline=root/'baseline.ser';current=root/'catalog.ser';installed=root/'installed.ser'
            translate_catalog(FIXTURES/'catalog-mixed-original.ser',baseline)
            def names(path):
                parser,bean=parse_catalog(path.read_bytes())
                return {v for k,v in values_of(entries(parser,bean)[0]).items() if k[:3]==('Screensaver','222','name')}
            self.assertGreater(len(names(baseline)),1)
            shutil.copyfile(baseline,current)
            self.assertGreater(apply_catalog(current),0)
            self.assertEqual(len(names(current)),1)
            shutil.copyfile(current,installed)
            self.assertEqual(apply_catalog(current),0)
            restore_catalog_metadata(current,baseline,installed)
            self.assertEqual(current.read_bytes(),baseline.read_bytes())

    def test_catalog_is_idempotent_and_rollback_preserves_serialized_bytes(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);current=root/'catalog.ser';installed=root/'installed.ser'
            baseline=root/'baseline.ser'
            translate_catalog(FIXTURES/'catalog-original.ser',baseline)
            shutil.copyfile(baseline,current)
            self.assertGreater(apply_catalog(current),0)
            shutil.copyfile(current,installed)
            self.assertEqual(apply_catalog(current),0)
            restore_catalog_metadata(current,baseline,installed)
            self.assertEqual(current.read_bytes(),baseline.read_bytes())

    def test_metadata_rollback_preserves_later_name_and_selection(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);current=root/'current.db';installed=root/'installed.db'
            baseline=FIXTURES/'atmosphere-original.db'
            shutil.copyfile(baseline,current)
            self.assertGreater(apply_db(current),0)
            shutil.copyfile(current,installed)
            self.assertEqual(apply_db(current),0)
            with closing(sqlite3.connect(current)) as db,db:
                ident=db.execute('select min(_id) from screen_saver').fetchone()[0]
                db.execute('update screen_saver set name=?,is_selected=1 where _id=?',('Моё название',ident))
            restore_db_metadata(current,baseline,installed)
            with closing(sqlite3.connect(current)) as db:
                self.assertEqual(db.execute('select name,is_selected from screen_saver where _id=?',(ident,)).fetchone(),('Моё название',1))

if __name__=='__main__':unittest.main()
