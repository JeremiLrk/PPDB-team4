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

NetRank follows a simple flow: people join, clubs organize them, teams compete, ladders track results, and disputed matches get resolved when needed. The short version is below; the deeper system notes live in [doc/README.md](doc/README.md).

```text
Account
|-- Player
|-- TeamManager
|   |-- ClubOwner
|-- Administrator

Club
|-- Teams
|-- Ladders
|   |-- Rulesets
|   |-- Match proposals
|   |-- Score submissions
|   |-- Disputed matches
```

### Accounts And Access

Every user starts as an `Account`. From there the app separates people into roles so each part of the system stays in the right hands: `Player` for match activity, `TeamManager` for team administration, `ClubOwner` for club-level control, and `Administrator` for broader moderation and dispute handling.

Signing up sends a verification email. Logging in stores the access token in an HTTP-only cookie. If someone forgets their password, they can request a reset link by email. Users can also update profile details and change their password from the dashboard.

### Dashboard

The dashboard is the main workspace after login. It collects the account, club, team, availability, and match tools in one place. See [doc/dashboard.md](doc/dashboard.md) for the page-level overview.

### Clubs And Teams

Clubs are the main organizing unit in the app, and teams are the groups that compete inside them or on their own. See [doc/club-page.md](doc/club-page.md) for the club home page and [doc/club-settings.md](doc/club-settings.md) for club management.

### Ladders, Matches, And Rules

Ladders belong to clubs and define how competition works. They decide which teams take part, which ruleset is used, and how rankings are calculated. When matches are completed, ladder standings update automatically.

Match play follows a clear path. Teams can be matched in two ways: an authorized club owner, team manager, or administrator can create a manual proposal for a valid team pair, or the weekly generator can create proposals from ladder order and player availability. The invited side accepts or rejects the proposal, and both sides can submit scores once the match is played. If the scores match, the result finalizes automatically. If they do not match, the match moves to a disputed state. Authorized club staff can then review the dispute and resolve it, after which the ladder rankings update again.

Rulesets keep the match rules consistent. They store the format of the match, third-set handling, deuce rules, and other game settings. The same ruleset can be reused across several ladders.

### Themes, Availability, And Email

The dashboard and club pages support light and dark themes. Availability blocks are used by the weekly match proposal system to find good match times, so the availability calendar is part of match planning rather than a separate calendar feature. Club creation uses city lookup, and match proposal cards can show weather for the proposed time and place.

Email support is built into the key flows. NetRank sends signup verification emails, password reset emails, and club activity emails such as join request notifications and join request decisions. The app also uses email links to send people back into the right part of the site, such as a club page or the dashboard.

### Deep Dives

- [doc/README.md](doc/README.md) for the feature map and detailed explanations.
- [doc/matches.md](doc/matches.md) for match proposals, score submission, disputes, and ladder ranking updates.
- [doc/ladders-and-elo.md](doc/ladders-and-elo.md) for how ladder rankings and Elo work.
- [doc/availability.md](doc/availability.md) for the availability calendar and weekly proposal generation.
- [doc/clubs-and-teams.md](doc/clubs-and-teams.md) for club, team, and membership management.
- [doc/auth.md](doc/auth.md) for signup, login, email verification, and password reset.
- [doc/dashboard.md](doc/dashboard.md) for the dashboard workspace.
- [doc/club-page.md](doc/club-page.md) for the club home page.
- [doc/club-settings.md](doc/club-settings.md) for the club settings pages.
