# 1.导入蓝图类
from flask import Blueprint

passport_bp = Blueprint('passport', __name__, url_prefix='/passport')

from .views import *