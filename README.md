# Team 4 - NetRank

NetRank is a web app for club, team, and ladder management with match proposals, score submission, and rankings.

## Requirements

- Python 3.11
- PostgreSQL
- Node.js 20+
- npm
- Redis optional, used only when `REDIS_URL` is configured

## Install

Backend dependencies:

```bash
python3.11 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

Frontend dependencies:

```bash
cd client
npm install
```

## Run

The project includes a helper script for local development:

```bash
./dev_tools/start_project.sh
```

It starts the backend, frontend, and PostgreSQL services expected by the app.
