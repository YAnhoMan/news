from ..index import index_bp


@index_bp.route('/')
def hello_world():
    return 'Hello World!'

