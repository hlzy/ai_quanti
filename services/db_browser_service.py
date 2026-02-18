"""
数据库浏览服务
提供数据库表结构和数据查询功能
"""
from database import db_manager


class DatabaseBrowserService:
    """数据库浏览服务"""
    
    def get_all_tables(self):
        """获取所有表信息"""
        query = """
        SELECT name, sql 
        FROM sqlite_master 
        WHERE type='table' AND name NOT LIKE 'sqlite_%'
        ORDER BY name
        """
        tables = db_manager.execute_query(query)
        
        # 为每个表添加记录数
        table_list = []
        for table in tables:
            count_query = f"SELECT COUNT(*) as count FROM {table['name']}"
            count_result = db_manager.execute_query(count_query, fetch_one=True)
            table_list.append({
                'name': table['name'],
                'sql': table['sql'],
                'row_count': count_result['count'] if count_result else 0
            })
        
        return table_list
    
    def get_table_structure(self, table_name):
        """获取表结构"""
        query = f"PRAGMA table_info({table_name})"
        return db_manager.execute_query(query)
    
    def get_table_data(self, table_name, limit=100, offset=0, order_by=None):
        """获取表数据
        
        Args:
            table_name: 表名
            limit: 返回记录数
            offset: 偏移量
            order_by: 排序字段（如 'id DESC'）
        """
        # 构建查询
        query = f"SELECT * FROM {table_name}"
        
        # 添加排序
        if order_by:
            query += f" ORDER BY {order_by}"
        else:
            # 默认按id降序（最新记录在前）
            query += " ORDER BY id DESC"
        
        # 添加分页
        query += f" LIMIT {limit} OFFSET {offset}"
        
        return db_manager.execute_query(query)
    
    def get_table_count(self, table_name):
        """获取表记录总数"""
        query = f"SELECT COUNT(*) as count FROM {table_name}"
        result = db_manager.execute_query(query, fetch_one=True)
        return result['count'] if result else 0
    
    def execute_custom_query(self, query):
        """执行自定义查询（仅限SELECT）"""
        # 安全检查：只允许SELECT查询
        query_upper = query.strip().upper()
        if not query_upper.startswith('SELECT'):
            raise ValueError('只允许执行SELECT查询')
        
        # 禁止危险操作
        dangerous_keywords = ['DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER', 'CREATE']
        for keyword in dangerous_keywords:
            if keyword in query_upper:
                raise ValueError(f'查询中不允许包含 {keyword} 操作')
        
        return db_manager.execute_query(query)
    
    def get_table_indexes(self, table_name):
        """获取表的索引信息"""
        query = f"""
        SELECT name, sql 
        FROM sqlite_master 
        WHERE type='index' AND tbl_name='{table_name}'
        """
        return db_manager.execute_query(query)
    
    def get_database_stats(self):
        """获取数据库统计信息"""
        tables = self.get_all_tables()
        
        stats = {
            'total_tables': len(tables),
            'total_rows': sum(t['row_count'] for t in tables),
            'tables': []
        }
        
        # 计算每个表的详细信息
        for table in tables:
            table_info = {
                'name': table['name'],
                'row_count': table['row_count'],
                'indexes': len(self.get_table_indexes(table['name']))
            }
            stats['tables'].append(table_info)
        
        return stats


# 创建全局实例
db_browser_service = DatabaseBrowserService()
