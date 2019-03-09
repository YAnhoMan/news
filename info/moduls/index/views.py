from ..index import index_bp
from flask import render_template, current_app
from info import redis_store


@index_bp.route('/')
def hello_world():
    redis_store.setex('name', 10, 'laowang',)
    return render_template('news/index.html')


@index_bp.route('/favicon.ico')
def favicon():
    return current_app.send_static_file('news/favicon.ico')


