# 1.导入蓝图类
from flask import Blueprint

index_bp = Blueprint('index', __name__)

from .views import *


