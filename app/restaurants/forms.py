from flask_wtf import FlaskForm
from wtforms import RadioField, SelectField, SelectMultipleField, StringField, SubmitField
from wtforms.validators import DataRequired, Length, ValidationError
from wtforms.widgets import CheckboxInput, ListWidget

from app.models import Restaurant
from app.mock_data import SUBURB_DISPLAY, CUISINE_DISPLAY


class MultiCheckboxField(SelectMultipleField):
    """SelectMultipleField rendered as a list of checkboxes."""
    widget = ListWidget(prefix_label=False)
    option_widget = CheckboxInput()


class AddRestaurantForm(FlaskForm):
    name = StringField(
        'Restaurant name',
        validators=[DataRequired(), Length(max=120)],
    )

    suburb = SelectField(
        'Suburb',
        choices=[('', 'Select a suburb')] + list(SUBURB_DISPLAY.items()),
        validators=[DataRequired(message='Please select a suburb.')],
    )

    cuisine_tags = MultiCheckboxField(
        'Cuisine tags',
        choices=list(CUISINE_DISPLAY.items()),  # [('italian', 'Italian'), ...]
    )

    price_range = RadioField(
        'Price range',
        choices=[('1', '$'), ('2', '$$'), ('3', '$$$')],
        validators=[DataRequired(message='Please select a price range.')],
    )

    submit = SubmitField('Add restaurant')

    def validate_name(self, field):
        """Reject a name that already exists (case-insensitive)."""
        duplicate = Restaurant.query.filter(
            Restaurant.name.ilike(field.data.strip()),
        ).first()
        if duplicate:
            raise ValidationError(
                f'"{field.data}" is already listed — '
                f'<a href="/restaurant/{duplicate.id}">view it here</a>.'
            )


class EditRestaurantForm(AddRestaurantForm):
    submit = SubmitField('Save changes')

    def __init__(self, *args, restaurant_id=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._restaurant_id = restaurant_id

    def validate_name(self, field):
        # same rule as add, but allow the restaurant being edited to keep its own name.
        duplicate = Restaurant.query.filter(
            Restaurant.name.ilike(field.data.strip()),
            Restaurant.id != self._restaurant_id,
        ).first()
        if duplicate:
            raise ValidationError(
                f'"{field.data}" is already listed — '
                f'<a href="/restaurant/{duplicate.id}">view it here</a>.'
            )