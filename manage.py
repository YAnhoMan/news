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



if __name__ == '__main__':
    manager.run()


