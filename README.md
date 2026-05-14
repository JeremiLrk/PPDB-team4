# Team 4 - NetRank

NetRank is a club, team, and ladder management platform for organizing matches, handling disputes, and tracking ladder rankings with an Elo-based rating system.

## What The Project Does

NetRank supports the full workflow for competitive club play:

- Players create and manage availability for match planning.
- Clubs can be searched and joined through join requests.
- Club members can create and manage teams.
- Weekly match proposals can be accepted, rejected, reset, and scored.
- Disputed match results can be reviewed and resolved by authorized club staff.
- Ladder rankings are updated automatically after finalized results.
- Match rule sets can be created, edited, and assigned to ladders.
- Club and ladder settings can be managed from the dashboard.

## Core Features

### Player Dashboard

- Edit profile details.
- Change password.
- Add and remove availability blocks.
- View dashboard notifications and club-related actions.

### Club Management

- Search for clubs.
- Send join requests.
- Review incoming join requests as a club admin.
- Create clubs and manage membership.
- Work with teams inside a club.

### Ladder Management

- Browse ladders for a club.
- View ladder standings and team rankings.
- Add teams to ladders.
- Assign ladders to specific rule sets.
- Use ladder-specific rating behavior with Elo updates.

### Match Flow

- Generate weekly match proposals.
- Accept or reject proposed matches.
- Submit scores from both sides.
- Detect conflicting submissions as disputed matches.
- Let ladder admins resolve disputes.
- Finalize results and update ladder rankings automatically.

### Rulesets

- Create new match rule sets.
- Update existing rule sets.
- Delete unused rule sets.
- Configure structured rules such as match format, third set handling, deuce rules, and game format.

### Disputed Matches

- View disputed matches in a dedicated review area.
- Inspect both sides' submitted scores.
- See the linked ladder and ruleset for the match.
- Resolve the result when you have permission to do so.

## Technology Stack

- Backend: Python, Flask, SQLAlchemy
- Database: PostgreSQL
- Frontend: React
- Local development: Node.js/npm
- Optional cache/session support: Redis when `REDIS_URL` is configured

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

The project includes a helper script for local development. It starts the backend, frontend, and PostgreSQL services expected by the app.

```bash
./dev_tools/start_project.sh
```

To start with the demo seed as well:

```bash
./dev_tools/start_project.sh --seed
```

If the backend is already running on port `5000`, start with:

```bash
./dev_tools/start_project.sh --restart --seed
```

or stop the existing backend and frontend processes before launching again.

If you want to control the services manually, use separate terminals.

Without seed:

```bash
# terminal 1
source .venv/bin/activate
python -m server.wsgi

# terminal 2
cd client
npm run dev
```

With seed:

```bash
# terminal 1
source .venv/bin/activate
SEED_ON_STARTUP=1 python -m server.wsgi

# terminal 2
cd client
npm run dev
```

The manual startup path assumes PostgreSQL is already running.

## Test

Run the full backend test suite from the project root after activating the virtual environment:

```bash
source .venv/bin/activate
python -m pytest
```

Frontend tests:

```bash
cd client
npm test
```
