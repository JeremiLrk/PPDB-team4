# Team 4 - NetRank

NetRank is a club, team, and ladder management platform for organizing matches, handling disputes, and tracking ladder rankings with an Elo-based rating system.

## Requirements

- Python 3.11
- PostgreSQL
- Node.js 20+
- npm
- Redis is optional and only used when `REDIS_URL` is configured

## Environment

The backend loads environment variables from `server/.env`.

Required backend variables:

- `PW_RESET_SALT`
- `RESEND_API_KEY`
- `FRONTEND_URL`
- `MAIL_FROM`
- `WEATHER_API_KEY` - required for club creation city lookup and weather display

Optional backend variables:

- `SECRET_KEY` - defaults to a development value if not set
- `EMAIL_VERIFICATION_SALT` - defaults to `email-verify-salt`
- `REDIS_URL` - enables Redis-backed cache/session support

Startup flags read by the Flask app:

- `RESET_DB_ON_STARTUP` - drops and recreates the database schema on startup
- `SEED_ON_STARTUP` - seeds demo data on startup
- `SEED_VERBOSE` - controls seed logging when `SEED_ON_STARTUP` is enabled

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

The easiest way to start everything locally is the helper script from the project root:

```bash
./dev_tools/start_project.sh
```

To start with demo seed data:

```bash
./dev_tools/start_project.sh --seed
```

If the backend is already running on port `5000`, restart the local processes first:

```bash
./dev_tools/start_project.sh --restart --seed
```

If you want to start services manually, use separate terminals.

Without seed data:

```bash
# terminal 1
source .venv/bin/activate
python -m server.wsgi

# terminal 2
cd client
npm run dev
```

With seed data:

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

Run the backend test suite from the project root after activating the virtual environment:

```bash
source .venv/bin/activate
python -m pytest
```

Run the frontend tests:

```bash
cd client
npm test
```

## Features

NetRank is built around a clear hierarchy of users and competitive objects.

```text
Account
|-- Player
|-- TeamManager
|   |-- ClubOwner
|-- Administrator

Club
|-- Teams
|-- Ladders
    |-- Ladder teams
    |-- Rulesets
    |-- Match proposals
    |-- Score submissions
    |-- Disputed matches
```

### User Roles

- `Account` is the base identity for every user. It stores login details, profile data, and verification state.
- `Player` is the user type for someone who takes part in teams and match activity.
- `TeamManager` is the role for handling team administration.
- `ClubOwner` is the role for managing clubs and the teams inside them.
- `Administrator` is the top-level role for platform-wide moderation and dispute handling.

### Clubs And Teams

- Clubs are the main organizational unit in the platform.
- A club can contain multiple teams.
- Teams can contain players and managers.
- Team managers and club owners do not have the same scope of access, which keeps ownership and day-to-day management separated.
- Users can search for clubs, request to join them, and review join requests when they have permission.

### Ladders

- Ladders belong to clubs and define the competition structure.
- A ladder decides which teams participate, which ruleset is used, and how rankings are calculated.
- Teams can be added to a ladder when they qualify for that competition.
- Ladder standings are updated automatically after matches are finalized.

### Match Flow

- Match proposals are created between eligible teams.
- The proposal is then accepted or rejected by the invited side.
- After the match is played, both sides can submit a score.
- If both submissions match, the result is finalized automatically.
- If the submissions differ, the match becomes disputed.
- Club owners or administrators can resolve disputed matches when they have the right permissions.
- Final results update the ladder ranking automatically.

### Rulesets

- Rulesets store the match rules that a ladder uses.
- They define things like match format, third-set handling, deuce rules, and game format.
- The same ruleset can be reused across multiple ladders so the competition rules stay consistent.

### Player Dashboard

- Users can edit profile details and password.
- Users can manage availability blocks.
- Users can see notifications and account-specific actions from one place.
- The dashboard gives a single view of the clubs and teams the account is connected to.
