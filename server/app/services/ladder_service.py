from server.app.models.team import Team
from server.app.models.ladder_team import LadderTeam
from server.app.models import db

def get_all_players_ladder(ladder_id: int):
    return (
        db.session.query(Team, LadderTeam)
        .join(LadderTeam, Team.id == LadderTeam.team_id)
        .filter(LadderTeam.ladder_id == ladder_id)
        .order_by(LadderTeam.rank)
        .all()
    )