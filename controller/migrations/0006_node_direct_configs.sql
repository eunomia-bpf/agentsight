CREATE TABLE IF NOT EXISTS node_direct_configs (
    node_id TEXT NOT NULL REFERENCES nodes(id) ON DELETE CASCADE,
    owner_user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    ciphertext TEXT NOT NULL,
    iv TEXT NOT NULL,
    version INTEGER NOT NULL,
    created_at INTEGER NOT NULL,
    updated_at INTEGER NOT NULL,
    PRIMARY KEY (node_id, owner_user_id)
);

CREATE INDEX IF NOT EXISTS idx_node_direct_configs_owner
    ON node_direct_configs(owner_user_id, node_id);
