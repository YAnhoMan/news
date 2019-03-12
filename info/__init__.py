# 业务文件夹
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask, render_template, g
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import generate_csrf
from redis import StrictRedis
from flask_wtf import CSRFProtect
from flask_session import Session
from config import config_dict

# 当APP对象为空的情况,并没有真正做数据库初始化操作
db = SQLAlchemy()

from info.common import user_login_data

# redis数据库对象
# 声明数据类型
redis_store = None  # type:StrictRedis


# config_class配置类
def wirte_log(config_class):
    # 设置日志的记录等级
    logging.basicConfig(level=config_class.LOG_LEVEL)  # 调试debug级

    # 创建日志记录器，指明日志保存的路径、每个日志文件的最大大小100M、保存的日志文件个数上限
    file_log_handler = RotatingFileHandler("logs/log", maxBytes=1024 * 1024 * 100, backupCount=10)

    # 创建日志记录的格式 日志等级 输入日志信息的文件名 行数 日志信息
    formatter = logging.Formatter('%(levelname)s %(filename)s:%(lineno)d %(message)s')

    # 为刚创建的日志记录器设置日志记录格式
    file_log_handler.setFormatter(formatter)

    # 为全局的日志工具对象（flask app使用的）添加日志记录器
    logging.getLogger().addHandler(file_log_handler)


def create_app(config_name):
    # 初始化APP对象
    app = Flask(__name__)

    # 获取项目配置类
    config_class = config_dict[config_name]

    # 加载项目配置类
    app.config.from_object(config_class)

    # 懒加载,延迟初始化db对象
    db.init_app(app)

    #记录日志
    wirte_log(config_class)

    # 创建redis数据库对象
    global redis_store
    redis_store = StrictRedis(host=config_class.REDIS_HOST, port=config_class.REDIS_PORT, decode_responses=True)

    # 设置CSRF保护
    CSRFProtect(app)

    # 注册蓝图
    from info.moduls.index import index_bp
    from info.moduls.passport import passport_bp
    from info.moduls.news import news_bp
    app.register_blueprint(index_bp)
    app.register_blueprint(passport_bp)
    app.register_blueprint(news_bp)

    # 设置session保存在redis里面
    Session(app)

    @app.after_request
    def set_csrf_token(response):
        csrf_token = generate_csrf()
        response.set_cookie('csrf_token', csrf_token)
        return response

    @app.errorhandler(404)
    # @user_login_data
    def abort_404():
        data = {
            'user_info': g.user_info
        }
        return render_template('news/404.html', data=data)

    return app







