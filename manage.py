
from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand
import pymysql
from info import create_app, db, redis_store
from info.models import *
pymysql.install_as_MySQLdb()

"""
manager文件只去实现项目的启动和数据库的迁移,其他项目配置,app应用相关都应该抽取到专门的文件中
"""

# 传入'development'就是开发环境
# 传入'prodution'就是生产环境
app = create_app('development')

# 使得数据库具备迁移能力
Migrate(app, db)

# 设置管理对象
manager = Manager(app)

# 加入管理命令行
manager.add_command('db', MigrateCommand)

# 装饰器定义的是创建管理员的命令行选项,以及对于的字段
@manager.option('-n', '-name', dest='name')
@manager.option('-p', '-password', dest='password')
def createsuperuser(name, password):
    """创建管理员用户"""
    if not all([name, password]):
        print('参数不足')
        return

    user = User()
    user.mobile = name
    user.nick_name = name
    user.password = password
    user.is_admin = True

    try:
        db.session.add(user)
        db.session.commit()
        print("创建成功")
    except Exception as e:
        print(e)
        db.session.rollback()




if __name__ == '__main__':
    manager.run()



