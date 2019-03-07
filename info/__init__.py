# 业务文件夹
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from redis import StrictRedis
from flask_wtf import CSRFProtect
from flask_session import Session
from config import config_dict

# 当APP对象为空的情况,并没有真正做数据库初始化操作
db = SQLAlchemy()

# redis数据库对象
# 声明数据类型
redis_store = None  # type:StrictRedis


def create_app(config_name):
    # 初始化APP对象
    app = Flask(__name__)

    # 获取项目配置类
    config_class = config_dict[config_name]

    # 加载项目配置类
    app.config.from_object(config_class)

    # 懒加载,延迟初始化db对象
    db.init_app(app)

    # 创建redis数据库对象
    global redis_store
    redis_store = StrictRedis(host=config_class.REDIS_HOST, port=config_class.REDIS_PORT, decode_responses=True)

    # 设置CSRF保护
    CSRFProtect(app)

    # 设置session保存在redis里面
    Session(app)

    return app







