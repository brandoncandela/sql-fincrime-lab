import unittest,sqlite3,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class SQLScenarios(unittest.TestCase):
 def setUp(self):
  self.db=sqlite3.connect(':memory:');src=sqlite3.connect(ROOT/'dist/lab.sqlite');src.backup(self.db);src.close();self.db.execute('PRAGMA foreign_keys=ON');self.q=json.loads((ROOT/'dist/queries.json').read_text())
 def tearDown(self): self.db.close()
 def ids(self,k,value):return {r[0] for r in self.db.execute(self.q[k],{k:value})}
 def test_known_baseline_cases(self):
  self.assertEqual(self.ids('rapid',30),{'R01','R02','R05','R06','R07'})
  self.assertEqual(self.ids('profile',3),{'P02','P03','P04','P05','P06','P07'})
  self.assertEqual(self.ids('fanin',5),{'F02','F03','F04','F05','F06','F07','F08'})
 def test_boundary_inclusion(self):
  self.assertIn('R01',self.ids('rapid',8));self.assertNotIn('R01',self.ids('rapid',7))
  self.assertIn('P02',self.ids('profile',4));self.assertNotIn('P02',self.ids('profile',4.01))
  self.assertIn('F02',self.ids('fanin',6));self.assertNotIn('F02',self.ids('fanin',7))
 def test_repeated_sender_not_counted_twice(self):
  self.db.execute("INSERT INTO transactions VALUES('TEST','AF01','PAYER0-0','in',50000,'2026-01-15T15:00:00Z','USD')")
  self.assertNotIn('F01',self.ids('fanin',5))
 def test_wrong_day_excluded(self):
  self.db.execute("INSERT INTO transactions VALUES('TEST','AP09','EXTRA','out',99999999,'2026-01-16T00:00:00Z','USD')")
  self.assertNotIn('P09',self.ids('profile',3))
 def test_duplicate_id_and_orphan_rejected(self):
  with self.assertRaises(sqlite3.IntegrityError): self.db.execute("INSERT INTO accounts VALUES('BAD','UNKNOWN')")
  with self.assertRaises(sqlite3.IntegrityError): self.db.execute("INSERT INTO transactions SELECT * FROM transactions LIMIT 1")
 def test_baseline_confusion_counts(self):
  hits=self.ids('rapid',30)|self.ids('profile',3)|self.ids('fanin',5)
  positives={r[0] for r in self.db.execute('SELECT customer_id FROM evaluation_labels WHERE seeded_positive=1')}
  self.assertEqual((len(hits),len(hits&positives),len(positives-hits)),(18,8,4))
 def test_tighter_queue_can_miss_more(self):
  hits=self.ids('rapid',5)|self.ids('profile',8)|self.ids('fanin',12)
  self.assertEqual(hits,{'R05','F08'})
 def test_data_quality_and_index(self):
  result=dict(self.db.execute(self.q['quality']));self.assertEqual(sum(result.values()),3)
  plan=' '.join(str(x) for x in self.db.execute('EXPLAIN QUERY PLAN SELECT * FROM transactions WHERE account_id=? AND direction=? AND occurred_at>?',('AR01','in','2026-01-15')))
  self.assertIn('idx_transactions_account_direction_time',plan)
if __name__=='__main__':unittest.main()
