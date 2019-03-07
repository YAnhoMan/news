from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from redis import StrictRedis
from flask_wtf import CSRFProtect
from flask_session import Session
from flask_script import Manager
from flask_migrate import Migrate,MigrateCommand
import pymysql

pymysql.install_as_MySQLdb()

class Config(object):
    # 开启debug模式
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
    SQLAlCHEMY_TRACK_MODIFICATIONS = False


# 初始化APP对象
app = Flask(__name__)
#加载配置类
app.config.from_object(Config)

# 设置CSRF保护
CSRFProtect(app)

# 设置session保存在redis里面
Session(app)

# 设置管理对象
manager = Manager(app)

# 加入管理命令行
manager.add_command('db', MigrateCommand)


# 创建mysql数据库对象
db = SQLAlchemy(app)

# 创建redis数据库对象
redis_store = StrictRedis(host=Config.REDIS_HOST, port=Config.REDIS_PORT, decode_responses=True)


@app.route('/')
def index():
    return "index"


if __name__ == '__main__':
    app.run(debug=True)


