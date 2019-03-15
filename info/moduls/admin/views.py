from datetime import datetime, timedelta
# import datetime
import time

from flask import render_template, request, g, redirect, jsonify, current_app, session, url_for
from info import user_login_data, constants, db
from info.models import User, News, Category
from info.moduls.admin import admin_bp
from info.response_code import RET
from info.utils.image_storage import upload_img


@admin_bp.route('/login', methods=['POST', 'GET'])
def admin_login():
    if request.method == 'GET':
        user_id = session.get("user_id", None)
        is_admin = session.get("is_admin", False)
        if user_id and is_admin:
            return redirect(url_for('admin.admin_index'))
        return render_template('admin/login.html')

    user_name = request.form.get('username')
    passoword = request.form.get('password')

    if not all([user_name, passoword]):
        return jsonify(errno=RET.PARAMERR, errmsg='参数错误')

    try:
        user = User.query.filter(User.mobile == user_name).first()
    except Exception as e:
        current_app.logger.error(e)
        return render_template('admin/login.html', errmsg="数据查询失败")

    if not user:
        return render_template('admin/login.html', errmsg="用户不存在")

    if not user.is_admin:
        return render_template('admin/login.html', errmsg="用户权限错误")

    if not user.check_password(passoword):
        return render_template('admin/login.html', errmsg="用户密码错误")

    session["user_id"] = user.id
    session["nick_name"] = user.nick_name
    session["mobile"] = user.mobile
    if user.is_admin:
        session["is_admin"] = True

    return redirect(url_for('admin.admin_index'))


@admin_bp.route('/')
@user_login_data
def admin_index():
    """站点主页
    """
    # 读取登录用户的信息
    # 优化进入主页逻辑：如果管理员进入主页，必须要登录状态以及管理员，反之，就引导到登录界面
    if not g.user:
        return redirect(url_for('admin.admin_login'))

    # 构造渲染数据
    data = {
        'user': g.user_info
    }
    # 渲染主页
    return render_template('admin/index.html', data=data)


@admin_bp.route('/user_count')
def user_count():
    #  查询总人数
    total_count = 0

    try:
        total_count = User.query.filter(User.is_admin == False).count()
    except Exception as e:
        current_app.logger.error(e)

    # 查询月新增数
    mon_count = 0
    try:
        now = time.localtime()

        mon_begin = '%d-%02d-01' % (now.tm_year, now.tm_mon)

        mon_begin_date = datetime.strptime(mon_begin, '%Y-%m-%d')

        mon_count = User.query.filter(User.is_admin == False, User.create_time >= mon_begin_date).count()

    except Exception as e:
        current_app.logger.error(e)

    # 查询日新增数

    day_count = 0

    try:
        day_begin = '%d-%02d-%02d' % (now.tm_year, now.tm_mon, now.tm_mday)

        day_begin_date = datetime.strptime(day_begin, '%Y-%m-%d')

        day_count = User.query.filter(User.is_admin == False, User.create_time >= day_begin_date).count()

    except Exception as e:
        current_app.logger.error(e)

    now_date = datetime.strptime(datetime.now().strftime('%Y-%m-%d'), '%Y-%m-%d')

    active_date = []
    active_count = []

    for i in range(0, 31):

        try:
            begin_date = now_date - timedelta(days=i)

            end_date = now_date - timedelta(days=(i - 1))

            active_date.append(begin_date.strftime('%Y-%m-%d'))

            count = User.query.filter(User.is_admin == False, User.last_login >= begin_date,
                                      User.last_login < end_date).count()

            active_count.append(count)

        except Exception as e:
            current_app.logger.error(e)

    active_count.reverse()
    active_date.reverse()

    data = {"total_count": total_count, "mon_count": mon_count, "day_count": day_count, "active_date": active_date,
            "active_count": active_count}

    return render_template('admin/user_count.html', data=data)

@admin_bp.route('/user_list')
def user_list():

    p = request.args.get('p', 1)
    try:
        p = int(p)
    except Exception as e:
        current_app.logger.error(e)
        p = 1

    users = []
    current_page = 1
    total_page = 1

    try:
        paginate = User.query.filter(User.is_admin == False).order_by(User.last_login.desc()).paginate(p, constants.ADMIN_USER_PAGE_MAX_COUNT, False)

        users = paginate.items

        current_page = paginate.page

        total_page = paginate.pages

    except Exception as e:
        current_app.logger.error(e)

    users_dict = [user.to_admin_dict() for user in users]

    data = {
        'users': users_dict,
        'total_page': total_page,
        'current_page': current_page
    }

    return render_template('admin/user_list.html', data=data)


@admin_bp.route('/news_review')
def news_review():

    p = request.args.get('p', 1)

    keywords = request.args.get('keywords', "")

    try:
        p = int(p)
    except Exception as e:
        current_app.logger.error(e)
        p = 1

    news_list = []
    current_page = 1
    total_page = 1

    filters = [News.status != '0']

    if keywords:
        filters.append(News.title.contains(keywords))

    try:
        paginate = News.query.filter(*filters).order_by(News.create_time.desc()).paginate(p, constants.ADMIN_NEWS_REVIEW_PAGE_MAX_COUNT, False)

        news_list = paginate.items

        current_page = paginate.page

        total_page = paginate.pages

    except Exception as e:
        current_app.logger.error(e)

    news_dict = [news.to_review_dict() for news in news_list]

    data = {
        'news_dict': news_dict,
        'current_page':current_page,
        'total_page': total_page
    }

    return render_template('admin/news_review.html', data=data)


