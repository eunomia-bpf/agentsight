ALTER TABLE oauth_states ADD COLUMN code_challenge TEXT;
ALTER TABLE auth_codes ADD COLUMN code_challenge TEXT;
