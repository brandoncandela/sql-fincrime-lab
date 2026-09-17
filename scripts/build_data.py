"""Deterministic synthetic fixtures. No customer or employer data."""
import sqlite3, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
D=ROOT/'dist'
SCHEMA='''PRAGMA foreign_keys=ON;
CREATE TABLE customers(customer_id TEXT PRIMARY KEY,name TEXT NOT NULL,scenario TEXT NOT NULL CHECK(scenario IN ('rapid','profile','fanin')),business_type TEXT NOT NULL,expected_daily_cents INTEGER NOT NULL CHECK(expected_daily_cents>0),country TEXT,context TEXT NOT NULL);
CREATE TABLE accounts(account_id TEXT PRIMARY KEY,customer_id TEXT NOT NULL REFERENCES customers(customer_id));
CREATE TABLE transactions(transaction_id TEXT PRIMARY KEY,account_id TEXT NOT NULL REFERENCES accounts(account_id),counterparty_id TEXT NOT NULL,direction TEXT NOT NULL CHECK(direction IN ('in','out')),amount_cents INTEGER NOT NULL CHECK(amount_cents>0),occurred_at TEXT NOT NULL,currency TEXT NOT NULL CHECK(currency='USD'));
CREATE INDEX idx_accounts_customer ON accounts(customer_id);
CREATE INDEX idx_transactions_account_direction_time ON transactions(account_id,direction,occurred_at);
CREATE TABLE evaluation_labels(customer_id TEXT PRIMARY KEY REFERENCES customers(customer_id),seeded_positive INTEGER NOT NULL CHECK(seeded_positive IN (0,1)),rationale TEXT NOT NULL);
'''
QUERIES={
'rapid':'''-- One row per customer; a timing/amount signal, not fund attribution.
WITH candidate_pairs AS (
 SELECT c.customer_id,c.name,c.scenario,i.transaction_id AS incoming_id,
 o.transaction_id AS outgoing_id,
 CAST(strftime('%s',o.occurred_at) AS INTEGER)-CAST(strftime('%s',i.occurred_at) AS INTEGER) AS gap_seconds,
 ROW_NUMBER() OVER (PARTITION BY c.customer_id ORDER BY o.occurred_at,i.transaction_id) AS pair_rank
 FROM customers c JOIN accounts a ON a.customer_id=c.customer_id
 JOIN transactions i ON i.account_id=a.account_id AND i.direction='in'
 JOIN transactions o ON o.account_id=a.account_id AND o.direction='out'
 WHERE c.scenario='rapid' AND i.amount_cents>=500000
 AND i.occurred_at>='2026-01-15' AND o.occurred_at<'2026-01-16'
 AND o.amount_cents BETWEEN i.amount_cents*0.90 AND i.amount_cents*1.10
 AND CAST(strftime('%s',o.occurred_at) AS INTEGER)-CAST(strftime('%s',i.occurred_at) AS INTEGER) BETWEEN 1 AND :rapid*60
)
SELECT customer_id,name,scenario,ROUND(gap_seconds/60.0,1) AS signal
FROM candidate_pairs WHERE pair_rank=1 ORDER BY customer_id;''',
'profile':'''-- Currency stored in integer cents; expected volume is a synthetic CDD input.
WITH daily_out AS (
 SELECT c.customer_id,c.name,c.scenario,c.expected_daily_cents,
 SUM(t.amount_cents) AS outbound_cents
 FROM customers c JOIN accounts a ON a.customer_id=c.customer_id
 JOIN transactions t ON t.account_id=a.account_id
 WHERE c.scenario='profile' AND t.direction='out'
 AND t.occurred_at>='2026-01-15' AND t.occurred_at<'2026-01-16'
 GROUP BY c.customer_id,c.name,c.scenario,c.expected_daily_cents
)
SELECT customer_id,name,scenario,ROUND(1.0*outbound_cents/expected_daily_cents,2) AS signal
FROM daily_out WHERE outbound_cents>=expected_daily_cents*:profile
ORDER BY customer_id;''',
'fanin':'''-- Fixed one-day observation window, not rolling 24 hours.
SELECT c.customer_id,c.name,c.scenario,COUNT(DISTINCT t.counterparty_id) AS signal
FROM customers c JOIN accounts a ON a.customer_id=c.customer_id
JOIN transactions t ON t.account_id=a.account_id
WHERE c.scenario='fanin' AND t.direction='in'
AND t.occurred_at>='2026-01-15' AND t.occurred_at<'2026-01-16'
GROUP BY c.customer_id,c.name,c.scenario
HAVING COUNT(DISTINCT t.counterparty_id)>=:fanin
ORDER BY c.customer_id;''',
'quality':'''SELECT 'Missing customer country (review required)' AS check_name, COUNT(*) AS issues FROM customers WHERE country IS NULL
UNION ALL SELECT 'Orphan accounts',COUNT(*) FROM accounts a LEFT JOIN customers c ON c.customer_id=a.customer_id WHERE c.customer_id IS NULL
UNION ALL SELECT 'Orphan transactions',COUNT(*) FROM transactions t LEFT JOIN accounts a ON a.account_id=t.account_id WHERE a.account_id IS NULL
UNION ALL SELECT 'Nonpositive amounts',COUNT(*) FROM transactions WHERE amount_cents<=0
UNION ALL SELECT 'Duplicate transaction IDs',COUNT(*) FROM (SELECT transaction_id FROM transactions GROUP BY transaction_id HAVING COUNT(*)>1);'''
}
path=D/'lab.sqlite'
if path.exists(): path.unlink()
db=sqlite3.connect(path);db.executescript(SCHEMA)
seq=0
def tx(account,cp,direction,amount,minute):
 global seq
 seq+=1
 stamp=f'2026-01-15T{minute//60:02}:{minute%60:02}:00Z'
 db.execute('INSERT INTO transactions VALUES(?,?,?,?,?,?,?)',(f'TX{seq:04}',account,cp,direction,round(amount*100),stamp,'USD'))
