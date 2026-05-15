from flask_login import current_user
from flask_wtf import FlaskForm
from wtforms import BooleanField, PasswordField, StringField, SubmitField
from wtforms.validators import (
    DataRequired,
    Email,
    EqualTo,
    Length,
    Optional,
    ValidationError,
)

from app.models import User


class ProfileEditForm(FlaskForm):

    username = StringField(
        'Username',
        validators=[DataRequired(), Length(min=3, max=40)],
    )
    email = StringField(
        'Email',
        validators=[DataRequired(), Email()],
    )
    profile_is_public = BooleanField('Public profile')

    current_password = PasswordField(
        'Current password',
        validators=[Optional()],
    )
    new_password = PasswordField(
        'New password',
        validators=[Optional(), Length(min=8)],
    )
    confirm_password = PasswordField(
        'Confirm new password',
        validators=[
            Optional(),
            EqualTo('new_password', message='Passwords must match.'),
        ],
    )

    submit = SubmitField('Save changes')

    def validate_username(self, field):
        """Reject usernames that belong to a different user."""
        existing = User.query.filter_by(username=field.data).first()
        if existing and existing.id != current_user.id:
            raise ValidationError('Username already taken.')

    def validate_email(self, field):
        """Reject emails that belong to a different user."""
        existing = User.query.filter_by(email=field.data).first()
        if existing and existing.id != current_user.id:
            raise ValidationError('Email already registered.')

    def validate_new_password(self, field):
        """If the user is changing their password they must supply current_password."""
        if field.data and not self.current_password.data:
            raise ValidationError(
                'Enter your current password to set a new one.'
            )

    def validate_current_password(self, field):
        """If current_password is supplied it must actually match."""
        if field.data and not current_user.check_password(field.data):
            raise ValidationError('Current password is incorrect.')
