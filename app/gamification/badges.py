"""
Badge identity (BadgeType enum) and display metadata.

Single source of truth for which badges exist, their human-readable labels,
icons, colour classes, descriptions, and threshold blurbs. Used by:
  - app.models.Badge (database column type)
  - app.gamification.logic.check_and_award_badges (award rules)
  - the profile page (earned/locked grid)
  - any future "How XP works" page or leaderboard widget

Keeping the enum here rather than in app.models avoids the awkward arrangement
where gamification code had to reach back into the data layer for its own
domain constants. The award thresholds in `threshold` mirror the numbers
hard-coded in check_and_award_badges in human-readable form.
"""

import enum


class BadgeType(enum.Enum):
    """Badge identifiers persisted on Badge.badge_type."""
    FIRST_BITE = "first_bite"                  # First review posted
    SUBURB_SCOUT = "suburb_scout"              # 5+ distinct suburbs reviewed
    GLOBE_TROTTER = "globe_trotter"            # 6+ distinct cuisines reviewed
    ON_FIRE = "on_fire"                        # 7-day streak
    PEN_AND_FORK = "pen_and_fork"              # Level 5 Writing XP (400 XP)
    RUTHLESSLY_ACCURATE = "ruthlessly_accurate"  # 50 accuracy likes received


BADGES = {
    BadgeType.FIRST_BITE: {
        "label": "First Bite",
        "icon": "bi-award-fill",
        "colour_class": "text-warning",
        "description": "Post your first review.",
        "threshold": "1 review",
    },
    BadgeType.PEN_AND_FORK: {
        "label": "Pen & Fork",
        "icon": "bi-pencil-fill",
        "colour_class": "text-primary",
        "description": "Reach Level 5 Writing XP.",
        "threshold": "400 Writing XP",
    },
    BadgeType.SUBURB_SCOUT: {
        "label": "Suburb Scout",
        "icon": "bi-geo-alt-fill",
        "colour_class": "text-success",
        "description": "Review in 5 different suburbs.",
        "threshold": "5 suburbs",
    },
    BadgeType.ON_FIRE: {
        "label": "On Fire",
        "icon": "bi-fire",
        "colour_class": "text-danger",
        "description": "Maintain a 7-day review streak.",
        "threshold": "7-day streak",
    },
    BadgeType.RUTHLESSLY_ACCURATE: {
        "label": "Ruthlessly Accurate",
        "icon": "bi-check-circle-fill",
        "colour_class": "text-info",
        "description": "Receive 50 accuracy likes across your reviews.",
        "threshold": "50 accuracy likes",
    },
    BadgeType.GLOBE_TROTTER: {
        "label": "Globe Trotter",
        "icon": "bi-globe2",
        "colour_class": "text-primary",
        "description": "Review 6 different cuisines.",
        "threshold": "6 cuisines",
    },
}

# Display order for the profile grid — keep the easier-to-earn ones first so
# new users see their progress fill in left-to-right.
BADGE_ORDER = [
    BadgeType.FIRST_BITE,
    BadgeType.PEN_AND_FORK,
    BadgeType.SUBURB_SCOUT,
    BadgeType.ON_FIRE,
    BadgeType.RUTHLESSLY_ACCURATE,
    BadgeType.GLOBE_TROTTER,
]


def badge_cards_for(earned_badges):
    """
    Build the view-model list the profile template iterates over.

    earned_badges: iterable of Badge ORM rows (the user's awarded badges).
    Returns a list of dicts in BADGE_ORDER, each with the registry fields plus
    `earned: bool`.
    """
    earned_types = {b.badge_type for b in earned_badges}
    cards = []
    for badge_type in BADGE_ORDER:
        meta = BADGES[badge_type]
        cards.append({
            "label": meta["label"],
            "icon": meta["icon"],
            "colour_class": meta["colour_class"],
            "description": meta["description"],
            "threshold": meta["threshold"],
            "earned": badge_type in earned_types,
        })
    return cards
