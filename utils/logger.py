"""
日志管理模块
"""
import logging
import os
from datetime import datetime
from pathlib import Path


class LoggerManager:
    """日志管理器"""
    
    _loggers = {}
    
    @classmethod
    def get_logger(cls, name, log_dir='log'):
        """获取或创建logger
        
        Args:
            name: logger名称
            log_dir: 日志目录
            
        Returns:
            logging.Logger对象
        """
        if name in cls._loggers:
            return cls._loggers[name]
        
        # 创建日志目录
        log_path = Path(log_dir)
        log_path.mkdir(parents=True, exist_ok=True)
        
        # 创建logger
        logger = logging.getLogger(name)
        logger.setLevel(logging.DEBUG)
        
        # 避免重复添加handler
        if logger.handlers:
            return logger
        
        # 文件handler - 按日期分割
        today = datetime.now().strftime('%Y-%m-%d')
        file_handler = logging.FileHandler(
            log_path / f'{name}_{today}.log',
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        
        # 控制台handler - 只显示WARNING及以上
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.WARNING)
        
        # 格式化
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # 添加handlers
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        cls._loggers[name] = logger
        return logger


# 预定义常用logger
stock_logger = LoggerManager.get_logger('stock_service')
ai_logger = LoggerManager.get_logger('ai_service')
position_logger = LoggerManager.get_logger('position_service')
watchlist_logger = LoggerManager.get_logger('watchlist_service')
app_logger = LoggerManager.get_logger('app')
