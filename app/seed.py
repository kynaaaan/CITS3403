"""
Seed the database from app.mock_data.

Philosophy: seed RAW facts only; users, restaurants, reviews, likes,
follows. Derived state (XP totals, streak counts, badges) is intentionally
left at zero/empty so the same gamification logic that runs in live routes
populates it.

Run with:
    flask --app run seed             # idempotent, bails if already seeded
    flask --app run seed --reset     # drop, recreate, reseed
"""
import re
from datetime import datetime, timedelta, timezone

import click
from flask.cli import with_appcontext

from app import db
from app.mock_data import RESTAURANTS, REVIEWS, USERS
from app.models import (
    Follow,
    LikeDimension,
    Restaurant,
    Review,
    ReviewLike,
    User,
)

DEFAULT_PASSWORD = "password"
RESTAURANT_OWNER_ID = 1

_RELATIVE_TIME_RE = re.compile(r"^(\d+)\s+(\w+?)s?\s+ago$", re.IGNORECASE)
_UNIT_TO_KW = {
    "minute": "minutes",
    "hour": "hours",
    "day": "days",
    "week": "weeks",
}


def _parse_relative_time(value):
    """Convert "2 hours ago" → tz-aware datetime; pass datetimes through."""
    if isinstance(value, datetime):
        return value
    now = datetime.now(timezone.utc)
    if not isinstance(value, str):
        return now
    m = _RELATIVE_TIME_RE.match(value.strip())
    if not m:
        return now
    n, unit = int(m.group(1)), m.group(2).lower()
    kwarg = _UNIT_TO_KW.get(unit)
    if not kwarg:
        return now
    return now - timedelta(**{kwarg: n})


def _seed_users():
    for u in USERS:
        user = User(
            id=u["id"],
            username=u["username"],
            email=f"{u['username'].lower()}@example.com",
        )
        user.set_password(DEFAULT_PASSWORD)
        db.session.add(user)
    db.session.flush()


def _seed_restaurants():
    for r in RESTAURANTS:
        db.session.add(Restaurant(
            id=r["id"],
            name=r["name"],
            suburb=r["suburb"],
            cuisine_tags=r["cuisine_tags"],
            price_range=r["price_range"],
            created_by=RESTAURANT_OWNER_ID,
        ))
    db.session.flush()


def _seed_reviews_and_likes():
    user_ids = [u["id"] for u in USERS]
    likes_total = 0

    for r in REVIEWS:
        review = Review(
            id=r["id"],
            user_id=r["user_id"],
            restaurant_id=r["restaurant_id"],
            star_rating=r["star_rating"],
            body=r["body"],
            craving_tags=r["craving_tags"],
            price_paid=r.get("price_paid"),
            created_at=_parse_relative_time(r["created_at"]),
        )
        db.session.add(review)
        db.session.flush()

        eligible = [uid for uid in user_ids if uid != r["user_id"]]
        for dim_str, count in r.get("like_counts", {}).items():
            try:
                dim = LikeDimension(dim_str)
            except ValueError:
                continue
            for i in range(min(count, len(eligible))):
                db.session.add(ReviewLike(
                    user_id=eligible[i],
                    review_id=review.id,
                    dimension=dim,
                ))
                likes_total += 1

    return likes_total


def _seed_follows():
    """User 1 follows everyone else, so the Following feed has content."""
    follows = 0
    for u in USERS:
        if u["id"] == 1:
            continue
        db.session.add(Follow(follower_id=1, followed_id=u["id"]))
        follows += 1
    return follows


def seed_database(reset=False):
    if reset:
        db.drop_all()
        db.create_all()
    elif User.query.first():
        click.echo("Database already seeded — pass --reset to wipe and re-seed.")
        return

    _seed_users()
    _seed_restaurants()
    likes_total = _seed_reviews_and_likes()
    follows_total = _seed_follows()

    db.session.commit()
    click.echo(
        f"Seeded {len(USERS)} users, {len(RESTAURANTS)} restaurants, "
        f"{len(REVIEWS)} reviews, {likes_total} review_likes, "
        f"{follows_total} follows."
    )


@click.command("seed")
@click.option("--reset", is_flag=True,
              help="Drop all tables and recreate them before seeding.")
@with_appcontext
def seed_command(reset):
    """Populate the database with raw-fact mock data."""
    seed_database(reset=reset)
