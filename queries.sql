-- Bind :rapid=30, :profile=3, :fanin=5 for baseline.

-- One row per customer; a timing/amount signal, not fund attribution.
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
FROM candidate_pairs WHERE pair_rank=1 ORDER BY customer_id;

-- Currency stored in integer cents; expected volume is a synthetic CDD input.
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
ORDER BY customer_id;

-- Fixed one-day observation window, not rolling 24 hours.
SELECT c.customer_id,c.name,c.scenario,COUNT(DISTINCT t.counterparty_id) AS signal
FROM customers c JOIN accounts a ON a.customer_id=c.customer_id
JOIN transactions t ON t.account_id=a.account_id
WHERE c.scenario='fanin' AND t.direction='in'
AND t.occurred_at>='2026-01-15' AND t.occurred_at<'2026-01-16'
GROUP BY c.customer_id,c.name,c.scenario
HAVING COUNT(DISTINCT t.counterparty_id)>=:fanin
ORDER BY c.customer_id;

SELECT 'Missing customer country (review required)' AS check_name, COUNT(*) AS issues FROM customers WHERE country IS NULL
UNION ALL SELECT 'Orphan accounts',COUNT(*) FROM accounts a LEFT JOIN customers c ON c.customer_id=a.customer_id WHERE c.customer_id IS NULL
UNION ALL SELECT 'Orphan transactions',COUNT(*) FROM transactions t LEFT JOIN accounts a ON a.account_id=t.account_id WHERE a.account_id IS NULL
UNION ALL SELECT 'Nonpositive amounts',COUNT(*) FROM transactions WHERE amount_cents<=0
UNION ALL SELECT 'Duplicate transaction IDs',COUNT(*) FROM (SELECT transaction_id FROM transactions GROUP BY transaction_id HAVING COUNT(*)>1);