from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from redis import StrictRedis
from flask_wtf import CSRFProtect
import pymysql
from flask_session import Session
pymysql.install_as_MySQLdb()

class Config(object):
    # 开启debug模式
    DEBUG = True

    # 设置session密钥
    SECRET_KEY = "EjpNVSNQTyGi1VvWECj9TvC/+kq3oujee2kTfQUs8yCM6xX9Yjq52v54g+HVoknA"
    SESSION_TYPE = "redis" # 指定 session 保存到 redis 中
    SESSION_USE_SIGNER = True # 让 cookie 中的 session_id 被加密签名处理
    PERMANENT_SESSION_LIFETIME = 86400 # session 的有效期，单位是秒


    # mysql数据库相关配置
    # 连接数据库配置
    SQLALCHEMY_DATABASE_URI = 'mysql://root:123456@127.0.0.1:3306/news'
    # 关闭数据库修改跟踪
    SQLAlCHEMY_TRACK_MODIFICATIONS = False

    # 初始化redis配置
    REDIS_HOST ='127.0.0.1'
    REDIS_PORT = 6379



# 初始化APP对象
app = Flask(__name__)
#加载配置类
app.config.from_object(Config)

# 设置CSRF保护
CSRFProtect(app)

# 创建mysql数据库对象
db = SQLAlchemy(app)

# 创建redis数据库对象
redis_store = StrictRedis(host=Config.REDIS_HOST, port=Config.REDIS_PORT, decode_responses=True)


@app.route('/')
def index():
    return "index"


if __name__ == '__main__':
    app.run(debug=True)


