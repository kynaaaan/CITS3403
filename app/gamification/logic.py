from app.models import LikeDimension, User

WRITING_XP_PER_LIKE       = 10
WRITING_XP_PER_REVIEW     = 5
ACCURACY_XP_PER_LIKE      = 10
EXPLORER_XP_PER_LIKE      = 10
EXPLORER_XP_PER_REVIEW    = 5
EXPLORER_XP_PER_NEW_SUBURB  = 25
EXPLORER_XP_PER_NEW_CUISINE = 25
STREAK_BREAK_HOURS        = 48
XP_PER_LEVEL              = 100 

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



def compute_recompute_streak(user: User):
    """ 
    Reads user reviews ordered by created_at, computes review streak.
    """
    pass

def check_and_award_badges(user: User):
    """
    Checks badge conditions, adds badges to user if they qualify and dont already have them.
    """
    pass

def recompute_user_state(user: User):
    """
    Calls all functions: compute_recompute_xp, compute_recompute_streak, check_and_award_badges.
    """
    pass