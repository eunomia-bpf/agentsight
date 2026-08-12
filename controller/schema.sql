CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    email TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    avatar_url TEXT,
    created_at INTEGER NOT NULL,
    updated_at INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS oauth_accounts (
    provider TEXT NOT NULL,
    provider_user_id TEXT NOT NULL,
    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    PRIMARY KEY (provider, provider_user_id)
);

CREATE TABLE IF NOT EXISTS oauth_states (
    state_hash TEXT PRIMARY KEY,
    provider TEXT NOT NULL,
    return_to TEXT NOT NULL,
    code_challenge TEXT NOT NULL,
    expires_at INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS auth_codes (
    code_hash TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    provider TEXT NOT NULL,
    code_challenge TEXT NOT NULL,
    expires_at INTEGER NOT NULL,
    consumed_at INTEGER
);

CREATE TABLE IF NOT EXISTS sessions (
    token_hash TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    expires_at INTEGER NOT NULL,
    created_at INTEGER NOT NULL,
    last_seen_at INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS nodes (
    id TEXT PRIMARY KEY,
    owner_user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    version TEXT,
    public_key TEXT,
    relay_token_hash TEXT,
    direct_config_ciphertext TEXT,
    direct_config_iv TEXT,
    direct_config_version INTEGER,
    connection_mode TEXT NOT NULL DEFAULT 'direct',
    last_seen_at INTEGER NOT NULL,
    created_at INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_nodes_owner ON nodes(owner_user_id, last_seen_at DESC);
CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id, expires_at);
CREATE INDEX IF NOT EXISTS idx_oauth_states_expiry ON oauth_states(expires_at);
CREATE INDEX IF NOT EXISTS idx_auth_codes_expiry ON auth_codes(expires_at);
CREATE INDEX IF NOT EXISTS idx_auth_codes_consumed ON auth_codes(consumed_at);
CREATE INDEX IF NOT EXISTS idx_sessions_expiry ON sessions(expires_at);
