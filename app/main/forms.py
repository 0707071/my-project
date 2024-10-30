from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Length

class ClientForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(min=2, max=100)])
    description = TextAreaField('Description')
    is_active = BooleanField('Active')
    submit = SubmitField('Save')

class SearchQueryForm(FlaskForm):
    main_phrases = TextAreaField('Main Phrases', validators=[DataRequired()])
    include_words = TextAreaField('Include Words')
    exclude_words = TextAreaField('Exclude Words')
    notes = TextAreaField('Notes')
    is_active = BooleanField('Active Version')
    submit = SubmitField('Save')

class PromptForm(FlaskForm):
    content = TextAreaField('Prompt Text', validators=[DataRequired()])
    description = TextAreaField('Description')
    is_active = BooleanField('Active Version')
    submit = SubmitField('Save')
