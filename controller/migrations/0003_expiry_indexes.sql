CREATE INDEX IF NOT EXISTS idx_oauth_states_expiry ON oauth_states(expires_at);
CREATE INDEX IF NOT EXISTS idx_auth_codes_expiry ON auth_codes(expires_at);
CREATE INDEX IF NOT EXISTS idx_auth_codes_consumed ON auth_codes(consumed_at);
CREATE INDEX IF NOT EXISTS idx_sessions_expiry ON sessions(expires_at);
