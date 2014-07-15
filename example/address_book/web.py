import flask
from flask.ext import kibble


app = flask.Flask(__name__)
app.debug = True
app.config['SECRET_KEY'] = 'SEKRET'
app.config['CSRF_SECRET_KEY'] = 'CSRF SEKRET'

admin = kibble.Kibble(
    'kibble',
    __name__,
    kibble.Authenticator(),
    label='Example Address Book',
    static_url_path='/kibble/static'
)

admin.autodiscover(
    paths=[
        'address_book',
    ])

app.register_blueprint(admin)
