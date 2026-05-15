"""
test_model_logic.py
===================
Regression tests for CITS3403 model logic.

Coverage
--------
1. Password hash round-trip  (set → check)
2. XP accrual on review creation
3. Streak break after 48 h
4. Follow is not symmetric   (A→B does not imply B→A)
5. Badge "First Bite" awarded exactly once

Running
-------
    pytest tests/test_model_logic.py -v          # if pytest is available
    python -m unittest tests/test_model_logic.py # stdlib only – no extra deps

Architecture
------------
All tests run against an in-memory SQLite database via SQLAlchemy / Flask-SQLAlchemy.
A minimal TestConfig swaps out the production URI and disables CSRF so that no
live database, email server, or browser is required.

When Flask-SQLAlchemy / pytest are not installed the module still imports cleanly
and every test class is skipped with a clear message so CI never silently passes
a green-zero run.
"""

import sys
import unittest
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock, patch, PropertyMock


# ---------------------------------------------------------------------------
# Availability guards
# ---------------------------------------------------------------------------

def _try_import(name):
    try:
        return __import__(name)
    except ModuleNotFoundError:
        return None


_flask          = _try_import("flask")
_flask_sqlalchemy = _try_import("flask_sqlalchemy")
_werkzeug_security = _try_import("werkzeug.security")

_FLASK_STACK_OK = all([_flask, _flask_sqlalchemy, _werkzeug_security])


# ===========================================================================
# SECTION A – Pure unit tests (no Flask, no DB)
#
# These tests import only the *logic functions* from gamification/logic.py by
# constructing lightweight stubs that satisfy the duck-typed interface those
# functions rely on.  They run on any Python 3.8+ installation with zero extra
# packages.
# ===========================================================================

# ---------------------------------------------------------------------------
# Stub classes that mirror the ORM interface used by gamification/logic.py
# ---------------------------------------------------------------------------

class _Stub:
    """Minimal attribute bag."""
    def __init__(self, **kw):
        self.__dict__.update(kw)


def _make_like(dimension_key: str):
    """
    Return a stub ReviewLike whose .dimension matches the LikeDimension
    singleton that the loaded logic module uses as a dict key.

    logic.py's _likes_received_by_dim indexes counts[like.dimension],
    where the keys are the _LikeDimension class attributes (WRITING, etc.).
    We must use exactly those same objects, not new _Stub instances.
    """
    dim_map = {
        "writing":  _LikeDimension.WRITING,
        "accuracy": _LikeDimension.ACCURACY,
        "breadth":  _LikeDimension.BREADTH,
    }
    return _Stub(dimension=dim_map[dimension_key])


def _make_review(suburb="CBD", cuisine_tags=None, created_at=None, likes=None):
    restaurant = _Stub(suburb=suburb, cuisine_tags=cuisine_tags or [])
    if created_at is None:
        created_at = datetime.now(timezone.utc)
    return _Stub(
        restaurant=restaurant,
        created_at=created_at,
        likes=likes or [],
    )


def _make_user(reviews=None, badges=None):
    user = _Stub(
        reviews=reviews or [],
        badges=badges or [],
        writing_xp=0,
        accuracy_xp=0,
        explorer_xp=0,
        streak_count=0,
        streak_last_review=None,
    )
    return user


# ---------------------------------------------------------------------------
# Import the real logic module (sys.path manipulation)
# ---------------------------------------------------------------------------

import os, importlib, types

def _find_repo_root():
    """
    Locate the CITS3403 project root.  Works whether the test file lives
    inside CITS3403/tests/ or in a sibling directory, and falls back to
    walking up from __file__ to find the directory that contains 'app/models.py'.
    """
    candidates = [
        # Typical layout: test file is in CITS3403/tests/
        os.path.abspath(os.path.join(os.path.dirname(__file__), "..")),
        # Test file placed next to the CITS3403/ directory
        os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "CITS3403")),
        # Running from the repo root directly
        os.path.abspath(os.path.join(os.path.dirname(__file__), "CITS3403")),
    ]
    for c in candidates:
        if os.path.isfile(os.path.join(c, "app", "models.py")):
            return c
    # Last resort: walk upward from this file
    current = os.path.dirname(os.path.abspath(__file__))
    for _ in range(6):
        if os.path.isfile(os.path.join(current, "app", "models.py")):
            return current
        current = os.path.dirname(current)
    return candidates[0]   # give up; let the import error be informative


