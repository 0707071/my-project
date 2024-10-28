from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Length

class ClientForm(FlaskForm):
    name = StringField('Название', validators=[DataRequired(), Length(min=2, max=100)])
    description = TextAreaField('Описание')
    is_active = BooleanField('Активен')
    submit = SubmitField('Сохранить')

class SearchQueryForm(FlaskForm):
    main_phrases = TextAreaField('Основные фразы', validators=[DataRequired()])
    include_words = TextAreaField('Include слова')
    exclude_words = TextAreaField('Exclude слова')
    notes = TextAreaField('Заметки')
    is_active = BooleanField('Активная версия')
    submit = SubmitField('Сохранить')

class PromptForm(FlaskForm):
    content = TextAreaField('Текст промпта', validators=[DataRequired()])
    description = TextAreaField('Описание')
    is_active = BooleanField('Активная версия')
    submit = SubmitField('Сохранить')
