import qiniu
import logging

access_key = 'hhMUf4l6Z1ryOK-jikMyzZJto4LMArkuOoawYX1_'
secret_key = 'Oe0yvlAY6ErO_9MEFH1zvIc-YMigw6xRcFl2gUJO'

bucket_name = 'news'


def upload_img(data):

    if not data:
        raise AttributeError('图片数据为空')

    # 七牛云进行权限校验
    q = qiniu.Auth(access_key, secret_key)

    # 上传图片名称,如果不指明,七牛云会默认分配

    # key = 'hello'

    token = q.upload_token(bucket_name)

    # 上传文件
    try:
        ret, info = qiniu.put_data(token, None, data)
    except Exception as e:
        logging.error(e)
        raise e

    if info and info.status_code != 200:
        raise Exception("上传文件到七牛失败")

    print(ret)
    print(info)

    return ret.get('key')

if __name__ == '__main__':
    file_name = input("输入上传的文件")
    with open(file_name, "rb") as f:
        upload_img(f.read())

