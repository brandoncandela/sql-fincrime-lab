PRAGMA foreign_keys=ON;
CREATE TABLE customers(customer_id TEXT PRIMARY KEY,name TEXT NOT NULL,scenario TEXT NOT NULL CHECK(scenario IN ('rapid','profile','fanin')),business_type TEXT NOT NULL,expected_daily_cents INTEGER NOT NULL CHECK(expected_daily_cents>0),country TEXT,context TEXT NOT NULL);
CREATE TABLE accounts(account_id TEXT PRIMARY KEY,customer_id TEXT NOT NULL REFERENCES customers(customer_id));
CREATE TABLE transactions(transaction_id TEXT PRIMARY KEY,account_id TEXT NOT NULL REFERENCES accounts(account_id),counterparty_id TEXT NOT NULL,direction TEXT NOT NULL CHECK(direction IN ('in','out')),amount_cents INTEGER NOT NULL CHECK(amount_cents>0),occurred_at TEXT NOT NULL,currency TEXT NOT NULL CHECK(currency='USD'));
CREATE INDEX idx_accounts_customer ON accounts(customer_id);
CREATE INDEX idx_transactions_account_direction_time ON transactions(account_id,direction,occurred_at);
CREATE TABLE evaluation_labels(customer_id TEXT PRIMARY KEY REFERENCES customers(customer_id),seeded_positive INTEGER NOT NULL CHECK(seeded_positive IN (0,1)),rationale TEXT NOT NULL);
