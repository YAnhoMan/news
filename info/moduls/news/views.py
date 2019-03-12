from sqlalchemy import and_

from info import constants, db
from info.common import user_login_data
from info.models import News, tb_user_collection, Comment, CommentLike
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

    # 查询该文章的评论列表,加用户是否点赞

    try:
        comment_list = Comment.query.filter(Comment.news_id == news_id).order_by(
            Comment.like_count.desc()).all()  # 评论对象列表
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="查询数据库错误")

    comment_like_ids = []
    if g.user:
        try:
            comment_ids = [comment.id for comment in comment_list]  # 获取当前文章的所有评论id
            if len(comment_ids) > 0:
                comments_user = CommentLike.query.filter(CommentLike.comment_id.in_(comment_ids),
                                                         CommentLike.user_id == g.user_id).all()  # 获取当前文章该用户的所有点赞记录
                comment_like_ids = [comment.id for comment in comments_user]  # 从当前文章该用户的所有点赞记录中抽取评论id
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.DBERR, errmsg="数据库查询错误")

    comment_dict_list = []
    for each_comment in comment_list:
        comment_data = each_comment.to_dict()
        comment_data['is_user_like'] = True if g.user and comment_data.id in comment_like_ids else False
        comment_dict_list.append(comment_data)

    # for each_comment in comment_list:
    #     comment_data = each_comment.to_dict()
    #     if g.user:
    #         try:
    #             is_like = CommentLike.query.filter(and_(CommentLike.comment_id == each_comment.id, CommentLike.user_id == g.user_id)).first()
    #         except Exception as e:
    #             current_app.logger.error(e)
    #             return jsonify(errno=RET.DBERR, errmsg="查询数据库失败")
    #
    #         if is_like:
    #             comment_data['is_user_like'] = True
    #         else:
    #             comment_data['is_user_like'] = False
    #
    #     comment_dict_list.append(comment_data)

    data = {
        'news': news.to_dict(),
        'user_info': g.user_info,
        'click_news_list': click_news_list,
        'is_collected': is_collected,
        'comment_list': comment_dict_list

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

    try:
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg="保存失败")

    return jsonify(errno=RET.OK, errmsg='OK')


@news_bp.route('/new_comment', methods=['POST'])
@user_login_data
def new_comment():
    user_id = g.user_id
    if not user_id:
        return jsonify(errno=RET.SESSIONERR, errmsg="用户未登录")

    news_id = request.json.get('news_id')
    comment_str = request.json.get('content')

    if not all([news_id, comment_str]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    parent_id = request.json.get('parent_id')

    try:
        news = News.query.get(news_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="查询新闻失败")

    if not news:
        return jsonify(errno=RET.NODATA, errmsg="不存在该新闻")

    comment = Comment()
    comment.user_id = user_id
    comment.news_id = news_id
    comment.content = comment_str
    if parent_id:
        comment.parent_id = parent_id

    try:
        db.session.add(comment)  # 记得当你要提交新数据的时候,就要先add
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg="保存失败",)

    return jsonify(errno=RET.OK, errmsg='OK', data=comment.to_dict())


@news_bp.route('/comment_like', methods=['POST'])
@user_login_data
def handler_comment_like():

    user_id = g.user_id
    if not user_id:
        return jsonify(errno=RET.SESSIONERR, errmsg="用户未登录")

    comment_id = request.json.get('comment_id')
    action = request.json.get('action')

    if not comment_id or action not in ['add', 'remove']:
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    try:
        comment = Comment.query.get(comment_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="查询数据失败")

    if not comment:
        return jsonify(errno=RET.NODATA, errmsg="不存在该评论")

    try:
        comment_like = CommentLike.query.filter(and_(CommentLike.comment_id == comment_id, CommentLike.user_id == user_id)).first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="查询数据失败")

    if action == 'add':
        if comment_like:
            return jsonify(errno=RET.DATAEXIST, errmsg="已经为该评论点过赞")
        else:
            new_like = CommentLike()
            new_like.comment_id = comment_id
            new_like.user_id = user_id
            comment.like_count += 1
            db.session.add(new_like)
    else:
        if not comment_like:
            return jsonify(errno=RET.NODATA, errmsg="还未给该条评论点赞!")
        else:
            db.session.delete(comment_like)
            comment.like_count -= 1

    try:
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="操作失败!")

    return jsonify(errno=RET.OK, errmsg="操作成功!")

