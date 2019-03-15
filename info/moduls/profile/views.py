from info import user_login_data, db, constants
from info.constants import QINIU_DOMIN_PREFIX
from info.models import Category, News
from info.moduls.profile import profile_bp
from flask import render_template, redirect, g, request, jsonify, current_app, session

from info.response_code import RET
from info.utils.image_storage import upload_img


@profile_bp.route('/info')
@user_login_data
def get_user_info():

    if not g.user:
        # 用户未登录，重定向到主页
        return redirect('/')
    data = {
        "user_info": g.user_info,
    }
    return render_template('news/user.html', data=data)


@profile_bp.route('/user_info', methods=['POST', 'GET'])
@user_login_data
def base_info():

    if request.method == 'GET':
        return render_template('news/user_base_info.html', data={"user_info": g.user_info})

    if g.user:

        new_name = request.json.get('nick_name')

        new_signature = request.json.get('signature')

        new_gender = request.json.get('gender')

        if not all([new_name, new_signature, new_gender]):
            return jsonify(errno=RET.PARAMERR, errmsg='参数错误')

        if new_gender not in ['MAN', 'WOMAN']:
            return jsonify(errno=RET.PARAMERR, errmsg='参数错误')

        g.user.nick_name = new_name

        g.user.signature = new_signature

        g.user.gender = new_gender

        try:
            db.session.commit()
        except Exception as e:
            current_app.logger.error(e)
            db.session.rollback()
            return jsonify(errno=RET.DBERR, errmsg="保存数据失败")

        session['nick_name'] = new_name

        return jsonify(errno=RET.OK, errmsg='操作成功')

    else:
        return redirect('/')


@profile_bp.route('/pic_info', methods=['POST', 'GET'])
@user_login_data
def pic_info():
    if request.method == 'GET':
        data = {'avatar_url': g.user_info.get('avatar_ur')}
        return render_template('news/user_pic_info.html', data=data)

    if g.user:

        try:
            avatar_file = request.files.get('avatar').read()
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.PARAMERR, errmsg="读取文件失败")

        # 再将文件上传到七牛云
        if avatar_file:
            try:
                url = upload_img(avatar_file)
            except Exception as e:
                current_app.logger.error(e)
                return jsonify(errno=RET.THIRDERR, errmsg="上传图片错误")
        else:
            return jsonify(errno=RET.THIRDERR, errmsg="上传图片错误")

        g.user.avatar_url = url

        try:
            db.session.commit()
        except Exception as e:
            current_app.logger.error(e)
            db.session.rollback()
            return jsonify(errno=RET.DBERR, errmsg="保存用户头像成功")

        return jsonify(errno=RET.OK, errmsg="图片上传成功", data={'avatar_url': QINIU_DOMIN_PREFIX + url})

    else:
        return redirect('/')


@profile_bp.route('/pass_info', methods=['POST', 'GET'])
@user_login_data
def pass_info():

    if request.method == 'GET':
        return render_template('news/user_pass_info.html')

    if not g.user:
        return redirect('/')

    old_password = request.json.get('old_password')
    new_password = request.json.get('new_password')

    if not all([old_password, new_password]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    if not g.user.check_password(old_password):
        return jsonify(errno=RET.PWDERR, errmsg="旧密码错误")

    g.user.password = new_password

    try:
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg="操作失败")

    return jsonify(errno=RET.OK, errmsg="保存成功")


@profile_bp.route('/collection_info')
@user_login_data
def collection_info():

    if not g.user:
        return redirect('/')

    p = request.args.get('p', 1)


    try:
        p = int(p)
    except Exception as e:
        current_app.logger.error(e)
        p = 1

    current_pag = 1
    total_pag = 1
    try:
        pag_data = g.user.collection_news.paginate(p, constants.USER_COLLECTION_MAX_NEWS, False)

        #  获取当前页码对象
        collections = pag_data.items

        #  当前页码
        current_pag = pag_data.page

        #  全部页码
        total_pag = pag_data.pages

    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据库查询粗我")

    collections_data_list = [news.to_basic_dict() for news in collections]

    data = {
        'collections': collections_data_list,
        'current_pag': current_pag,
        'total_pag': total_pag
    }

    return render_template('news/user_collection.html', data=data)


