from flask import Flask

app = Flask(__name__)

@app.route('/hello/')
@app.route('/')
def hello_world():
    return 'Hello World!'


@app.route('/greet/', defaults={'name':'Programmer'})
@app.route('/greet/<name>')
def greet(name):
    return 'hello,%s!' % name


if __name__ == '__main__':
    app.run()
