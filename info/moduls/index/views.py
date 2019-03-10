from info.models import User
from ..index import index_bp
from flask import render_template, current_app, session
from info import redis_store


@index_bp.route('/')
def hello_world():
    # 查询用户基本信息
    # 1.根据session获取用户id
    user_id = session.get('user_id')
    user = None
    # 2.根据用户id查询用户对象
    if user_id:
        try:
            user = User.query.get(user_id)
        except Exception as e:
            current_app.logger.error(e)
            return '查询用户对象异常'
    # 3.通过用户对象转换成字典

    user_dict = user.to_dict() if user else None

    data = {
        "user_info": user_dict,
    }


    # 4.返回模板的同时,将查询到的数据一并返回
    return render_template('news/index.html', data=data)


@index_bp.route('/favicon.ico')
def favicon():
    return current_app.send_static_file('news/favicon.ico')


