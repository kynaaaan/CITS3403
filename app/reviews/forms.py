from flask_wtf import FlaskForm
from wtforms import (
    FloatField,
    IntegerField,
    SelectField,
    SelectMultipleField,
    SubmitField,
    TextAreaField,
)
from wtforms.validators import DataRequired, Length, NumberRange, Optional
from wtforms.widgets import CheckboxInput, ListWidget

from app.models import Restaurant


# Locked craving tag slugs (CONTEXT.md). Order = display order on the form.
CRAVING_CHOICES = [
    ("hearty", "Hearty"),
    ("classy", "Classy"),
    ("spicy", "Spicy"),
    ("sweet", "Sweet"),
    ("cheap", "Cheap"),
    ("healthy", "Healthy"),
    ("indulgent", "Indulgent"),
    ("wine", "Wine"),
    ("cocktails", "Cocktails"),
    ("pricey", "Pricey"),
    ("date-night", "Date-night"),
]


class MultiCheckboxField(SelectMultipleField):
    """SelectMultipleField rendered as a list of checkboxes."""
    widget = ListWidget(prefix_label=False)
    option_widget = CheckboxInput()


class WriteReviewForm(FlaskForm):
    restaurant_id = SelectField(
        "Restaurant",
        coerce=int,
        validators=[NumberRange(min=1, message="Please choose a restaurant.")],
    )

    star_rating = IntegerField(
        "Rating",
        validators=[
            DataRequired(message="Please pick a star rating."),
            NumberRange(min=1, max=5, message="Rating must be between 1 and 5."),
        ],
    )

    body = TextAreaField(
        "Review",
        validators=[
            DataRequired(),
            Length(min=20, max=4000, message="Review must be 20–4000 characters."),
        ],
    )

    craving_tags = MultiCheckboxField("Craving tags", choices=CRAVING_CHOICES)

    price_paid = FloatField(
        "Price paid",
        validators=[Optional(), NumberRange(min=0, message="Price cannot be negative.")],
    )

    submit = SubmitField("Submit review")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Populate restaurant dropdown from the DB on every instantiation so
        # newly added restaurants appear without a server restart.
        self.restaurant_id.choices = [(0, "Select a restaurant")] + [
            (r.id, r.name) for r in
            Restaurant.query.order_by(Restaurant.name).all()
        ]