for scenario in ['rapid','profile','fanin']:
 for i in range(12):
  cid=f'{scenario[0].upper()}{i+1:02}';acc='A'+cid;positive=i<4;confounder=4<=i<8
  if scenario=='rapid':
   context='Incoming third-party payment followed by a similar outgoing transfer. Purpose and relationship need explanation.' if positive else 'Treasury sweep schedule documented in this fictional fixture; verify the schedule and counterparties before closure.' if confounder else 'Routine payments spread over the day.'
  elif scenario=='profile':
   context='Outbound activity exceeds the expected profile. No supporting purpose is supplied in this fixture.' if positive else 'Seasonal inventory purchase documented in the fixture; validate invoice and refresh the expected activity profile.' if confounder else 'Activity consistent with the fictional operating profile.'
  else:
   context='Several unrelated senders fund a personal account. Source and relationships need review.' if positive else 'Fictional online seller receives payments from distinct customers; verify sales and business activity.' if confounder else 'Small number of expected counterparties.'
  db.execute('INSERT INTO customers VALUES(?,?,?,?,?,?,?)',(cid,f'Demo {scenario.title()} {i+1:02}',scenario,'Individual' if positive else 'Small business',100000,None if i==11 else 'US',context))
  db.execute('INSERT INTO accounts VALUES(?,?)',(acc,cid))
  db.execute('INSERT INTO evaluation_labels VALUES(?,?,?)',(cid,int(positive),'Seeded review-worthy pattern; not an illicit-activity determination.' if positive else 'Seeded benign activity; still requires supporting evidence in real work.'))
  if scenario=='rapid':
   gap=[8,18,35,70,5,12,22,50,140,170,200,230][i]
   tx(acc,'SENDER'+cid,'in',8000,540);tx(acc,'PAYEE'+cid,'out',8000,540+gap)
  elif scenario=='profile':
   ratio=[2.5,4,5,7,3.5,4.5,6,2,0.8,1,1.4,1.8][i]
   for j in range(5): tx(acc,f'VENDOR{j}','out',ratio*1000/5,540+j*40)
   tx(acc,'REVENUE'+cid,'in',1000,480)
  else:
   n=[4,6,8,10,5,7,9,12,1,2,2,3][i]
   for j in range(n): tx(acc,f'PAYER{i}-{j}','in',500+j*20,540+j*10)
   tx(acc,'RENT'+cid,'out',800,1000)
db.execute('PRAGMA optimize');db.commit();db.close()
(D/'schema.sql').write_text(SCHEMA)
(D/'queries.json').write_text(json.dumps(QUERIES,indent=2))
(D/'queries.sql').write_text('-- Bind :rapid=30, :profile=3, :fanin=5 for baseline.\n\n'+'\n\n'.join(QUERIES.values()))
print(f'Built 36 customers, {seq} transactions, 12 seeded positives; 3 missing-country fixtures.')
