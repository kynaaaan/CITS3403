from app.models import LikeDimension, User, BadgeType, Badge
from datetime import datetime, timezone, timedelta

WRITING_XP_PER_LIKE       = 10
WRITING_XP_PER_REVIEW     = 5
ACCURACY_XP_PER_LIKE      = 10
EXPLORER_XP_PER_LIKE      = 10
EXPLORER_XP_PER_REVIEW    = 5
EXPLORER_XP_PER_NEW_SUBURB  = 25
EXPLORER_XP_PER_NEW_CUISINE = 25
STREAK_BREAK_HOURS        = 48
XP_PER_LEVEL              = 100


def level_for_xp(xp):
    """
    Map a raw XP value to (level, progress, xp_to_next).
    """
    level = xp // XP_PER_LEVEL + 1
    progress = xp % XP_PER_LEVEL
    xp_to_next = XP_PER_LEVEL - progress
    return level, progress, xp_to_next

def _likes_received_by_dim(user: User):
    """Total likes the user's reviews have received, grouped by dimension."""
    counts = {
        LikeDimension.WRITING: 0,
        LikeDimension.ACCURACY: 0,
        LikeDimension.BREADTH: 0,
    }
    for review in user.reviews:
        for like in review.likes:
            counts[like.dimension] += 1
    return counts


def _unique_suburbs_reviewed(user: User):
    """Distinct suburbs the user has reviewed at."""
    return len({r.restaurant.suburb for r in user.reviews})


def _unique_cuisines_reviewed(user: User):
    """Distinct cuisine tags across every restaurant the user has reviewed."""
    return len({
        tag for r in user.reviews for tag in (r.restaurant.cuisine_tags or [])
    })


def _calc_writing_xp(n_reviews, writing_likes):
    """
    Formula: WRITING_XP_PER_REVIEW * n_reviews + WRITING_XP_PER_LIKE * writing_likes
    """
    return WRITING_XP_PER_REVIEW * n_reviews + WRITING_XP_PER_LIKE * writing_likes


def _calc_accuracy_xp(accuracy_likes):
    """
    Formula: ACCURACY_XP_PER_LIKE * accuracy_likes
    """
    return ACCURACY_XP_PER_LIKE * accuracy_likes


def _calc_explorer_xp(n_reviews, breadth_likes, unique_suburbs, unique_cuisines):
    """
    Formula: EXPLORER_XP_PER_REVIEW * n_reviews + EXPLORER_XP_PER_LIKE * breadth_likes +
    EXPLORER_XP_PER_NEW_SUBURB * unique_suburbs + EXPLORER_XP_PER_NEW_CUISINE * unique_cuisines
    """
    return (
        EXPLORER_XP_PER_REVIEW * n_reviews
        + EXPLORER_XP_PER_LIKE * breadth_likes
        + EXPLORER_XP_PER_NEW_SUBURB * unique_suburbs
        + EXPLORER_XP_PER_NEW_CUISINE * unique_cuisines
    )


def compute_recompute_xp(user: User):
    """
    Reads user reviews and their likes, overwrites the three XP fields.
    Idempotent — calling twice yields the same state.
    """
    n_reviews = len(user.reviews)
    likes = _likes_received_by_dim(user)

    user.writing_xp = _calc_writing_xp(n_reviews, likes[LikeDimension.WRITING])
    user.accuracy_xp = _calc_accuracy_xp(likes[LikeDimension.ACCURACY])
    user.explorer_xp = _calc_explorer_xp(
        n_reviews,
        likes[LikeDimension.BREADTH],
        _unique_suburbs_reviewed(user),
        _unique_cuisines_reviewed(user),
    )


def _as_aware(dt):
    """SQLite strips tzinfo on read but freshly flushed rows keep it in
    memory. Normalise to UTC aware so sort/compare works either side of
    that boundary."""
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def compute_recompute_streak(user: User):
    """
    Reads user reviews ordered by created_at, computes review streak.
    Idempotent — overwrites streak_count and streak_last_review.
    """
    reviews = sorted(user.reviews, key=lambda x: _as_aware(x.created_at), reverse=True)
    if not reviews:
        user.streak_count = 0
        user.streak_last_review = None
        return

    now = datetime.now(timezone.utc)
    last = _as_aware(reviews[0].created_at)
    user.streak_last_review = last

    if (now - last) > timedelta(hours=STREAK_BREAK_HOURS):
        user.streak_count = 0
        return

    days = sorted({r.created_at.date() for r in reviews}, reverse=True)
    streak = 1
    for i in range(1, len(days)):
        if (days[i-1] - days[i]).days == 1:
            streak += 1
        else:
            break

    user.streak_count = streak


def check_and_award_badges(user: User):
    """
    Checks badge conditions, adds badges to user if they qualify and don't
    already have them.

    Depends on writing_xp + streak_count being already populated, so run
    after compute_recompute_xp and compute_recompute_streak.
    """
    already = {b.badge_type for b in user.badges}

    def award(badge_type):
        if badge_type not in already:
            user.badges.append(Badge(badge_type=badge_type))
            already.add(badge_type)

    likes = _likes_received_by_dim(user)

    if len(user.reviews) >= 1:
        award(BadgeType.FIRST_BITE)
    if _unique_suburbs_reviewed(user) >= 5:
        award(BadgeType.SUBURB_SCOUT)
    if _unique_cuisines_reviewed(user) >= 6:
        award(BadgeType.GLOBE_TROTTER)
    if user.streak_count >= 7:
        award(BadgeType.ON_FIRE)
    if user.writing_xp >= 400:
        award(BadgeType.PEN_AND_FORK)
    if likes[LikeDimension.ACCURACY] >= 50:
        award(BadgeType.RUTHLESSLY_ACCURATE)

def recompute_user_state(user: User):
    """
    Caller controls the transaction, no commit here.
    """
    compute_recompute_xp(user)
    compute_recompute_streak(user)
    check_and_award_badges(user)