from flask import request, abort, make_response
from info.utils.captcha.captcha import captcha
from info import redis_store
from info import constants

from . import passport_bp

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