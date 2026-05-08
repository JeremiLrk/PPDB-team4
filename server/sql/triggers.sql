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