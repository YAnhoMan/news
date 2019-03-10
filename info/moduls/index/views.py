from info.models import User, News, Category
from ..index import index_bp
from flask import render_template, current_app, session, jsonify
from info import redis_store, constants
from info.response_code import RET


@index_bp.route('/')
def index():
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



    # 查询新闻列表数据,order_by(条件)
    try:
        rank_news_list = News.query.order_by(News.clicks.desc()).limit(constants.CLICK_RANK_MAX_NEWS)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.NODATA, errmsg='没有新闻')

    click_news_list = []
    for news in rank_news_list if rank_news_list else []:
        click_news_list.append(news.to_basic_dict())


    # 查询新闻分类列表
    try:
        categories = Category.query.all()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='查询分类失败')

    categories_list = []
    for category in categories if categories else []:
        categories_list.append(category.to_dict())

    data = {
        "user_info": user_dict,
        'click_news_list': click_news_list,
        'categories_list': categories_list,
    }

    # 4.返回模板的同时,将查询到的数据一并返回
    return render_template('news/index.html', data=data)


@index_bp.route('/favicon.ico')
def favicon():
    return current_app.send_static_file('news/favicon.ico')


