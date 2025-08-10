-- Function to backfill claim IDs for existing users
CREATE OR REPLACE FUNCTION backfill_existing_users_claims()
RETURNS void AS $$
BEGIN
    -- Insert records for users who don't have entries in claims_master
    INSERT INTO claims_master (
        user_id,
        active_claim_id,
        submitted_claim_id
    )
    SELECT 
        u.auth_id,
        generate_claim_id(),
        generate_claim_id(),
        generate_claim_id()
    FROM user_table u
    LEFT JOIN claims_master cm ON u.auth_id = cm.user_id
    WHERE cm.id IS NULL;
END;
$$ LANGUAGE plpgsql;

-- Execute the backfill function
SELECT backfill_existing_users_claims();

-- Drop the function after use (optional)
DROP FUNCTION backfill_existing_users_claims(); 