@profile_bp.route('/news_release', methods=['POST', 'GET'])
@user_login_data
def news_release():

    if not g.user:
        return jsonify(errno=RET.SESSIONERR, errmsg="用户未登录")

    if request.method == 'GET':
        try:
            categories = Category.query.all()
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.DBERR, errmsg='查询分类失败')

        categories_list = []
        for category in categories if categories else []:
            categories_list.append(category.to_dict())

        categories_list.pop(0)

        data = {
            'categories': categories_list
        }

        return render_template('news/user_news_release.html', data=data)

    else:

        title = request.form.get('title')

        category_id = request.form.get('category_id')

        digest = request.form.get('digest')

        index_image = request.files.get('index_image')

        content = request.form.get('content')

        source ='个人发布'

        if not all([title, category_id, digest, index_image, content]):
            return jsonify(errno=RET.PARAMERR, errmsg='参数错误')
        else:
            pass

        # 尝试读取图片

        try:
            index_image = index_image.read()
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.PARAMERR, errmsg='参数错误')

        try:
            key = upload_img(index_image)
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.THIRDERR, errmsg="上传图片错误")

        news = News()
        news.title = title
        news.source = source
        news.digest = digest
        news.index_image_url = constants.QINIU_DOMIN_PREFIX + key
        news.category_id = category_id
        news.content = content
        news.user_id = g.user_id
        news.status = 1

        try:
            db.session.add(news)
            db.session.commit()
        except Exception as e:
            current_app.logger.error(e)
            db.session.rollback()
            return jsonify(errno=RET.DBERR, errmsg="保存到数据库错误")

        return jsonify(errno=RET.OK, errmsg="发布成功，等待审核")


@profile_bp.route('/news_list')
@user_login_data
def news_list():

    if not g.user:
        return jsonify(errno=RET.SESSIONERR, errmsg="用户未登录")

    else:
        p = request.args.get('p', 1)

        try:
            p = int(p)
        except Exception as e:
            current_app.logger.error(e)
            p = 1

        news_list = []
        current_page = 1
        total_page = 1
        try:
            paginate = News.query.filter(News.user_id == g.user_id).paginate(p, constants.USER_COLLECTION_MAX_NEWS, False)

            news_list = paginate.items

            current_page = paginate.page

            total_page = paginate.pages

        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.DBERR, errmsg="查询数据库错误")

        news_dict_list = [news.to_review_dict() for news in news_list]

        data = {
            'current_page': current_page,
            'total_page': total_page,
            'news_dict_list': news_dict_list
        }

        return render_template('news/user_news_list.html', data=data)


@profile_bp.route('/user_follow', methods=['POST', 'GET'])
@user_login_data
def user_follow():

    if not g.user:
        return jsonify(errno=RET.SESSIONERR, errmsg="用户未登录")

    if request.method == "GET":


        p = request.args.get('p', 1)

        try:
            p = int(p)
        except Exception as e:
            current_app.logger.error(e)
            p = 1

        follows = []
        current_page = 1
        total_page = 1

        try:
            paginate = g.user.followed.paginate(current_page, constants.USER_FOLLOWED_MAX_COUNT, False)

            follows = paginate.items

            current_page = paginate.page

            total_page = paginate.pages

        except Exception as e:
            current_app.logger.error(e)

        user_dict_li = [user.to_dict() for user in follows]

        data = {
            'user_data': user_dict_li,
            'current_page': current_page,
            'total_page': total_page
        }

        return render_template('news/user_follow.html', data=data)