@admin_bp.route('/news_review_detail', methods=['POST', 'GET'])
def news_review_detail():

    if request.method == 'GET':

        news_id = request.args.get('news_id', '')

        if not news_id:
            return render_template('admin/news_review_detail.html', data={"errmsg": "未查询到此新闻"})

        news = None

        try:
            news = News.query.get(news_id)
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.DBERR, errmsg="查询数据库失败")

        if not news:
            return render_template('admin/news_review_detail.html', data={"errmsg": "未查询到此新闻"})

        data = {
            'news': news.to_dict()
        }

        return render_template('admin/news_review_detail.html', data=data)

    else:

        news_id = request.json.get('news_id')

        action = request.json.get('action')

        if not all([news_id, action]) or action not in ["accept", "reject"]:
            return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

        news = None

        try:
            news = News.query.get(news_id)
        except Exception as e:
            current_app.logger.error(e)

        if not news:
            return jsonify(errno=RET.NODATA, errmsg="未查询到数据")

        if action == 'accept':
            news.status = 0
        else:
            reason = request.json.get('reason')
            if not reason:
                return jsonify(errno=RET.PARAMERR, errmsg="参数错误")
            news.reason = reason
            news.status = -1

        try:
            db.session.commit()
        except Exception as e:
            current_app.logger.error(e)
            db.session.rollback()
            return jsonify(errno=RET.DBERR, errmsg="数据保存失败")

        return jsonify(errno=RET.OK, errmsg="操作成功")


@admin_bp.route('/news_edit')
def news_edit():

    p = request.args.get('p', 1)
    keywords = request.args.get('keywords', '')

    try:
        p = int(p)
    except Exception as e:
        current_app.logger.error(e)
        p = 1

    news_items = []
    current_page = 1
    total_page = 1

    try:
        filters = []

        if keywords:
            filters.append(News.title.contains(keywords))

        paginate = News.query.filter(*filters).order_by(News.create_time.desc()).paginate(p, constants.ADMIN_NEWS_PAGE_MAX_COUNT, False)

        news_items = paginate.items

        current_page = paginate.page

        total_page = paginate.pages

    except Exception as e:
        current_app.logger.error(e)

    news_dict = [news.to_basic_dict() for news in news_items]

    data = {
        'news': news_dict,
        'current_page': current_page,
        'total_page': total_page
    }

    return render_template('admin/news_edit.html', data=data)


@admin_bp.route('/news_edit_detail', methods=['POST', 'GET'])
def news_edit_detail():

    if request.method == 'GET':

        news_id =request.args.get('news_id')

        if not news_id:
            return render_template('admin/news_edit_detail.html', data={"errmsg": "未查询到此新闻"})

        news = None

        try:
            news = News.query.get(news_id)
        except Exception as e:
            current_app.logger.error(e)

        if not news:
            return render_template('admin/news_edit_detail.html', data={"errmsg": "未查询到此新闻"})

        categories = Category.query.all()

        categories_list = []

        for category in categories:
            category_dict = category.to_dict()
            category_dict['is_selected'] = False
            if news.category_id == category.id:
                category_dict['is_selected'] = True
            categories_list.append(category_dict)

        categories_list.pop(0)

        data = {
            'news': news.to_dict(),
            'categories': categories_list
        }

        return render_template('admin/news_edit_detail.html', data=data)

    else:
        news_id = request.form.get("news_id")
        title = request.form.get("title")
        digest = request.form.get("digest")
        content = request.form.get("content")
        index_image = request.files.get("index_image")
        category_id = request.form.get("category_id")
        # 1.1 判断数据是否有值
        if not all([title, digest, content, category_id]):
            return jsonify(errno=RET.PARAMERR, errmsg="参数有误")

        news = None
        try:
            news = News.query.get(news_id)
        except Exception as e:
            current_app.logger.error(e)
        if not news:
            return jsonify(errno=RET.NODATA, errmsg="未查询到新闻数据")

        # 1.2 尝试读取图片
        if index_image:
            try:
                index_image = index_image.read()
            except Exception as e:
                current_app.logger.error(e)
                return jsonify(errno=RET.PARAMERR, errmsg="参数有误")

            # 2. 将标题图片上传到七牛
            try:
                key = upload_img(index_image)
            except Exception as e:
                current_app.logger.error(e)
                return jsonify(errno=RET.THIRDERR, errmsg="上传图片错误")
            news.index_image_url = constants.QINIU_DOMIN_PREFIX + key
        # 3. 设置相关数据
        news.title = title
        news.digest = digest
        news.content = content
        news.category_id = category_id

        # 4. 保存到数据库
        try:
            db.session.commit()
        except Exception as e:
            current_app.logger.error(e)
            db.session.rollback()
            return jsonify(errno=RET.DBERR, errmsg="保存数据失败")
        # 5. 返回结果
        return jsonify(errno=RET.OK, errmsg="编辑成功")


@admin_bp.route('/news_category')
def news_category():

    categories = None

    try:
        categories = Category.query.all()
    except Exception as e:
        current_app.logger.error(e)

    categories_dicts = [category.to_dict() for category in categories]

    categories_dicts.pop(0)

    data = {"categories": categories_dicts}

    return render_template('admin/news_type.html', data=data)


@admin_bp.route('/add_category', methods=["POST"])
def add_category():
    category_id = request.json.get("id")
    category_name = request.json.get("name")
    if not category_name:
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")
    # 判断是否有分类id
    if category_id:
        try:
            category = Category.query.get(category_id)
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.DBERR, errmsg="查询数据失败")

        if not category:
            return jsonify(errno=RET.NODATA, errmsg="未查询到分类信息")

        category.name = category_name
    else:
        # 如果没有分类id，则是添加分类
        category = Category()
        category.name = category_name
        db.session.add(category)

    try:
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg="保存数据失败")
    return jsonify(errno=RET.OK, errmsg="保存数据成功")