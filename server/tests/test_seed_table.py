import json

from server.app.models.match_rule import MatchRuleSet
from server.app.utils.seed_table import seed_table
from server.extensions import db


def test_seed_table_inserts_all_rows_with_unique_name(tmp_path, app):
    seed_path = tmp_path / "seed.json"
    seed_path.write_text(
        json.dumps(
            [
                {
                    "name": "Seed One",
                    "description": "First row",
                    "match_format": "best_of_3",
                    "third_set_format": "super_tiebreak",
                    "deuce_rule": "advantage",
                    "game_format": "doubles",
                    "can_be_used_by_others": True,
                },
                {
                    "name": "Seed Two",
                    "description": "Second row",
                    "match_format": "timed",
                    "timed_duration_minutes": 45,
                    "third_set_format": "super_tiebreak",
                    "deuce_rule": "golden_point",
                    "game_format": "singles",
                    "can_be_used_by_others": True,
                },
            ]
        ),
        encoding="utf-8",
    )

    with app.app_context():
        seed_table(MatchRuleSet, str(seed_path), unique_fields=["name"])
        seed_table(MatchRuleSet, str(seed_path), unique_fields=["name"])
        rows = MatchRuleSet.query.order_by(MatchRuleSet.id.asc()).all()

    assert [row.name for row in rows] == ["Seed One", "Seed Two"]
    assert rows[1].game_format == "singles"