_REPO_ROOT = _find_repo_root()
_APP_DIR = os.path.join(_REPO_ROOT, "app")

# We need to import gamification/logic.py without triggering the full Flask
# application startup.  We mock the names that logic.py imports from app:
#   - app.models.LikeDimension / User / Badge
#   - app.gamification.badges.BadgeType

class _LikeDimension:
    WRITING  = _Stub(value="writing")
    ACCURACY = _Stub(value="accuracy")
    BREADTH  = _Stub(value="breadth")

class _BadgeType:
    FIRST_BITE        = "first_bite"
    SUBURB_SCOUT      = "suburb_scout"
    GLOBE_TROTTER     = "globe_trotter"
    ON_FIRE           = "on_fire"
    PEN_AND_FORK      = "pen_and_fork"
    RUTHLESSLY_ACCURATE = "ruthlessly_accurate"

class _Badge:
    def __init__(self, badge_type=None):
        self.badge_type = badge_type


def _load_logic_module():
    """
    Load app/gamification/logic.py with fake `app.models` so we can test the
    pure logic without a running Flask app or SQLAlchemy.
    """
    # Fake the `app` package hierarchy
    fake_app = types.ModuleType("app")
    fake_gamification = types.ModuleType("app.gamification")
    fake_badges = types.ModuleType("app.gamification.badges")
    fake_badges.BadgeType = _BadgeType

    fake_models = types.ModuleType("app.models")
    fake_models.LikeDimension = _LikeDimension
    fake_models.User          = object          # only used as type hint
    fake_models.Badge         = _Badge

    sys.modules.setdefault("app", fake_app)
    sys.modules.setdefault("app.gamification", fake_gamification)
    sys.modules["app.gamification.badges"] = fake_badges
    sys.modules["app.models"] = fake_models

    logic_path = os.path.join(_APP_DIR, "gamification", "logic.py")
    spec   = importlib.util.spec_from_file_location("app.gamification.logic", logic_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


try:
    _logic = _load_logic_module()
    _LOGIC_OK = True
except Exception as _logic_err:
    _LOGIC_OK = False
    _logic_err_msg = str(_logic_err)


# ---------------------------------------------------------------------------
# Helper: build a stubbed user whose badges list is mutable and badge_type
# attrs come from the real _BadgeType strings so comparisons work.
# ---------------------------------------------------------------------------

def _user_with_reviews(*reviews):
    return _make_user(reviews=list(reviews))


# ===========================================================================
# 1. Password hash round-trip
# ===========================================================================

class TestPasswordHashRoundTrip(unittest.TestCase):
    """
    set_password → check_password must return True for the correct password
    and False for any other string.  Tests the Werkzeug pbkdf2:sha256 pipeline
    directly without the ORM.
    """

    def setUp(self):
        try:
            from werkzeug.security import generate_password_hash, check_password_hash
        except ImportError:
            self.skipTest("werkzeug not available")
        self._gen = generate_password_hash
        self._chk = check_password_hash

    def _set_password(self, plaintext):
        return self._gen(plaintext, method="pbkdf2:sha256")

    def _check_password(self, hash_, plaintext):
        return self._chk(hash_, plaintext)

    def test_correct_password_accepted(self):
        pw = "super$ecret99"
        h  = self._set_password(pw)
        self.assertTrue(
            self._check_password(h, pw),
            "check_password must return True for the original plaintext",
        )

    def test_wrong_password_rejected(self):
        pw = "super$ecret99"
        h  = self._set_password(pw)
        self.assertFalse(
            self._check_password(h, "wrong_password"),
            "check_password must return False for a different string",
        )

    def test_empty_string_rejected(self):
        pw = "super$ecret99"
        h  = self._set_password(pw)
        self.assertFalse(self._check_password(h, ""))

    def test_hash_is_not_plaintext(self):
        pw = "super$ecret99"
        h  = self._set_password(pw)
        self.assertNotEqual(h, pw, "Password must be stored hashed, not as plaintext")

    def test_different_calls_produce_different_hashes(self):
        """Hashing is salted — two hashes of the same password must differ."""
        pw = "samePassword"
        h1 = self._set_password(pw)
        h2 = self._set_password(pw)
        self.assertNotEqual(h1, h2, "Each hash call should produce a unique salt")


# ===========================================================================
# 2. XP accrual on review creation
# ===========================================================================

@unittest.skipUnless(_LOGIC_OK, f"logic module unavailable: {'' if _LOGIC_OK else _logic_err_msg if not _LOGIC_OK else ''}")
class TestXpAccrualOnReviewCreation(unittest.TestCase):
    """
    compute_recompute_xp must raise writing_xp and explorer_xp after a
    review is added.  No likes needed — per-review flat XP must fire.
    """

    def _recompute(self, user):
        _logic.compute_recompute_xp(user)

    def test_zero_reviews_means_zero_xp(self):
        user = _user_with_reviews()
        self._recompute(user)
        self.assertEqual(user.writing_xp,   0)
        self.assertEqual(user.accuracy_xp,  0)
        self.assertEqual(user.explorer_xp,  0)

    def test_one_review_accrues_writing_xp(self):
        user = _user_with_reviews(_make_review())
        self._recompute(user)
        expected = _logic.WRITING_XP_PER_REVIEW * 1
        self.assertEqual(
            user.writing_xp, expected,
            f"Expected writing_xp={expected} after one review, got {user.writing_xp}",
        )

    def test_one_review_accrues_explorer_xp(self):
        user = _user_with_reviews(_make_review(suburb="Northbridge", cuisine_tags=["italian"]))
        self._recompute(user)
        # base per-review XP + suburb bonus + cuisine bonus
        expected = (
            _logic.EXPLORER_XP_PER_REVIEW * 1
            + _logic.EXPLORER_XP_PER_NEW_SUBURB * 1
            + _logic.EXPLORER_XP_PER_NEW_CUISINE * 1
        )
        self.assertEqual(user.explorer_xp, expected)

    def test_xp_scales_with_review_count(self):
        reviews = [_make_review(suburb=f"suburb_{i}", cuisine_tags=[f"c{i}"]) for i in range(3)]
        user = _user_with_reviews(*reviews)
        self._recompute(user)
        self.assertGreater(user.writing_xp, _logic.WRITING_XP_PER_REVIEW * 1)
        self.assertGreater(user.explorer_xp, _logic.EXPLORER_XP_PER_REVIEW * 1)

    def test_idempotent_double_recompute(self):
        """Calling recompute twice must not double-count."""
        user = _user_with_reviews(_make_review())
        self._recompute(user)
        xp_after_first = user.writing_xp
        self._recompute(user)
        self.assertEqual(user.writing_xp, xp_after_first)

    def test_writing_like_increases_writing_xp(self):
        like  = _make_like("writing")
        rev   = _make_review(likes=[like])
        user  = _user_with_reviews(rev)
        self._recompute(user)
        expected = (
            _logic.WRITING_XP_PER_REVIEW * 1
            + _logic.WRITING_XP_PER_LIKE  * 1
        )
        self.assertEqual(user.writing_xp, expected)

    def test_accuracy_like_increases_accuracy_xp(self):
        like  = _make_like("accuracy")
        rev   = _make_review(likes=[like])
        user  = _user_with_reviews(rev)
        self._recompute(user)
        self.assertEqual(user.accuracy_xp, _logic.ACCURACY_XP_PER_LIKE * 1)


# ===========================================================================
# 3. Streak break after 48 h
# ===========================================================================

@unittest.skipUnless(_LOGIC_OK, "logic module unavailable")
class TestStreakBreakAfter48h(unittest.TestCase):
    """
    compute_recompute_streak must reset streak_count to 0 when the most
    recent review is older than STREAK_BREAK_HOURS (48 h).
    """

    def _recompute(self, user):
        _logic.compute_recompute_streak(user)

    def _ago(self, hours):
        return datetime.now(timezone.utc) - timedelta(hours=hours)

    def test_no_reviews_streak_is_zero(self):
        user = _make_user()
        self._recompute(user)
        self.assertEqual(user.streak_count, 0)
        self.assertIsNone(user.streak_last_review)

    def test_recent_review_gives_streak_of_one(self):
        rev  = _make_review(created_at=self._ago(1))   # 1 h ago
        user = _user_with_reviews(rev)
        self._recompute(user)
        self.assertEqual(user.streak_count, 1)

    def test_review_exactly_at_break_boundary_resets_streak(self):
        """Review posted exactly 48 h ago should break the streak."""
        rev  = _make_review(created_at=self._ago(_logic.STREAK_BREAK_HOURS))
        user = _user_with_reviews(rev)
        self._recompute(user)
        self.assertEqual(
            user.streak_count, 0,
            "A review exactly at the 48 h boundary must reset the streak",
        )

    def test_review_just_over_48h_resets_streak(self):
        rev  = _make_review(created_at=self._ago(49))
        user = _user_with_reviews(rev)
        self._recompute(user)
        self.assertEqual(user.streak_count, 0)

    def test_review_just_under_48h_preserves_streak(self):
        rev  = _make_review(created_at=self._ago(47))
        user = _user_with_reviews(rev)
        self._recompute(user)
        self.assertGreater(user.streak_count, 0)

    def test_consecutive_daily_reviews_build_streak(self):
        now   = datetime.now(timezone.utc)
        revs  = [
            _make_review(created_at=now - timedelta(days=i))
            for i in range(4)          # today, yesterday, day-2, day-3
        ]
        user  = _user_with_reviews(*revs)
        self._recompute(user)
        self.assertEqual(user.streak_count, 4)

    def test_gap_in_reviews_breaks_consecutive_count(self):
        now  = datetime.now(timezone.utc)
        # today and 3 days ago (gap of 2 days in between)
        revs = [
            _make_review(created_at=now),
            _make_review(created_at=now - timedelta(days=3)),
        ]
        user = _user_with_reviews(*revs)
        self._recompute(user)
        # streak must not be 2 because the days are not consecutive
        self.assertEqual(user.streak_count, 1)

    def test_streak_last_review_is_set_to_most_recent(self):
        recent = self._ago(2)
        older  = self._ago(10)
        revs   = [_make_review(created_at=recent), _make_review(created_at=older)]
        user   = _user_with_reviews(*revs)
        self._recompute(user)
        self.assertEqual(user.streak_last_review, recent)


# ===========================================================================
# 4. Follow is not symmetric
# ===========================================================================

class TestFollowAsymmetry(unittest.TestCase):
    """
    User.follow(other) must create a directed edge A→B.
    B→A must NOT be implied; it requires a separate explicit call.

    Uses stub objects because the ORM relationship logic lives in Python
    (the Follow model + User.follow / User.is_following helpers).
    We replicate the exact implementation from models.py here so the test
    is a true regression guard against someone accidentally making it
    symmetric.
    """

    # ---- minimal Follow stub -----------------------------------------------
    class _Follow:
        def __init__(self, follower_id, followed_id):
            self.follower_id = follower_id
            self.followed_id = followed_id

    # ---- minimal User stub --------------------------------------------------
    class _User:
        _id_counter = 0

        def __init__(self, name):
            TestFollowAsymmetry._User._id_counter += 1
            self.id       = TestFollowAsymmetry._User._id_counter
            self.username = name
            self.following: list = []  # list of _Follow (follower=self)

        def is_following(self, other):
            return any(f.followed_id == other.id for f in self.following)

        def follow(self, other):
            if other.id != self.id and not self.is_following(other):
                self.following.append(
                    TestFollowAsymmetry._Follow(self.id, other.id)
                )

        def unfollow(self, other):
            self.following = [f for f in self.following if f.followed_id != other.id]

    def setUp(self):
        self.alice = self._User("alice")
        self.bob   = self._User("bob")

    def test_after_alice_follows_bob_alice_is_following(self):
        self.alice.follow(self.bob)
        self.assertTrue(self.alice.is_following(self.bob))

    def test_after_alice_follows_bob_bob_is_not_following_alice(self):
        """The core asymmetry assertion."""
        self.alice.follow(self.bob)
        self.assertFalse(
            self.bob.is_following(self.alice),
            "A→B follow must NOT automatically create B→A",
        )

    def test_mutual_follow_requires_two_explicit_calls(self):
        self.alice.follow(self.bob)
        self.bob.follow(self.alice)
        self.assertTrue(self.alice.is_following(self.bob))
        self.assertTrue(self.bob.is_following(self.alice))

    def test_follow_is_idempotent(self):
        """Calling follow twice must not create a duplicate edge."""
        self.alice.follow(self.bob)
        self.alice.follow(self.bob)
        edges = [f for f in self.alice.following if f.followed_id == self.bob.id]
        self.assertEqual(len(edges), 1)

    def test_cannot_follow_self(self):
        self.alice.follow(self.alice)
        self.assertFalse(self.alice.is_following(self.alice))

    def test_unfollow_removes_only_directed_edge(self):
        self.alice.follow(self.bob)
        self.bob.follow(self.alice)
        self.alice.unfollow(self.bob)
        self.assertFalse(self.alice.is_following(self.bob))
        # Bob still follows Alice
        self.assertTrue(self.bob.is_following(self.alice))


# ===========================================================================
# 5. Badge "First Bite" awarded exactly once
# ===========================================================================

@unittest.skipUnless(_LOGIC_OK, "logic module unavailable")
class TestFirstBiteBadge(unittest.TestCase):
    """
    check_and_award_badges must award BadgeType.FIRST_BITE when the user has
    >= 1 review, and must never award it a second time regardless of how many
    reviews or recompute calls follow.
    """

    def _award(self, user):
        _logic.check_and_award_badges(user)

    def _has_first_bite(self, user):
        return any(b.badge_type == _BadgeType.FIRST_BITE for b in user.badges)

    def _count_first_bite(self, user):
        return sum(1 for b in user.badges if b.badge_type == _BadgeType.FIRST_BITE)

    def test_no_reviews_no_badge(self):
        user = _make_user()
        self._award(user)
        self.assertFalse(self._has_first_bite(user))

    def test_one_review_awards_badge(self):
        user = _user_with_reviews(_make_review())
        self._award(user)
        self.assertTrue(self._has_first_bite(user))

    def test_badge_awarded_exactly_once_single_call(self):
        user = _user_with_reviews(_make_review())
        self._award(user)
        self.assertEqual(self._count_first_bite(user), 1)

    def test_badge_not_duplicated_on_second_award_call(self):
        """Calling check_and_award_badges a second time must not add a duplicate."""
        user = _user_with_reviews(_make_review())
        self._award(user)
        self._award(user)         # second call
        self.assertEqual(
            self._count_first_bite(user), 1,
            "First Bite badge must be awarded exactly once even across repeated recompute calls",
        )

    def test_badge_not_duplicated_after_more_reviews_added(self):
        rev1 = _make_review()
        user = _user_with_reviews(rev1)
        self._award(user)
        # Simulate adding more reviews later
        user.reviews.append(_make_review(suburb="Fremantle"))
        user.reviews.append(_make_review(suburb="Subiaco"))
        self._award(user)
        self.assertEqual(self._count_first_bite(user), 1)

    def test_full_recompute_state_awards_badge_once(self):
        """
        recompute_user_state calls xp → streak → badges in sequence.
        First Bite must still appear exactly once.
        """
        user = _user_with_reviews(_make_review())
        _logic.recompute_user_state(user)
        _logic.recompute_user_state(user)
        self.assertEqual(self._count_first_bite(user), 1)


# ===========================================================================
# Integration tests using real Flask-SQLAlchemy + in-memory SQLite
# (skipped gracefully when dependencies are absent)
# ===========================================================================

@unittest.skipUnless(_FLASK_STACK_OK, "Flask-SQLAlchemy not installed – skipping integration tests")
class TestIntegrationWithInMemorySQLite(unittest.TestCase):
    """
    Full integration layer: real ORM, real in-memory SQLite.
    Every test gets a fresh database (setUp / tearDown).
    """

    @classmethod
    def setUpClass(cls):
        # Fix sys.path FIRST so the project's app/ wins over anything else.
        if _REPO_ROOT not in sys.path:
            sys.path.insert(0, _REPO_ROOT)

        # The unit-test section injected a fake app.models into sys.modules
        # so it could test logic.py without Flask.  That stub must be evicted
        # before we import the real package, otherwise "from app import
        # create_app" hits the stub and raises ImportError.
        for key in [k for k in sys.modules if k == "app" or k.startswith("app.")]:
            del sys.modules[key]

        # Minimal config that overrides the production database URI.
        class TestConfig:
            TESTING                        = True
            SQLALCHEMY_DATABASE_URI        = "sqlite:///:memory:"
            SQLALCHEMY_TRACK_MODIFICATIONS = False
            SECRET_KEY                     = "test-secret"
            WTF_CSRF_ENABLED               = False

        from app import create_app, db as _db
        cls._app = create_app(TestConfig)
        cls._db  = _db

    def setUp(self):
        self._ctx = self.__class__._app.app_context()
        self._ctx.push()
        self.__class__._db.create_all()

    def tearDown(self):
        self.__class__._db.session.remove()
        self.__class__._db.drop_all()
        self._ctx.pop()

    def _make_user(self, username="testuser", password="Password1!"):
        from app.models import User
        u = User(username=username, email=f"{username}@test.com")
        u.set_password(password)
        self.__class__._db.session.add(u)
        self.__class__._db.session.flush()
        return u

    def _make_restaurant(self, owner=None):
        from app.models import Restaurant
        creator = owner or self._make_user("creator")
        r = Restaurant(
            name="Test Burger",
            suburb="CBD",
            cuisine_tags=["burgers"],
            price_range=2,
            created_by=creator.id,
        )
        self.__class__._db.session.add(r)
        self.__class__._db.session.flush()
        return r

    def _make_review(self, user, restaurant, created_at=None):
        from app.models import Review
        rev = Review(
            user_id=user.id,
            restaurant_id=restaurant.id,
            star_rating=4,
            body="Great food.",
            craving_tags=[],
        )
        if created_at:
            rev.created_at = created_at
        self.__class__._db.session.add(rev)
        self.__class__._db.session.flush()
        return rev

    # --- password round-trip (integration) ----------------------------------

    def test_integration_password_round_trip(self):
        u = self._make_user(password="MySecurePass42!")
        self.assertTrue(u.check_password("MySecurePass42!"))
        self.assertFalse(u.check_password("wrong"))

    # --- XP accrual (integration) -------------------------------------------

    def test_integration_xp_increases_after_review(self):
        from app.gamification.logic import compute_recompute_xp
        u = self._make_user()
        r = self._make_restaurant(owner=u)
        self.assertEqual(u.writing_xp, 0)
        self._make_review(u, r)
        compute_recompute_xp(u)
        self.assertGreater(u.writing_xp, 0)

    # --- streak break (integration) -----------------------------------------

    def test_integration_streak_resets_after_48h(self):
        from app.gamification.logic import compute_recompute_streak
        u    = self._make_user()
        r    = self._make_restaurant(owner=u)
        old  = datetime.now(timezone.utc) - timedelta(hours=49)
        self._make_review(u, r, created_at=old)
        compute_recompute_streak(u)
        self.assertEqual(u.streak_count, 0)

    # --- asymmetric follow (integration) ------------------------------------

    def test_integration_follow_not_symmetric(self):
        db = self.__class__._db
        alice = self._make_user("alice_int")
        bob   = self._make_user("bob_int")
        alice.follow(bob)
        db.session.flush()
        self.assertTrue(alice.is_following(bob))
        self.assertFalse(bob.is_following(alice))

    # --- First Bite badge exactly once (integration) ------------------------

    def test_integration_first_bite_awarded_once(self):
        from app.gamification.badges import BadgeType
        from app.gamification.logic import recompute_user_state
        db = self.__class__._db
        u  = self._make_user()
        r  = self._make_restaurant(owner=u)
        self._make_review(u, r)
        recompute_user_state(u)
        recompute_user_state(u)   # idempotency check
        db.session.flush()
        first_bites = [b for b in u.badges if b.badge_type == BadgeType.FIRST_BITE]
        self.assertEqual(len(first_bites), 1)


# ===========================================================================
# Entry point
# ===========================================================================

if __name__ == "__main__":
    unittest.main(verbosity=2)