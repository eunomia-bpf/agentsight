-- AgentSight hosted preview: every registered user gets unrestricted access to
-- the currently implemented hosted feature set. Keep the public price catalog
-- unchanged; this migration only removes billing gates during the preview.
--
-- Personal organizations need Pro for managed Node registration/relay. Team
-- organizations need Team for multi-member/RBAC operations. Those are the
-- highest relevant gates for each organization kind today.

UPDATE organizations
SET plan = CASE kind WHEN 'personal' THEN 'pro' ELSE 'team' END,
    billing_status = 'active',
    updated_at = unixepoch()
WHERE plan = 'free' AND billing_status = 'inactive';

CREATE TRIGGER IF NOT EXISTS organizations_unlimited_preview_after_insert
AFTER INSERT ON organizations
BEGIN
    UPDATE organizations
    SET plan = CASE NEW.kind WHEN 'personal' THEN 'pro' ELSE 'team' END,
        billing_status = 'active',
        updated_at = NEW.updated_at
    WHERE id = NEW.id
      AND NEW.plan = 'free'
      AND NEW.billing_status = 'inactive';
END;
