import datetime
import random
import re

from flask import request, abort, make_response, current_app, jsonify, session

from info.lib.yuntongxun.sms import CCP
from info.models import User
from info.utils.captcha.captcha import captcha
from info import redis_store, db
from info import constants
from info.response_code import RET

from . import passport_bp


# /passport/logout
@passport_bp.route('/logout', methods=['POST'])
def logout():
    """
       清除session中的对应登录之后保存的信息
       :return:
   """
    session.pop('user_id', None)
    session.pop('nick_name', None)
    session.pop('mobile', None)
    session.pop('is_admin', None)
    return jsonify(errno=RET.OK, errmsg="OK")

# 参数通过请求体获得
@passport_bp.route('/sms_code', methods=['POST'])
def sent_sms_code():
    """发送短信验证码后端接口"""
    """
    1.获取参数 
        1.1 mobile,image_code,image_code_id
        1.2 数据是通过json格式上传的:request.json
    2.校验参数
        2.1 非空判断
        2.2 使用正则判断手机号码格式是否正确
    3.逻辑处理
        3.1 根据image_code_id编号提取redis数据库中,真实的图形验证码real_image_code
        real_code有值:从redis数据库中删除
        real_code没有值:图形验证码过期了
        3.2 将输入的与真实验证码作校验(忽略大小写,注意redis返回的是字符串)
        3.3不相等, 就返回
        判断  手机号码是否注册    
    4.返回数据
    
    """
    # 获取参数
    param_dict = request.json
    mobile = param_dict.get('mobile')
    image_code = param_dict.get('image_code')
    image_code_id = param_dict.get('image_code_id')
    # 非空判断
    if not all([mobile, image_code, image_code_id]):
        current_app.logger.error('参数不足')
        err_dict = {'error': RET.PARAMERR, 'errmsg': '参数不足'}
        return jsonify(err_dict)

    # 判断手机号码格式
    if not re.match(r'^1(3|4|5|7|8)\d{9}$', mobile):
        return jsonify(errno=RET.PARAMERR, errmsg='手机号码格式异常')

    # 提取真实数据库的code
    try:
        real_image_code = redis_store.get('Image_Code_%s' % image_code_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='查询redis图形验证码异常')

    # 如果存在,就删除redis里面的数据
    if real_image_code:
        redis_store.delete('Image_Code_%s' % image_code_id)
    else:
        return jsonify(errno=RET.NODATA, errmsg='图形验证码过期')

    # 比对两个码
    if image_code.lower() != real_image_code.lower():
        return jsonify(errno=RET.DBERR, errmsg='请输入正确的验证码')

    # 校验该手机是否已经注册
    try:
        user = User.query.filter(User.mobile == mobile).first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='查询用户数据异常')
    if user:
        return jsonify(errno=RET.DATAEXIST, errmsg='该用户已注册')

    real_sms_code = random.randint(0, 999999)

    real_sms_code = '%06d' % real_sms_code

    try:
        result = CCP().send_template_sms(mobile, {real_sms_code, 5}, 1)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.THIRDERR, errmsg='云通信发送短信验证码异常')
    if result == -1:
        return jsonify(errno=RET.THIRDERR, errmsg='云通信发送短信验证码异常')

    redis_store.setex("SMS_CODE%s" % mobile, constants.SMS_CODE_REDIS_EXPIRES, real_sms_code)

    return jsonify(errno=RET.OK, errmsg='发送短信验证码成功')


@passport_bp.route('/image_code')
def get_image_code():
    # 获取UUid
    code_id = request.args.get('code_id')

    if not code_id:
        return abort(404)

    #获取真实值
    image_name, real_image_code, image_data = captcha.generate_captcha()

    redis_store.setex('Image_Code_%s' % code_id, constants.IMAGE_CODE_REDIS_EXPIRES, real_image_code)

    # 直接返回图片,不能兼容所有浏览器
    response = make_response(image_data)

    # 设置响应头中返回的数据格式为:png格式
    response.headers['Content-Type'] = 'png/image'

    return response


@passport_bp.route('/register', methods=["POST"])
def register():
    """
    1. 获取参数和判断是否有值
    2. 从redis中获取指定手机号对应的短信验证码的
    3. 校验验证码
    4. 初始化 user 模型，并设置数据并添加到数据库
    5. 保存当前用户的状态
    6. 返回注册的结果
    :return:
    """
    param_dict = request.json
    mobile = param_dict.get('mobile')
    sms_code = param_dict.get('sms_code')
    password = param_dict.get('password')

    if not all([mobile, sms_code, password]):
        return jsonify(errno=RET.PARAMERR, errmsg='参数不全')

    if not re.match(r'^1(3|4|5|7|8)\d{9}$', mobile):
        return jsonify(errno=RET.PARAMERR, errmsg='手机号码格式异常')

    try:
        real_sms_code = redis_store.get("SMS_CODE%s" % mobile)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='查询短信验证码异常')

    if real_sms_code:
        redis_store.delete("SMS_CODE%s" % mobile)
    else:
        return jsonify(errno=RET.NODATA, errmsg='短信验证码过期')

    if real_sms_code != sms_code:
        return jsonify(errno=RET.DBERR, errmsg='请输入正确的短信验证码')

    user = User()
    user.mobile = mobile
    user.nick_name = mobile
    user.password = password

    try:
        db.session.add(user)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(e)
        return jsonify(errno=RET.DATAERR, errmsg="数据保存错误")

    session['user_id'] = user.id
    session['nick_'] = user.nick_name
    session['mobile'] = user.mobile

    return jsonify(errno=RET.OK, errmsg="OK")


@passport_bp.route('/login', methods=["POST"])
def login():
    """
    1. 获取参数和判断是否有值
    2. 从数据库查询出指定的用户
    3. 校验密码
    4. 保存用户登录状态
    5. 返回结果
    :return:
    """
    param_dict = request.json
    mobile = param_dict.get('mobile')
    password = param_dict.get('password')

    if not all([mobile, password]):
        return jsonify(errno=RET.PARAMERR, errmsg='参数错误')

    if not re.match(r'^1(3|4|5|7|8)\d{9}$', mobile):
        return jsonify(errno=RET.PARAMERR, errmsg='手机号码格式异常')

    try:
        user = User.query.filter(User.mobile == mobile).first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='查询数据错误')

    if not user:
        return jsonify(errno=RET.USERERR, errmsg='用户不存在')

    if not user.check_password(password):
        return jsonify(errno=RET.PWDERR, errmsg='密码错误')

    session['user_id'] = user.id
    session['nick_'] = user.nick_name
    session['mobile'] = user.mobile

    # 记录用户最后一次登录时间

    try:
        user.last_login = datetime.datetime.now()
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)

    return jsonify(errno=RET.OK, errmsg="OK")