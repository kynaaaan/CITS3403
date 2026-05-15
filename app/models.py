import enum
import hashlib
from datetime import datetime, timezone
from flask_login import UserMixin

from sqlalchemy import Enum, UniqueConstraint
from werkzeug.security import check_password_hash, generate_password_hash

from app import db, login_manager


def _utcnow():
    return datetime.now(timezone.utc)


_AVATAR_PALETTE = [
    "#ff7e5f", "#0d6efd", "#20c997", "#6f42c1", "#d63384",
    "#fd7e14", "#198754", "#0dcaf0",
]


class LikeDimension(enum.Enum):
    ACCURACY = "accuracy"
    WRITING = "writing"
    BREADTH = "breadth"


class User(db.Model, UserMixin):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(40), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)

    is_restaurant_account = db.Column(db.Boolean, default=False, nullable=False)
    profile_is_public = db.Column(db.Boolean, default=True, nullable=False)

    writing_xp = db.Column(db.Integer, default=0, nullable=False)
    accuracy_xp = db.Column(db.Integer, default=0, nullable=False)
    explorer_xp = db.Column(db.Integer, default=0, nullable=False)
    streak_count = db.Column(db.Integer, default=0, nullable=False)
    streak_last_review = db.Column(db.DateTime, nullable=True)

    created_at = db.Column(db.DateTime, default=_utcnow, nullable=False)

    reviews = db.relationship(
        "Review", back_populates="user", cascade="all, delete-orphan",
    )
    badges = db.relationship(
        "Badge", back_populates="user", cascade="all, delete-orphan",
    )

    following = db.relationship(
        "Follow",
        foreign_keys="Follow.follower_id",
        back_populates="follower",
        cascade="all, delete-orphan",
    )
    followers = db.relationship(
        "Follow",
        foreign_keys="Follow.followed_id",
        back_populates="followed",
        cascade="all, delete-orphan",
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password, method="pbkdf2:sha256")

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def initials(self):
        return self.username[:2].upper() if self.username else "?"

    @property
    def avatar_colour(self):
        # Hash username so the colour is deterministic across processes.
        digest = hashlib.md5(self.username.encode("utf-8")).hexdigest()
        return _AVATAR_PALETTE[int(digest, 16) % len(_AVATAR_PALETTE)]

    def is_following(self, other):
        return any(f.followed_id == other.id for f in self.following)

    def follow(self, other):
        if other.id != self.id and not self.is_following(other):
            db.session.add(Follow(follower_id=self.id, followed_id=other.id))

    def unfollow(self, other):
        link = next((f for f in self.following if f.followed_id == other.id), None)
        if link:
            db.session.delete(link)

    def __repr__(self):
        return f"<User {self.username}>"


class Restaurant(db.Model):
    __tablename__ = "restaurants"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False, index=True)
    suburb = db.Column(db.String(40), nullable=False, index=True)
    cuisine_tags = db.Column(db.JSON, nullable=False, default=list)
    price_range = db.Column(db.Integer, nullable=False)  # 1, 2, or 3

    owner_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    created_at = db.Column(db.DateTime, default=_utcnow, nullable=False)

    reviews = db.relationship(
        "Review", back_populates="restaurant", cascade="all, delete-orphan",
    )

    @property
    def avg_rating(self):
        if not self.reviews:
            return 0.0
        return sum(r.star_rating for r in self.reviews) / len(self.reviews)

    @property
    def review_count(self):
        return len(self.reviews)

    def __repr__(self):
        return f"<Restaurant {self.name}>"


class Review(db.Model):
    __tablename__ = "reviews"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    restaurant_id = db.Column(db.Integer, db.ForeignKey("restaurants.id"), nullable=False)

    star_rating = db.Column(db.Integer, nullable=False)  # 1–5
    body = db.Column(db.Text, nullable=False)
    craving_tags = db.Column(db.JSON, nullable=False, default=list)
    price_paid = db.Column(db.Float, nullable=True)

    created_at = db.Column(db.DateTime, default=_utcnow, nullable=False)

    user = db.relationship("User", back_populates="reviews")
    restaurant = db.relationship("Restaurant", back_populates="reviews")
    likes = db.relationship(
        "ReviewLike", back_populates="review", cascade="all, delete-orphan",
    )

    @property
    def like_counts(self):
        counts = {"accuracy": 0, "writing": 0, "breadth": 0}
        for like in self.likes:
            counts[like.dimension.value] += 1
        return counts

    def __repr__(self):
        return f"<Review #{self.id} {self.star_rating}★>"


class ReviewLike(db.Model):
    __tablename__ = "review_likes"
    __table_args__ = (
        # A user can only like a given review once per dimension.
        UniqueConstraint("user_id", "review_id", "dimension", name="uq_review_like"),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    review_id = db.Column(db.Integer, db.ForeignKey("reviews.id"), nullable=False)
    dimension = db.Column(Enum(LikeDimension), nullable=False)

    created_at = db.Column(db.DateTime, default=_utcnow, nullable=False)

    review = db.relationship("Review", back_populates="likes")


class BadgeType(enum.Enum):
    """
    Badge types and their accompanying reqs
    """
    FIRST_BITE = "first_bite" # First review posted
    SUBURB_SCOUT = "suburb_scout" # 5+ distinct suburbs reviewed
    GLOBE_TROTTER = "globe_trotter" # 6+ distinct cuisines reviewed
    ON_FIRE = "on_fire" # 7 day streak
    PEN_AND_FORK = "pen_and_fork" # Level 5 Writing XP
    RUTHLESSLY_ACCURATE = "ruthlessly_accurate"  # 50 accuracy likes received


class Follow(db.Model):
    __tablename__ = "follows"
    __table_args__ = (
        UniqueConstraint("follower_id", "followed_id", name="uq_follow"),
    )

    id = db.Column(db.Integer, primary_key=True)
    follower_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    followed_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=_utcnow, nullable=False)

    follower = db.relationship(
        "User", foreign_keys=[follower_id], back_populates="following",
    )
    followed = db.relationship(
        "User", foreign_keys=[followed_id], back_populates="followers",
    )


class Badge(db.Model):
    __tablename__ = "badges"
    __table_args__ = (
        # Each badge is awarded at most once per user.
        UniqueConstraint("user_id", "badge_type", name="uq_user_badge"),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    badge_type = db.Column(Enum(BadgeType), nullable=False)
    awarded_at = db.Column(db.DateTime, default=_utcnow, nullable=False)

    user = db.relationship("User", back_populates="badges")


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))
