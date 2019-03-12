import functools

from flask import session, g, current_app

from info.models import User


def user_login_data(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        user_id = session.get('user_id')
        g.user = None
        # 2.根据用户id查询用户对象
        if user_id:
            try:
                g.user = User.query.get(user_id)
            except Exception as e:
                current_app.logger.error(e)
                return '查询用户对象异常'
        # 3.通过用户对象转换成字典

        g.user_info = g.user.to_dict() if g.user else None

        return func(*args, **kwargs)

    return wrapper

