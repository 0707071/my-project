from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, BooleanField, SubmitField, IntegerField, SelectField, FieldList, FormField
from wtforms.validators import DataRequired, Length, NumberRange

class ClientForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(min=2, max=100)])
    description = TextAreaField('Description')
    is_active = BooleanField('Active')
    submit = SubmitField('Save')

class SearchQueryForm(FlaskForm):
    main_phrases = TextAreaField('Search Phrases', validators=[DataRequired()])
    include_words = TextAreaField('Include Words')
    exclude_words = TextAreaField('Exclude Words')
    notes = TextAreaField('Notes')
    days_back = IntegerField('Days Back', default=7)
    results_per_page = IntegerField('Results Per Page', default=10)
    num_pages = IntegerField('Number of Pages', default=1)
    is_active = BooleanField('Active')
    submit = SubmitField('Save')
    
    def __init__(self, *args, **kwargs):
        super(SearchQueryForm, self).__init__(*args, **kwargs)
        if 'obj' in kwargs:
            # Если форма используется для редактирования, меняем текст кнопки
            self.submit.label.text = 'Update'

class PromptForm(FlaskForm):
    content = TextAreaField('Prompt Text', validators=[DataRequired()])
    description = TextAreaField('Description')
    is_active = BooleanField('Active Version')
    column_names = TextAreaField('Column Names', 
        description='Enter each column name on a new line in the same order as questions in the prompt',
        validators=[DataRequired()])
    submit = SubmitField('Save')

    def __init__(self, *args, **kwargs):
        super(PromptForm, self).__init__(*args, **kwargs)
        if kwargs.get('obj'):
            self.submit.label.text = 'Update'
