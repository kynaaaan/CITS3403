# RateFoodPerth

A gamified food review web app for Perth. Users review restaurants,
earn XP across three dimensions (Writing, Accuracy, Explorer), keep a
review streak, collect badges and follow other reviewers.

Built for CITS3403

---

## Quick start

### macOS / Linux

```bash
git clone "https://github.com/kynaaaan/CITS3403.git" CITS3403
cd CITS3403
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env                      # then edit if you like
flask --app run db upgrade                # creates app.db from migrations
flask --app run seed                      # loads mock users/restaurants/reviews
flask --app run run --debug               
```

### Windows (PowerShell)

```powershell
# one-time
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned

git clone <repo-url> CITS3403
cd CITS3403
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
flask --app run db upgrade
flask --app run seed
flask --app run run --debug
```

Default seed credentials: `perthfoodie99@example.com` / `password` and
similar for the other seeded usernames.

---

## Configuration

Two configs in [config.py](config.py):

- **`Config`**: development defaults. `SECRET_KEY` and `DATABASE_URL`
  fall back to safe local values so the app boots without a `.env`.
- **`ProductionConfig`**: no defaults. Refuses to start if `SECRET_KEY`
  or `DATABASE_URL` is unset.

`create_app()` picks `ProductionConfig` iff `FLASK_CONFIG=production`.

---

## Common commands

```bash
flask --app run run --debug              # dev server, auto-reload
flask --app run seed                     # seed mock data (idempotent)
flask --app run seed --reset             # wipe and reseed

flask --app run db migrate -m "msg"      # generate a new migration
flask --app run db upgrade               # apply migrations

python -m unittest discover tests        # unit + integration tests
python -m unittest tests.test_selenium   # selenium tests (needs chromedriver)
```

---

## Project layout

```
app/
  __init__.py           Flask app factory
  models.py             SQLAlchemy models (User, Restaurant, Review, Follow, Badge, ...)
  seed.py               `flask seed` CLI command
  mock_data.py          Seed data + slug/display mappings
  auth/                 Login, register, logout
  main/                 Home feed (/) + Discover (/search)
  reviews/              Write review, like (AJAX)
  restaurants/          Restaurant detail page + add restaurant
  social/               Profile, follow/unfollow, account dashboard
  gamification/         BadgeType enum, XP/streak/badge logic, leaderboard
  static/               CSS, JS, images
  templates/            Jinja2 templates (one folder per blueprint)

migrations/             Alembic revisions
tests/                  unittest + Selenium tests
config.py               Dev + Production configs
run.py                  Entry point (`flask --app run`)
```

---

## Team

CITS3403 group project (3 members), Semester 1 2026.

## License

See [LICENSE](LICENSE).
