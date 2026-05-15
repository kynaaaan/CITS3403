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
import random
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

_SYNTHETIC_BODIES = [
    "Solid spot — happy I tried it. Would come back for the mains.",
    "Service was a touch slow at peak hour but the food held up.",
    "Great atmosphere, generous portions. Pricing felt fair for what you get.",
    "Came on a Tuesday — quiet, relaxed, plates landed quickly. Recommended.",
    "Mixed feelings — entrees were excellent, mains a bit under-seasoned.",
    "Genuinely one of the better meals I've had in this suburb lately.",
    "Cocktails were strong, food was decent. Better for drinks than a sit-down.",
    "Not the cheapest, but the quality is there. Save it for a special occasion.",
    "Coffee was great and the brunch menu has nice options. Will be back.",
    "Overhyped, honestly — fine but nothing to write home about.",
    "Loved the vibe. Brought friends from interstate and they were impressed.",
    "Small menu but everything they do, they do well.",
]
_ALL_CRAVING_TAGS = [
    "hearty", "classy", "spicy", "sweet", "cheap", "healthy",
    "indulgent", "wine", "cocktails", "pricey", "date-night",
]

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


def _seed_synthetic_reviews(target_per_restaurant=8):
    rng = random.Random(42)
    user_ids = [u["id"] for u in USERS]
    now = datetime.now(timezone.utc)

    added = 0
    likes_added = 0
    for restaurant in Restaurant.query.all():
        existing = len(restaurant.reviews)
        needed = max(0, target_per_restaurant - existing)
        for _ in range(needed):
            review = Review(
                user_id=rng.choice(user_ids),
                restaurant_id=restaurant.id,
                star_rating=rng.choices([2, 3, 4, 5], weights=[1, 3, 6, 5])[0],
                body=rng.choice(_SYNTHETIC_BODIES),
                craving_tags=rng.sample(_ALL_CRAVING_TAGS, k=rng.randint(1, 3)),
                price_paid=rng.choice([None, 18, 28, 42, 60, 95]),
                created_at=now - timedelta(
                    days=rng.randint(0, 28),
                    hours=rng.randint(0, 23),
                    minutes=rng.randint(0, 59),
                ),
            )
            db.session.add(review)
            db.session.flush()
            added += 1

            # Sprinkle a few likes per review for non-empty like counters.
            eligible = [uid for uid in user_ids if uid != review.user_id]
            for dim in LikeDimension:
                count = rng.randint(0, 4)
                for liker in rng.sample(eligible, k=min(count, len(eligible))):
                    db.session.add(ReviewLike(
                        user_id=liker, review_id=review.id, dimension=dim,
                    ))
                    likes_added += 1
    return added, likes_added


def _seed_follows():
    # User 1 follows everyone (gives the Following feed broad content).
    pairs = {(1, u["id"]) for u in USERS if u["id"] != 1}
    # Plus a few cross-edges so non-user-1 accounts also have a follow graph.
    pairs |= {(2, 3), (2, 5), (3, 1), (3, 4), (4, 2), (5, 1), (5, 3)}

    for follower_id, followed_id in pairs:
        db.session.add(Follow(follower_id=follower_id, followed_id=followed_id))
    return len(pairs)


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
    synthetic_reviews, synthetic_likes = _seed_synthetic_reviews()
    follows_total = _seed_follows()

    from app.gamification.logic import recompute_user_state
    for u in User.query.all():
        recompute_user_state(u)

    db.session.commit()

    from app.models import Badge
    click.echo(
        f"Seeded {len(USERS)} users, {len(RESTAURANTS)} restaurants, "
        f"{len(REVIEWS) + synthetic_reviews} reviews "
        f"({synthetic_reviews} synthetic), "
        f"{likes_total + synthetic_likes} review_likes, "
        f"{follows_total} follows, {Badge.query.count()} badges."
    )


@click.command("seed")
@click.option("--reset", is_flag=True,
              help="Drop all tables and recreate them before seeding.")
@with_appcontext
def seed_command(reset):
    """Populate the database with raw-fact mock data."""
    seed_database(reset=reset)
