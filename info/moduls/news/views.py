from sqlalchemy import and_

from info import constants
from info.common import user_login_data
from info.models import News, tb_user_collection, Comment
from info.moduls.news import news_bp
from flask import render_template, current_app, jsonify, abort, g, session, request

from info.response_code import RET


@news_bp.route('/<int:news_id>')
@user_login_data
def news_detail(news_id):

    # 查询文章内容详情
    try:
        news = News.query.get(news_id)
    except Exception as e:
        current_app.logger.error(e)
        abort(404)
        return jsonify(errno=RET.DBERR, errmsg="数据库查询异常")
    if not news:
        abort(404)

    news.clicks += 1
    # 查询点击排行数据
    try:
        rank_news_list = News.query.order_by(News.clicks.desc()).limit(constants.CLICK_RANK_MAX_NEWS)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.NODATA, errmsg='没有新闻')
    click_news_list = []
    for rank_news in rank_news_list if rank_news_list else []:
        click_news_list.append(rank_news.to_basic_dict())

    # 查询当前用户的具体信息,包括是否关注

    is_collected = False
    if g.user and news in g.user.collection_news:
        is_collected = True

    data = {
        'news': news.to_dict(),
        'user_info': g.user_info,
        'click_news_list': click_news_list,
        'is_collected': is_collected

    }
    return render_template("news/detail.html", data=data)


@news_bp.route('/new_collect', methods=['POST'])
@user_login_data
def handle_collect():

    news_id = request.json.get('news_id')
    action = request.json.get('action')
    user_id = g.user_id

    if not user_id:
        return jsonify(errno=RET.SESSIONERR, errmsg="用户未登录")

    if not news_id:
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    if action not in ("collect", "cancel_collect"):
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    try:
        news = News.query.get(news_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="查询新闻失败")

    if news:
        if action == "collect":
            g.user.collection_news.append(news)
        else:
            g.user.collection_news.remove(news)

    return jsonify(errno=RET.OK, errmsg='OK')

@news_bp.route('/new_comment', methods=['POST'])
@user_login_data
def new_comment():

    news_id = request.json.get('news_id')
    comment = request.json.get('comment')
    parent_id = request.json.get('parent_id')
    user_id = g.user_id

    if not user_id:
        return jsonify(errno=RET.SESSIONERR, errmsg="用户未登录")

    if not all([news_id, comment]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    try:
        news = News.query.get(news_id)
        parent_comment = Comment.query.get()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="查询新闻失败")

