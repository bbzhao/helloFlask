import os
import uuid
import click
from urllib.parse import urlparse, urljoin

from flask import Flask, url_for, redirect, request, session, render_template, flash, Markup, send_from_directory, abort
from flask_wtf.csrf import validate_csrf
from jinja2.utils import generate_lorem_ipsum
from wtforms import ValidationError

from forms import *
from flask_ckeditor import CKEditor, upload_success, upload_fail

from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

db = SQLAlchemy(app)  # 传入程序实例，完成初始化

app.config['WTF_I18N_ENABLED'] = False  # 会让Flask-WTF 使用默认WTForms内置的错误消息翻译.
app.config['MAX_CONTENT_LENGTH'] = 3 * 1024 * 1024  # 限制请求报文的最大长度，从而限制最大上传文件的大小 （3M),文件过大 413 错误
app.config['UPLOAD_PATH'] = os.path.join(app.root_path, 'uploads')
app.config['ALLOWED_EXTENSIONS'] = ['png', 'jpg', 'jpeg', 'gif']
# ckeditor
app.config['CKEDITOR_SERVE_LOCAL'] = True
app.config['CKEDITOR_LANGUAGE'] = 'zh-cn'
app.config['CKEDITOR_FILE_UPLOADER'] = 'upload_for_ckeditor'

# sqlalchemy
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL',
                                                  'sqlite:///{0}'.format(os.path.join(app.root_path, 'data.db')))
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # 是否追踪对象的修改，用于sqlalchemy的时间通知系统

app.secret_key = os.getenv('SECRET_KEY', 'secret string')
ckeditor = CKEditor(app)
user = {
    'username': 'Grey Li',
    'bio': 'A boy who loves movies and music.',
}

movies = [
    {'name': 'My Neighbor Totoro', 'year': '1988'},
    {'name': 'Three Colours trilogy', 'year': '1993'},
    {'name': 'Forrest Gump', 'year': '1994'},
    {'name': 'Perfect Blue', 'year': '1997'},
    {'name': 'The Matrix', 'year': '1999'},
    {'name': 'Memento', 'year': '2000'},
    {'name': 'The Bucket list', 'year': '2007'},
    {'name': 'Black Swan', 'year': '2010'},
    {'name': 'Gone Girl', 'year': '2014'},
    {'name': 'CoCo', 'year': '2017'},
]


# 校验URL是否安全
def is_safe_url(target):
    # host_url 获取程序内部主机URL
    # urlparse 解析URL
    ref_url = urlparse(request.host_url)
    print(ref_url)
    # url_join 将目标url转换为绝对url
    test_url = urlparse(urljoin(request.host_url, target))
    print(test_url)
    # 对目标URL的URL模式和主机地址进行验证
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc


# 重定向到原地址
def redirect_back(default='hello_world', **kwargs):
    for target in request.args.get('next'), request.referrer:
        if not target:
            continue
        if is_safe_url(target):
            return redirect(target)
    return redirect(url_for(default, **kwargs))


# register template context handler
@app.context_processor
def inject_info():
    foo = 'I am foo.'
    return dict(foo=foo)  # equal to: return {'foo': foo}


# register template global function
@app.template_global()
def bar():
    return 'I am bar.'


# reigster template filter
@app.template_filter()
def musical(s):
    return s + Markup(' &#9835;')


# register template test
@app.template_test()
def baz(n):
    if n == 'baz':
        return True
    return False


@app.errorhandler(404)
def page_not_found(e):
    return render_template('errors/404.html'), 404


@app.errorhandler(405)
def method_not_found(e):
    return render_template('errors/405.html'), 405


@app.errorhandler(413)
def request_entity_too_large(e):
    return render_template('errors/413.html'), 413


@app.route('/watchlist')
def watchlist():
    return render_template('watchlist.html', user=user, movies=movies)


@app.route('/watchlist2')
def watchlist_with_static():
    return render_template('watchlist_with_static.html', user=user, movies=movies)


# 闪现消息
@app.route('/flash')
def just_flash():
    flash('I am flash, who is looking for me?')
    return redirect(url_for('index'))


@app.route('/post')
def show_post():
    # 生成两段随机文本
    post_body = generate_lorem_ipsum(n=2)
    return '''
    <h1>A very long post</h1>
    <div class="body">%s</div>
    <button id="load">Load More</button>
    <script src="https://code.jquery.com/jquery-3.3.1.min.js"></script>
    <script type="text/javascript">
    $(function() {
        $('#load').click(function() {
            $.ajax({
                url: '/more',
                type: 'get',
                success: function(data){
                    $('.body').append(data);
                }
            })
        })
    })
    </script>
    ''' % post_body


@app.route('/more')
def load_post():
    return generate_lorem_ipsum(n=1)


@app.route('/')
def index():
    # return 'Hello World!'
    form = DeleteNoteForm()
    notes = Note.query.all()
    return render_template('index.html', notes=notes, form=form)


@app.route('/edit/<int:note_id>', methods=['GET', 'POST'])
def edit_note(note_id):
    form = EditNoteForm()
    note = Note.query.get(note_id)
    if form.validate_on_submit():
        note.body = form.body.data
        db.session.commit()
        flash('Your note is updated.')
        return redirect(url_for('index'))
    form.body.data = note.body
    return render_template('edit_note.html', form=form)


@app.route('/delete/<int:note_id>', methods=['POST'])
def delete_note(note_id):
    form = DeleteNoteForm()
    if form.validate_on_submit():
        note = Note.query.get(note_id)
        db.session.delete(note)
        db.session.commit()
        flash('Your note is deleted.')
    else:
        abort(404)
    return redirect(url_for('index'))


@app.route('/do_something')
def do_something():
    # return redirect(url_for(request.referrer or 'hello_world'))
    return redirect_back()


