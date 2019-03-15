from info import user_login_data, db
from info.constants import QINIU_DOMIN_PREFIX
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