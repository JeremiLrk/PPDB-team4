from server.app import create_app
from server.config import DEBUG, HOST

app = create_app()

if __name__ == "__main__":
    app.run(HOST, debug=DEBUG)