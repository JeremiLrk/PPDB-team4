/*
 =====
 TRIGGERS
 =====
 */
CREATE OR REPLACE FUNCTION check_teams_no_common_players()
    RETURNS TRIGGER AS $$
DECLARE
    common_count INT;
BEGIN
    SELECT COUNT(*)
    INTO common_count

    FROM player_team pt1
             JOIN player_team pt2 ON pt1.player_id = pt2.player_id

    WHERE pt1.team_id = NEW.team1_id
      AND pt2.team_id = NEW.team2_id;

    IF common_count > 0 THEN
        RAISE WARNING 'Warning: Match has teams with common players';
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_check_teams_no_common_players
    ON match_proposal;

CREATE TRIGGER trg_check_teams_no_common_players
    BEFORE INSERT OR UPDATE ON match_proposal
    FOR EACH ROW
EXECUTE FUNCTION check_teams_no_common_players();



CREATE OR REPLACE FUNCTION prevent_match_rule_update()
    RETURNS trigger AS $$
BEGIN
    RAISE EXCEPTION 'match_rule is immutable';
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_no_update_match_rule ON match_rule;

CREATE TRIGGER trg_no_update_match_rule
    BEFORE UPDATE ON match_rule
    FOR EACH ROW
    WHEN (
        OLD.name                IS DISTINCT FROM NEW.name OR
        OLD.description         IS DISTINCT FROM NEW.description OR
        OLD.can_be_used_by_others IS DISTINCT FROM NEW.can_be_used_by_others OR
        OLD.creator_id          IS DISTINCT FROM NEW.creator_id OR
        OLD.club_id             IS DISTINCT FROM NEW.club_id OR
        OLD.created_at          IS DISTINCT FROM NEW.created_at
        )
EXECUTE FUNCTION prevent_match_rule_update();