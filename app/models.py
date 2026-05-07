import enum
from datetime import datetime, timezone

from sqlalchemy import Enum, UniqueConstraint
from werkzeug.security import check_password_hash, generate_password_hash

from app import db


def _utcnow():
    return datetime.now(timezone.utc)


class LikeDimension(enum.Enum):
    ACCURACY = "accuracy"
    WRITING = "writing"
    BREADTH = "breadth"


class User(db.Model):
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

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

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
