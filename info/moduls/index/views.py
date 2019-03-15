from info.common import user_login_data
from info.models import User, News, Category
from ..index import index_bp
from flask import render_template, current_app, session, jsonify, request, g
from info import redis_store, constants
from info.response_code import RET


@index_bp.route('/news_list', methods=['GET'])
def get_news_list():
    """获取首页新闻列表数据接口"""

    """
    1.获取参数
        1.1 cid: 当前分类id，page:当前页码，默认值：1， per_page:每一页多少条数据，默认值：10
    2.参数校验
        2.1 判断cid是否为空
        2.2 将数据进行int强制类型转换
    3.逻辑处理
        3.1 根据cid作为查询条件获取查询对象，再调用paginate方法进行数据分页处理
        3.2 调用分类对象的属性 获取当前页所有数据，当前页码，总页码
        3.3 将新闻对象列表转换成字典列表
    4.返回值
    """
    cid = request.args.get('cid')

    page = request.args.get('page', 1)

    per_page = request.args.get('per_page', 10)

    if not cid:
        return jsonify(errno=RET.PARAMERR, errmsg="参数不足")

    try:
        cid = int(cid)
        page = int(page)
        per_page = int(per_page)

    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg="参数格式错误")

    # 这个是条件列表,需要变动的条件可以在此加入
    filter_list = [News.status == 0]

    if cid != 1:
        filter_list.append(News.category_id == cid)

    try:
        paginate = News.query.filter(*filter_list).order_by(News.create_time.desc()).paginate(page, per_page, False)

        news_list = paginate.items

        current_page = paginate.page

        total_page = paginate.pages

    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="查询数据库出错")

    news_dict_list = []

    for news in news_list:
        news_dict_list.append(news.to_dict())

    data = {
        'news_dict_list': news_dict_list,
        'current_page': current_page,
        'total_page': total_page
    }

    return jsonify(errno=RET.OK, errmsg='OK', data=data)


@index_bp.route('/')
@user_login_data
def index():
    # 查询用户基本信息
    # # 1.根据session获取用户id
    # user_id = session.get('user_id')
    # user = None
    # # 2.根据用户id查询用户对象
    # if user_id:
    #     try:
    #         user = User.query.get(user_id)
    #     except Exception as e:
    #         current_app.logger.error(e)
    #         return '查询用户对象异常'
    # # 3.通过用户对象转换成字典
    #
    # user_info = user.to_dict() if user else None



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
        "user_info": g.user_info,
        'click_news_list': click_news_list,
        'categories_list': categories_list,
    }

    # 4.返回模板的同时,将查询到的数据一并返回
    return render_template('news/index.html', data=data)


@index_bp.route('/favicon.ico')
def favicon():
    return current_app.send_static_file('news/favicon.ico')


