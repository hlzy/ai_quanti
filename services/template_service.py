"""
初始对话模版服务
"""
from database import db_manager


class TemplateService:
    """对话模版服务类"""
    
    def get_all_templates(self):
        """获取所有模版"""
        query = "SELECT * FROM chat_templates ORDER BY id"
        return db_manager.execute_query(query)
    
    def get_template(self, template_id):
        """获取单个模版"""
        query = "SELECT * FROM chat_templates WHERE id = %s"
        return db_manager.execute_query(query, (template_id,), fetch_one=True)
    
    def create_template(self, name, content):
        """创建模版"""
        query = """
        INSERT INTO chat_templates (name, content)
        VALUES (%s, %s)
        """
        return db_manager.execute_update(query, (name, content))
    
    def update_template(self, template_id, name, content):
        """更新模版"""
        query = """
        UPDATE chat_templates
        SET name = %s, content = %s
        WHERE id = %s
        """
        return db_manager.execute_update(query, (name, content, template_id))
    
    def delete_template(self, template_id):
        """删除模版"""
        query = "DELETE FROM chat_templates WHERE id = %s"
        return db_manager.execute_update(query, (template_id,))


# 创建全局模版服务实例
template_service = TemplateService()
