"""
服务模块
"""
from .stock_service import stock_service
from .position_service import position_service
from .ai_service import ai_service
from .template_service import template_service

__all__ = ['stock_service', 'position_service', 'ai_service', 'template_service']
