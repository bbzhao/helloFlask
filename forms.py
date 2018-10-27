from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import Form, StringField, PasswordField, BooleanField, SubmitField, IntegerField, MultipleFileField, TextAreaField
from wtforms.validators import DataRequired, Length, ValidationError
from flask_ckeditor import CKEditorField

# 自定义验证器-行内验证器
class FortyTowForm(FlaskForm):
    answer = IntegerField('The Number')
    submit = SubmitField()

    @staticmethod
    def validate_answer(form, field):
        if field.data != 42:
            raise ValidationError('Must be 42.')


# 全局验证器,使用的时候在 answer = IntegerField('The number', validators=[is_42()])
# 工厂函数形式的全局验证器示例
def is_42(message=None):
    if message is None:
        message = 'Must be 42.'

    def _is_42(form, field):
        if field.data != '42':
            raise ValidationError(message)
    return _is_42


# 表单
class MyBaseForm(FlaskForm):
    class Meta:
        locales = ['zh']


class LoginForm(MyBaseForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired(), Length(8, 128)])
    # password = PasswordField('Password', validators=[DataRequired(), is_42('要是42啊')])
    remember = BooleanField('Remember me')
    submit = SubmitField('Log in')


class UploadForm(FlaskForm):
    photo = FileField('Upload Image', validators=[FileRequired(), FileAllowed(['jpg', 'jpeg', 'png', 'gif'])],
                      render_kw={'accept': '.jpg, .jpeg, .png .gif'})
    submit = SubmitField()


class MultiUploadForm(FlaskForm):
    photo = MultipleFileField('Upload Image', validators={DataRequired()})
    submit = SubmitField()


class RichTextForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(1,50)])
    body = CKEditorField('Body', validators=[DataRequired()])
    submit = SubmitField('Publish')


class NewPostForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(1, 50)])
    body = TextAreaField('Body', validators=[DataRequired()])
    save = SubmitField('Save')  # 保存
    publish = SubmitField('Publish')  # 发布


class NewNoteForm(FlaskForm):
    body = TextAreaField('Body', validators=[DataRequired()])
    submit = SubmitField('Save')


class EditNoteForm(NewNoteForm):
    submit = SubmitField('Update')


class DeleteNoteForm(FlaskForm):
    submit = SubmitField('Delete')


class EmailForm(FlaskForm):
    to = StringField('To', validators=[DataRequired(), Email()])
    subject = StringField('Subject', validators=[DataRequired()])
    body = TextAreaField('Body', validators=[DataRequired()])
    submit_smtp = SubmitField('Send with SMTP')
    submit_api = SubmitField('Send with SendGrid API')
    submit_async = SubmitField('Send with SMTP asynchronously')


class SubscribeForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Subscribe')
