CREATE TABLE IF NOT EXISTS organizations (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    kind TEXT NOT NULL CHECK (kind IN ('personal', 'team')),
    plan TEXT NOT NULL DEFAULT 'free' CHECK (plan IN ('free', 'pro', 'team', 'enterprise')),
    billing_interval TEXT CHECK (billing_interval IS NULL OR billing_interval IN ('monthly', 'annual')),
    billing_status TEXT NOT NULL DEFAULT 'inactive' CHECK (billing_status IN ('inactive', 'trialing', 'active', 'past_due', 'canceled')),
    external_customer_id TEXT,
    external_subscription_id TEXT,
    current_period_end INTEGER,
    created_by_user_id TEXT REFERENCES users(id) ON DELETE SET NULL,
    created_at INTEGER NOT NULL,
    updated_at INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS memberships (
    organization_id TEXT NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK (role IN ('viewer', 'operator', 'admin', 'owner')),
    created_at INTEGER NOT NULL,
    updated_at INTEGER NOT NULL,
    PRIMARY KEY (organization_id, user_id)
);

CREATE TABLE IF NOT EXISTS organization_configs (
    organization_id TEXT NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    key TEXT NOT NULL,
    value_json TEXT NOT NULL,
    updated_by TEXT NOT NULL,
    updated_at INTEGER NOT NULL,
    PRIMARY KEY (organization_id, key)
);

CREATE TABLE IF NOT EXISTS entitlements (
    id TEXT PRIMARY KEY,
    user_id TEXT REFERENCES users(id) ON DELETE CASCADE,
    organization_id TEXT REFERENCES organizations(id) ON DELETE CASCADE,
    kind TEXT NOT NULL,
    source TEXT NOT NULL,
    source_ref TEXT,
    expires_at INTEGER,
    revoked_at INTEGER,
    created_at INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS organization_invites (
    token_hash TEXT PRIMARY KEY,
    organization_id TEXT NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    email TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('viewer', 'operator', 'admin')),
    invited_by_user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    expires_at INTEGER NOT NULL,
    consumed_at INTEGER,
    created_at INTEGER NOT NULL
);

INSERT OR IGNORE INTO organizations (
    id, name, kind, plan, billing_status, created_by_user_id, created_at, updated_at
)
SELECT
    'org_personal_' || replace(id, '-', ''),
    'Personal',
    'personal',
    'free',
    'inactive',
    id,
    created_at,
    updated_at
FROM users;

INSERT OR IGNORE INTO memberships (organization_id, user_id, role, created_at, updated_at)
SELECT
    'org_personal_' || replace(id, '-', ''),
    id,
    'owner',
    created_at,
    updated_at
FROM users;

CREATE TABLE nodes_v2 (
    id TEXT PRIMARY KEY,
    organization_id TEXT NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    version TEXT,
    public_key TEXT,
    relay_token_hash TEXT,
    connection_mode TEXT NOT NULL DEFAULT 'direct',
    last_seen_at INTEGER NOT NULL,
    created_at INTEGER NOT NULL
);

INSERT INTO nodes_v2 (
    id, organization_id, name, version, public_key, relay_token_hash,
    connection_mode, last_seen_at, created_at
)
SELECT
    id,
    'org_personal_' || replace(owner_user_id, '-', ''),
    name,
    version,
    public_key,
    relay_token_hash,
    connection_mode,
    last_seen_at,
    created_at
FROM nodes;

DROP TABLE nodes;
ALTER TABLE nodes_v2 RENAME TO nodes;

CREATE INDEX IF NOT EXISTS idx_memberships_user ON memberships(user_id, organization_id);
CREATE INDEX IF NOT EXISTS idx_memberships_org ON memberships(organization_id, role);
CREATE INDEX IF NOT EXISTS idx_nodes_org ON nodes(organization_id, last_seen_at DESC);
CREATE INDEX IF NOT EXISTS idx_entitlements_user ON entitlements(user_id, kind, revoked_at, expires_at);
CREATE INDEX IF NOT EXISTS idx_entitlements_org ON entitlements(organization_id, kind, revoked_at, expires_at);
CREATE INDEX IF NOT EXISTS idx_invites_org ON organization_invites(organization_id, expires_at);
CREATE INDEX IF NOT EXISTS idx_invites_email ON organization_invites(email, expires_at);
