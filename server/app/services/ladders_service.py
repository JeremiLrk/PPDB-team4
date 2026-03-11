from server.app.models.ladder import Ladder

def get_all_club_ladders(club_id: int):
    return Ladder.query.filter_by(club_id=club_id).all()