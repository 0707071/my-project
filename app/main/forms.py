from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, BooleanField, SubmitField, IntegerField, SelectField, FieldList, FormField
from wtforms.validators import DataRequired, Length, NumberRange

class ClientForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(min=2, max=100)])
    description = TextAreaField('Description')
    is_active = BooleanField('Active')
    submit = SubmitField('Save')

class SearchQueryForm(FlaskForm):
    main_phrases = TextAreaField('Main Phrases', 
        validators=[DataRequired()],
        description='Enter each phrase on a new line')
    include_words = TextAreaField('Include Words',
        description='Words to include, each on a new line')
    exclude_words = TextAreaField('Exclude Words',
        description='Words to exclude, each on a new line')
    notes = TextAreaField('Notes')
    is_active = BooleanField('Active Version')
    
    days_back = IntegerField('Days to Look Back', 
        validators=[NumberRange(min=1, max=365)],
        default=7)
    results_per_page = IntegerField('Results per Page',
        validators=[NumberRange(min=10, max=100)],
        default=100)
    num_pages = IntegerField('Number of Pages',
        validators=[NumberRange(min=1, max=10)],
        default=2)
    
    submit = SubmitField('Save')
    
    def __init__(self, *args, **kwargs):
        super(SearchQueryForm, self).__init__(*args, **kwargs)
        if 'obj' in kwargs:
            # Если форма используется для редактирования, меняем текст кнопки
            self.submit.label.text = 'Update'

class PromptFieldForm(FlaskForm):
    name = StringField('Column Name', validators=[DataRequired()])

class PromptForm(FlaskForm):
    content = TextAreaField('Prompt Text', validators=[DataRequired()])
    description = TextAreaField('Description')
    is_active = BooleanField('Active Version')
    fields = FieldList(FormField(PromptFieldForm), min_entries=1)
    submit = SubmitField('Save')
