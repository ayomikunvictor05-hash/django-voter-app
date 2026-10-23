# VoterApp

A secure, schedule-driven voting platform built with Python and Django. VoterApp supports elections for academic institutions, corporations, and private organizations, offering configurable eligibility rules, time-bound polls, real-time result visualization, and verifiable, anonymized vote receipts.

---

## Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [System Flow](#system-flow)
- [Getting Started](#getting-started)
- [Security Considerations](#security-considerations)
- [Contributing](#contributing)

---

## Features

### Access Control and Eligibility

- **Email domain whitelisting:** Select from common email providers or define custom institutional and corporate domains (for example, `university.edu` or `company.com`).
- **Target voter groups:** Restrict a poll to specific departments, cohorts, or organizational roles.
- **Secondary passcode:** Optionally require a passphrase before the ballot is displayed.
- **Masked ballot routing:** A session-token lookup keeps raw voting codes out of public URL paths (`/vote/ballot/`).

### Scheduling and Lifecycle

- **Time-window enforcement:** Each poll has an explicit `start_time` and `end_time`. Ballots remain locked until launch and close automatically on schedule.
- **Creator participation:** Poll creators may vote in their own polls, subject to the same eligibility and anti-fraud checks as every other voter.

### Ballot Customization

- **Option images:** Attach an optional image to each choice, suited to candidate profiles or showcase items.
- **Automatic QR codes:** A QR code is generated for every new poll to enable quick access from mobile devices.

### Analytics and Verification

- **Interactive charts:** Responsive vote-progress charts rendered with Chart.js.
- **Configurable result visibility:** Creators can display live tallies or hide results until the election closes.
- **Anonymized vote receipts:** Every cast vote produces a unique receipt token (for example, `VOTE-8F3A-99B2`). Voters can use it to confirm their vote was recorded without revealing their choice.
- **Double-vote prevention:** Database-level unique constraints prevent duplicate votes, including under concurrent requests.

---

## Tech Stack

| Layer              | Technologies                                                  |
| :----------------- | :------------------------------------------------------------ |
| Core framework     | Python 3.10+, Django 4.x / 5.x                                |
| Database           | SQLite (development), PostgreSQL-ready                        |
| Frontend           | HTML5, CSS3, Bootstrap 5, Bootstrap Icons                     |
| Data visualization | Chart.js                                                      |
| Media and security | Pillow (image processing), `qrcode` (QR generation), `secrets` (token generation) |

---

## System Flow

```text
[ User Sign Up / Sign In ]
            |
            +--> [ Create Voting Avenue ]
            |      Set dates, domains, groups, passcode, options and images
            |            |
            |            v
            |      [ QR Code and Poll Code Generation ]
            |            |
            +--> [ Search by Code / Scan QR ] <---+
                         |
                         v
              [ Eligibility and Time Gate ]
                1. Active schedule check (start_time <= now <= end_time)
                2. Email domain match
                3. Voter group match
                4. Passcode verification
                         |
                         v
                [ Cast Ballot ]
                  Unique constraint check and IP logging
                         |
                         v
                [ Vote Receipt Issued ]
                  Format: VOTE-XXXX-XXXX
                         |
                         v
                [ Live Analytics Dashboard ]
                  Chart.js visualization
```

---

## Getting Started

### Prerequisites

- Python 3.10 or higher
- pip
- Git

### Installation

Clone the repository, open a terminal in the project folder (the one containing `manage.py`), and run:

```bash
# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate        # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Apply database migrations
python manage.py migrate

# Create an administrator account
python manage.py createsuperuser

# Start the development server
python manage.py runserver
```

The application will be available at `http://127.0.0.1:8000/`.

---

## Security Considerations

- Vote receipts are generated with Python's `secrets` module and do not reveal ballot choices.
- Double voting is prevented at the database level through unique constraints.
- Ballot access uses session tokens, so raw voting codes do not appear in public URLs.
- For production deployments, set `DEBUG = False`, configure `ALLOWED_HOSTS`, store `SECRET_KEY` in an environment variable, and serve the application over HTTPS.

---

## Contributing

Contributions are welcome. To propose a change:

1. Fork the repository.
2. Create a feature branch: `git checkout -b feature/your-feature-name`.
3. Commit your changes with clear messages.
4. Push the branch and open a pull request describing the change.
