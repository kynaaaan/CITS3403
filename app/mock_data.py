"""
Mock data for the RateFoodPerth frontend.

These lists mirror what the SQLAlchemy models will eventually return.
Dict keys are the future column names, when the DB lands the swap
in each route is one line:

restaurants = RESTAURANTS                  
restaurants = Restaurant.query.all()       

and Jinja templates don't change at all (dot-access works on dicts and
ORM objects alike).
"""

USERS = [
    {
        "id": 1,
        "username": "PerthFoodie99",
        "initials": "PF",
        "avatar_color": "#ff7e5f",
        "writing_xp": 340,
        "accuracy_xp": 120,
        "explorer_xp": 300,
        "streak_count": 14,
    },
    {
        "id": 2,
        "username": "TasteExplorer",
        "initials": "TE",
        "avatar_color": "#0d6efd",
        "writing_xp": 600,
        "accuracy_xp": 400,
        "explorer_xp": 240,
        "streak_count": 7,
    },
    {
        "id": 3,
        "username": "noodlequeen_",
        "initials": "NQ",
        "avatar_color": "#20c997",
        "writing_xp": 500,
        "accuracy_xp": 270,
        "explorer_xp": 100,
        "streak_count": 3,
    },
    {
        "id": 4,
        "username": "SuburbScout42",
        "initials": "SS",
        "avatar_color": "#6f42c1",
        "writing_xp": 280,
        "accuracy_xp": 200,
        "explorer_xp": 500,
        "streak_count": 9,
    },
    {
        "id": 5,
        "username": "forkandfilm",
        "initials": "FF",
        "avatar_color": "#d63384",
        "writing_xp": 420,
        "accuracy_xp": 180,
        "explorer_xp": 100,
        "streak_count": 2,
    },
]

RESTAURANTS = [
    {
        "id": 1,
        "name": "Lalla Rookh",
        "suburb": "cbd",
        "cuisine_tags": ["modern-australian", "italian"],
        "price_range": 3,
        "avg_rating": 4.8,
        "review_count": 42,
    },
    {
        "id": 2,
        "name": "Brika",
        "suburb": "northbridge",
        "cuisine_tags": ["modern-australian"],
        "price_range": 2,
        "avg_rating": 4.5,
        "review_count": 28,
    },
    {
        "id": 3,
        "name": "Bread in Common",
        "suburb": "fremantle",
        "cuisine_tags": ["modern-australian"],
        "price_range": 2,
        "avg_rating": 4.5,
        "review_count": 35,
    },
    {
        "id": 4,
        "name": "Rockpool Bar & Grill",
        "suburb": "cbd",
        "cuisine_tags": ["modern-australian"],
        "price_range": 3,
        "avg_rating": 5.0,
        "review_count": 56,
    },
    {
        "id": 5,
        "name": "Fuku",
        "suburb": "northbridge",
        "cuisine_tags": ["japanese"],
        "price_range": 2,
        "avg_rating": 5.0,
        "review_count": 31,
    },
    {
        "id": 6,
        "name": "Long Chim",
        "suburb": "cbd",
        "cuisine_tags": ["thai"],
        "price_range": 2,
        "avg_rating": 4.0,
        "review_count": 48,
    },
    {
        "id": 7,
        "name": "Mary Street Bakery",
        "suburb": "leederville",
        "cuisine_tags": ["cafe"],
        "price_range": 1,
        "avg_rating": 4.0,
        "review_count": 62,
    },
    {
        "id": 8,
        "name": "Pleased to Meet You",
        "suburb": "northbridge",
        "cuisine_tags": ["italian"],
        "price_range": 2,
        "avg_rating": 4.0,
        "review_count": 19,
    },
    {
        "id": 9,
        "name": "Bib & Tucker",
        "suburb": "fremantle",
        "cuisine_tags": ["seafood"],
        "price_range": 3,
        "avg_rating": 4.5,
        "review_count": 27,
    },
    {
        "id": 10,
        "name": "Lucky Chan's",
        "suburb": "northbridge",
        "cuisine_tags": ["chinese"],
        "price_range": 1,
        "avg_rating": 3.5,
        "review_count": 15,
    },
]