@app.route('/foo')
def foo():
    return '<h1>Foo page</h1><a href="%s">Do something and redirect</a>' % url_for('do_something',
                                                                                   next=request.full_path)


@app.route('/bar')
def bar():
    return '<h1>Bar page</h1><a href="%s">Do something and redirect</a>' % url_for('do_something',
                                                                                   next=request.full_path)


@app.route('/basic', methods=['GET', 'POST'])
def basic():
    form = LoginForm()  # GET + POST
    # if request.method == 'POST' and form.validate(): 等价于下面的代码
    if form.validate_on_submit():  # form.validate_on_submit 在 PUT/PATCH/DELETE方法的时候都会验证表单,如果为True,代表用户提交了表单
        # 处理POST请求
        username = form.username.data
        flash('Welcome home, %s!' % username)
        return redirect(url_for('index'))
    return render_template('basic.html', form=form)


@app.route('/bootstrap', methods=['GET', 'POST'])
def bootstrap():
    form = LoginForm()
    return render_template('bootstrap.html', form=form)


def random_filename(filename):
    ext = os.path.splitext(filename)[1]  # 后缀
    new_filename = uuid.uuid4().hex + ext  # uuid 通用唯一识别码,使用来标识信息的128位数字
    return new_filename


@app.route('/upload', methods=['GET', 'POST'])
def upload():
    form = UploadForm()
    if form.validate_on_submit():
        f = form.photo.data
        filename = random_filename(f.filename)
        # filename = f.filename
        f.save(os.path.join(app.config['UPLOAD_PATH'], filename))
        flash('Upload success.')
        session['filenames'] = [filename]
        return redirect(url_for('show_images'))
    return render_template('upload.html', form=form)


# filename使用了path转换器，以支持传入包含斜线的路径字符串
@app.route('/uploads/<path:filename>')
def get_file(filename):
    return send_from_directory(app.config['UPLOAD_PATH'], filename)


@app.route('/show_images')
def show_images():
    return render_template('uploaded.html')


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


@app.route('/multi-upload', methods=['GET', 'POST'])
def multi_upload():
    form = MultiUploadForm()
    if request.method == 'POST':
        filenames = []
        # 验证CSRF 令牌
        try:
            validate_csrf(form.csrf_token.data)
        except ValidationError:
            flash('CSRF token error.')
            return redirect(url_for('multi_upload'))
        # 检查文件是否存在
        if 'photo' not in request.files:
            flash('This field is required.')
            return redirect(url_for('multi_upload'))

        for f in request.files.getlist('photo'):
            # 检查文件类型
            if f and allowed_file(f.filename):
                filename = random_filename(f.filename)
                f.save(os.path.join(app.config['UPLOAD_PATH'], filename))
                filenames.append(filenames)
            else:
                flash('Invalid file type.')
                return redirect(url_for('multi_upload'))
        flash('Upload success.')
        session['filenames'] = filenames
        return redirect(url_for('show_images'))
    return render_template('upload.html', form=form)


@app.route('/ckeditor', methods=['GET', 'POST'])
def integrate_ckeditor():
    form = RichTextForm()
    if form.validate_on_submit():
        title = form.title.data
        body = form.body.data
        flash('Your post is published!')
        return render_template('post.html', title=title, body=body)
    return render_template('ckeditor.html', form=form)


# handle image upload for ckeditor
@app.route('/upload-ck', methods=['POST'])
def upload_for_ckeditor():
    f = request.files.get('upload')
    if not allowed_file(f.filename):
        return upload_fail('Image only!')
    f.save(os.path.join(app.config['UPLOAD_PATH'], f.filename))
    url = url_for('get_file', filename=f.filename)
    return upload_success(url, f.filename)


@app.route('/two-submits', methods=['GET', 'POST'])
def two_submits():
    form = NewPostForm()
    if form.validate_on_submit():
        if form.save.data:
            # save it ...
            flash('You click the "Save" button.')
        elif form.publish.data:
            # publish it...
            flash('You click the "Publish" button.')
        return redirect(url_for('index'))
    return render_template('2submit.html', form=form)


# database
class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text)

    def __repr__(self):
        return '<Note {0}>'.format(self.body)


@app.cli.command()
def initdb():
    db.create_all()
    click.echo('Initialized database.')


@app.route('/new_note', methods=['GET', 'POST'])
def new_note():
    form = NewNoteForm()
    if form.validate_on_submit():
        body = form.body.data
        note = Note(body=body)
        db.session.add(note)
        db.session.commit()
        flash('Your note is saved.')
        return redirect(url_for('index'))
    return render_template('new_note.html', form=form)


@app.shell_context_processor
def make_shell_content():
    return dict(db=db, Note=Note, Article=Article, Author=Author)


class Author(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(70), unique=True)
    phone = db.Column(db.String(20))
    articles = db.relationship('Article')


class Article(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(50), index=True)
    body = db.Column(db.Text)
    author_id = db.Column(db.Integer, db.ForeignKey('author.id'))

    def __repr__(self):
        return "<Article '{0}'>".format(self.title)


class Writer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(70), unique=True)
    books = db.relationship('Book', back_populates='writer')


class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String, index=True)
    writer_id = db.Column(db.Integer, db.ForeignKey('writer.id'))
    writer = db.relationship('Writer', back_populates='books')


class Country(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30), unique=True)
    capital = db.relationship('Capital', uselist=False)

    def __repr__(self):
        return "<Country '{0}'>".format(self.name)


class Capital(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30), unique=True)
    country_id = db.Column(db.Integer, db.ForeignKey('country.id'))
    country = db.relationship('Country')

    def __repr__(self):
        return "<Capital '{0}'>".format(self.name)


if __name__ == '__main__':
    app.run()
