from redis import StrictRedis


class Config(object):

    """
    项目配置基类
    """
    # 默认开启debug模式
    DEBUG = True

    # 初始化redis配置
    REDIS_HOST ='127.0.0.1'
    REDIS_PORT = 6379

    # 设置session密钥
    SECRET_KEY = "EjpNVSNQTyGi1VvWECj9TvC/+kq3oujee2kTfQUs8yCM6xX9Yjq52v54g+HVoknA"

    # 指定 session 保存到 redis 中
    SESSION_TYPE = "redis"

    # 具体保存到哪个数据库
    SESSION_REDIS = StrictRedis(host=REDIS_HOST, port=REDIS_PORT, db=1)

    # 让 cookie 中的 session_id 被加密签名处理
    SESSION_USE_SIGNER = True

    # session 的有效期，单位是秒
    PERMANENT_SESSION_LIFETIME = 86400

    # mysql数据库相关配置
    # 连接数据库配置
    SQLALCHEMY_DATABASE_URI = 'mysql://root:123456@127.0.0.1:3306/news'

    # 关闭数据库修改跟踪
    SQLALCHEMY_TRACK_MODIFICATIONS = False


class DevelopmentConfig(Config):
    """
    开发模式的配置信息
    """
    # 开启debug模式
    DEBUG = True


class ProductionConfig(Config):
    """
    生产模式的配置信息
    """
    # 关闭debug模式
    DEBUG = False


# 提供一个接口功供外界调用
# 使用:config_dict['development']
config_dict = {
    'development': DevelopmentConfig,
    'production': ProductionConfig
}