REVIEWS = [
    {
        "id": 1,
        "user_id": 1,            # PerthFoodie99
        "restaurant_id": 1,      # Lalla Rookh
        "star_rating": 5,
        "body": (
            "The slow-roasted lamb shoulder has been on my radar for ages and it "
            "absolutely delivered. Perfectly tender with a rich jus, paired beautifully "
            "with an excellent WA Shiraz from the cellar list. If you haven't visited "
            "Lalla Rookh, you're missing the best of Perth's CBD dining scene."
        ),
        "craving_tags": ["hearty", "classy"],
        "price_paid": 78,
        "created_at": "2 hours ago",
        "likes": {"accuracy": 14, "writing": 9, "breadth": 6},
    },
    {
        "id": 2,
        "user_id": 2,            # TasteExplorer
        "restaurant_id": 1,      # Lalla Rookh
        "star_rating": 4,
        "body": (
            "Atmosphere is impeccable — warm lighting, exposed brick, that kind of "
            "place where everything just feels considered. We shared the burrata and "
            "the pappardelle with oxtail ragu. The pasta was the standout. My only "
            "gripe: service ran slow at peak hour, so book early if you're in a rush."
        ),
        "craving_tags": ["wine", "date-night"],
        "price_paid": 110,
        "created_at": "1 day ago",
        "likes": {"accuracy": 22, "writing": 18, "breadth": 11},
    },
    {
        "id": 3,
        "user_id": 3,            # noodlequeen_
        "restaurant_id": 1,      # Lalla Rookh
        "star_rating": 5,
        "body": (
            "The nduja rigatoni is genuinely one of the best pasta dishes I've had "
            "in Perth. Rich, spicy, just the right amount of char on the sausage. "
            "Finished with the tiramisu — classic, boozy, no surprises, just done "
            "really well. I'll be back."
        ),
        "craving_tags": ["indulgent", "spicy"],
        "price_paid": 65,
        "created_at": "3 days ago",
        "likes": {"accuracy": 8, "writing": 12, "breadth": 4},
    },
    {
        "id": 4,
        "user_id": 4,            # SuburbScout42
        "restaurant_id": 1,      # Lalla Rookh
        "star_rating": 4,
        "body": (
            "Good food, great wine list, but prices have crept up noticeably in the "
            "last year. Mains now sitting at $40–50 territory. Still worth it for a "
            "special occasion but I wouldn't make this a weeknight regular anymore."
        ),
        "craving_tags": ["classy", "pricey"],
        "price_paid": 95,
        "created_at": "1 week ago",
        "likes": {"accuracy": 31, "writing": 7, "breadth": 15},
    },
    {
        "id": 5,
        "user_id": 1,            # PerthFoodie99
        "restaurant_id": 7,      # Mary Street Bakery
        "star_rating": 4,
        "body": (
            "Best brekkie in Leederville. The beef brisket bagel is huge and the "
            "coffee is consistently great. Gets packed by 9am on weekends, so come "
            "early or be prepared to queue down the street."
        ),
        "craving_tags": ["hearty", "cheap"],
        "price_paid": 22,
        "created_at": "5 days ago",
        "likes": {"accuracy": 19, "writing": 6, "breadth": 8},
    },
    {
        "id": 6,
        "user_id": 3,            # noodlequeen_
        "restaurant_id": 5,      # Fuku
        "star_rating": 5,
        "body": (
            "Omakase at Fuku is the best sushi experience in Perth, full stop. The "
            "chef's selection was generous and the toro was unreal. Pricey but worth "
            "it for a special occasion."
        ),
        "craving_tags": ["indulgent", "date-night"],
        "price_paid": 145,
        "created_at": "4 days ago",
        "likes": {"accuracy": 27, "writing": 14, "breadth": 9},
    },
]


# Slug -> human-readable label mappings, used in templates so we don't have
# to deal with title-casing slugs like "modern-australian" inline.
# Exposed to all templates via the context_processor in app/__init__.py.

SUBURB_DISPLAY = {
    "cbd": "CBD",
    "northbridge": "Northbridge",
    "fremantle": "Fremantle",
    "subiaco": "Subiaco",
    "leederville": "Leederville",
    "cottesloe": "Cottesloe",
}

CUISINE_DISPLAY = {
    "modern-australian": "Modern Australian",
    "italian": "Italian",
    "japanese": "Japanese",
    "chinese": "Chinese",
    "thai": "Thai",
    "indian": "Indian",
    "cafe": "Cafe",
    "seafood": "Seafood",
}

PRICE_DISPLAY = {
    "1": "$",
    "2": "$$",
    "3": "$$$"
}


def user_by_id(user_id):
    """Return the user dict matching user_id, or None if not found."""
    return next((u for u in USERS if u["id"] == user_id), None)


def restaurant_by_id(restaurant_id):
    """Return the restaurant dict matching restaurant_id, or None if not found."""
    return next((r for r in RESTAURANTS if r["id"] == restaurant_id), None)


def user_by_username(username):
    """Return the user dict matching username (case-insensitive), or None."""
    return next((u for u in USERS if u["username"].lower() == username.lower()), None)


def enrich_review(review):
    """
    Pre-join review -> user and review -> restaurant so templates can do:

        {{ review.user.username }}
        {{ review.restaurant.name }}

    Returns a new dict; does not mutate the original.
    """
    return {
        **review,
        "user": user_by_id(review["user_id"]),
        "restaurant": restaurant_by_id(review["restaurant_id"]),
    }
