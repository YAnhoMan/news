import random
import re

from flask import request, abort, make_response, current_app, jsonify

from info.lib.yuntongxun.sms import CCP
from info.models import User
from info.utils.captcha.captcha import captcha
from info import redis_store
from info import constants
from info.response_code import RET

from . import passport_bp

# 参数通过请求体获得
@passport_bp.route('/sms_code',methods=['POST'])
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
    param_dict = request.json
    mobile = param_dict.get('mobile')
    image_code = param_dict.get('image_code')
    image_code_id = param_dict.get('image_code_id')

    if not all([mobile, image_code, image_code_id]):
        current_app.logger.error('参数不足')
        err_dict = {'error': RET.PARAMERR, 'errmsg': '参数不足'}
        return jsonify(err_dict)

    if not re.match(r'^1(3|4|5|7|8)\d{9}$', mobile):
        return jsonify(errno=RET.PARAMERR, errmsg='手机号码格式异常')

    try:
        real_image_code = redis_store.get('Image_Code_%s' % image_code_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='查询redis图形验证码异常')

    if real_image_code:
        redis_store.delete('Image_Code_%s' % image_code_id)
    else:
        return jsonify(errno=RET.NODATA, errmsg='图形验证码过期')

    if image_code.lowwer() != real_image_code.lowwer():
        return jsonify(errno=RET.DBERR, errmsg='查询redis图形验证码异常')

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