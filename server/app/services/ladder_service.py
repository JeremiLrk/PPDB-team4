from server.app.models.ladder import Ladder

def get_all_ladder():
    return Ladder.query.all()