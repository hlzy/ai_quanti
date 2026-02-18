"""
AI服务模块 - 通义千问API集成
"""
import requests
import json
import os
import re
from datetime import datetime
from config import config
from database import db_manager


class AIService:
    """AI服务类 - 使用通义千问API"""
    
    def __init__(self):
        self.api_key = config.QWEN_API_KEY
        self.api_url = config.QWEN_API_URL
        self.model = config.QWEN_MODEL
        self.prompt_history_dir = os.path.join(config.BASE_DIR, 'prompt_history')
        
        # 确保prompt_history目录存在
        os.makedirs(self.prompt_history_dir, exist_ok=True)
        
        if not self.api_key:
            raise ValueError("通义千问API Key未配置，请在.env文件中设置QWEN_API_KEY")
    
    def chat(self, messages, temperature=0.7, max_tokens=2000):
        """调用通义千问API进行对话"""
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_key}'
        }
        
        payload = {
            'model': self.model,
            'input': {
                'messages': messages
            },
            'parameters': {
                'result_format': 'message',  # 必须！指定返回格式
                'temperature': temperature,
                'max_tokens': max_tokens,
                'top_p': 0.8
            }
        }
        
        try:
            response = requests.post(self.api_url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            
            # 打印调试信息
            print(f"API响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
            
            # 解析响应
            if result.get('output') and result['output'].get('choices'):
                return result['output']['choices'][0]['message']['content']
            else:
                error_msg = result.get('message', 'AI响应格式错误')
                print(f"API响应格式异常: {error_msg}")
                return f"AI响应错误: {error_msg}"
        except requests.exceptions.RequestException as e:
            print(f"API调用失败: {e}")
            import traceback
            traceback.print_exc()
            return f"AI服务暂时不可用: {str(e)}"
    
    def analyze_stock(self, stock_code, stock_name, stock_data, indicators, user_message=None):
        """分析股票数据并生成交易策略"""
        # 构建系统提示
        system_prompt = """你是一位专业的量化交易分析师，擅长技术分析和交易策略制定。
请基于提供的股票K线数据和技术指标，进行深入分析并给出交易建议。

分析要点：
1. 趋势分析：基于K线形态和均线系统判断当前趋势
2. 技术指标分析：MACD、RSI等指标的信号解读
3. 支撑位和阻力位分析
4. 交易建议：买入、卖出或持有，并给出理由和目标价位
5. 风险提示

请用专业但易懂的语言进行分析。"""
        
        # 构建股票数据上下文
        recent_data = stock_data[-10:] if len(stock_data) > 10 else stock_data
        recent_indicators = indicators[-10:] if len(indicators) > 10 else indicators
        
        data_context = f"""
股票代码: {stock_code}
股票名称: {stock_name}

最近10个交易日K线数据:
"""
        for d in recent_data:
            data_context += f"\n日期: {d['trade_date']}, 开: {d['open']}, 高: {d['high']}, 低: {d['low']}, 收: {d['close']}, 量: {d['volume']}"
        
        data_context += "\n\n最近10个交易日技术指标:"
        for ind in recent_indicators:
            data_context += f"\n日期: {ind['trade_date']}, MACD: {ind['macd']:.4f}, Signal: {ind['macd_signal']:.4f}, RSI(6): {ind['rsi_6']:.2f}, RSI(12): {ind['rsi_12']:.2f}"
        
        # 构建消息
        messages = [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': data_context}
        ]
        
        if user_message:
            messages.append({'role': 'user', 'content': user_message})
        
        # 调用AI
        response = self.chat(messages, temperature=0.7, max_tokens=2000)
        return response
    
    def save_chat_history(self, stock_code, role, content):
        """保存聊天记录"""
        query = """
        INSERT INTO chat_history (stock_code, role, content)
        VALUES (%s, %s, %s)
        """
        return db_manager.execute_update(query, (stock_code, role, content))
    
    def get_chat_history(self, stock_code, limit=50):
        """获取聊天记录"""
        query = """
        SELECT * FROM chat_history
        WHERE stock_code = %s
        ORDER BY created_at DESC
        LIMIT %s
        """
        history = db_manager.execute_query(query, (stock_code, limit))
        return list(reversed(history))
    
    def clear_chat_history(self, stock_code):
        """清除聊天记录，并增加历史索引"""
        # 删除数据库记录
        query = "DELETE FROM chat_history WHERE stock_code = %s"
        result = db_manager.execute_update(query, (stock_code,))
        
        # 增加文件历史索引
        stock_dir = os.path.join(self.prompt_history_dir, stock_code)
        if os.path.exists(stock_dir):
            current_index = self._get_history_index(stock_code)
            # 创建新的空文件，index+1
            new_index = current_index + 1
            new_filename = os.path.join(stock_dir, f'history_{new_index}.md')
            
            timestamp = datetime.now().strftime('%Y/%m/%d %H:%M:%S')
            with open(new_filename, 'w', encoding='utf-8') as f:
                f.write(f"""# 对话历史 - {stock_code}

**创建时间**: {timestamp}
**历史索引**: {new_index}

---

*对话记录已清除，开始新的对话轮次*

""")
            print(f"✅ 历史索引已更新: {stock_code} -> history_{new_index}.md")
        
        return result
    
    def save_strategy(self, stock_code, stock_name, analysis_result, indicators_summary):
        """保存交易策略到文件"""
        today = datetime.now().strftime('%Y-%m-%d')
        filename = f"{config.STRATEGY_DIR}/策略_{stock_code}_{today}.md"
        
        content = f"""# 交易策略报告

**股票代码**: {stock_code}
**股票名称**: {stock_name}
**分析日期**: {today}

## 技术指标概况

{indicators_summary}

## AI分析结果

{analysis_result}

---
*本报告由AI量化分析系统自动生成*
"""
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(content)
            return filename
        except Exception as e:
            print(f"保存策略文件失败: {e}")
            return None
    
    def _get_history_index(self, stock_code):
        """获取当前股票的历史记录索引"""
        stock_dir = os.path.join(self.prompt_history_dir, stock_code)
        if not os.path.exists(stock_dir):
            return 1
        
        # 查找最大的index
        max_index = 0
        for filename in os.listdir(stock_dir):
            if filename.startswith('history_') and filename.endswith('.md'):
                try:
                    index = int(filename.replace('history_', '').replace('.md', ''))
                    max_index = max(max_index, index)
                except ValueError:
                    continue
        
        return max_index if max_index > 0 else 1
    
    def _format_kline_data(self, data_list, columns=['trade_date', 'open', 'close', 'high', 'low', 'volume']):
        """格式化K线数据为表格字符串"""
        if not data_list:
            return "暂无数据"
        
        # 表头
        headers = {
            'trade_date': '日期',
            'open': '开盘',
            'close': '收盘',
            'high': '最高',
            'low': '最低',
            'volume': '成交量'
        }
        
        result = '\t'.join([headers.get(col, col) for col in columns]) + '\n'
        
        # 数据行
        for data in data_list:
            row = []
            for col in columns:
                value = data.get(col, '-')
                # 格式化数字
                if isinstance(value, (int, float)):
                    if col == 'volume':
                        row.append(f"{int(value):,}")
                    else:
                        row.append(f"{float(value):.2f}")
                else:
                    row.append(str(value))
            result += '\t'.join(row) + '\n'
        
        return result
    
    def _format_macd_data(self, indicators):
        """格式化MACD数据为表格字符串"""
        if not indicators:
            return "暂无数据"
        
        result = "日期\tMACD\tMACD信号线\tMACD柱\tRSI(6)\tRSI(12)\n"
        
        for ind in indicators:
            result += f"{ind.get('trade_date', '-')}\t"
            result += f"{ind.get('macd', 0):.4f}\t"
            result += f"{ind.get('macd_signal', 0):.4f}\t"
            result += f"{ind.get('macd_hist', 0):.4f}\t"
            result += f"{ind.get('rsi_6', 0):.2f}\t"
            result += f"{ind.get('rsi_12', 0):.2f}\n"
        
        return result
    
    def _replace_variables(self, stock_code, message):
        """替换消息中的变量占位符
        
        支持的变量：
        - {日K} - 60天日K线数据
        - {周K} - 60周周K线数据
        - {1分钟K} - 1分钟K线数据（暂不支持）
        - {MACD_日K} - 日K的MACD数据
        """
        from services.stock_service import stock_service
        
        replaced_message = message
        variables_used = {}
        
        # 检查并替换 {日K}
        if '{日K}' in message:
            daily_data = stock_service.get_stock_data_from_db(stock_code, 'daily', days=60)
            if daily_data:
                kline_str = self._format_kline_data(daily_data)
                replaced_message = replaced_message.replace('{日K}', f'\n"""\n{kline_str}"""')
                variables_used['日K'] = kline_str
            else:
                replaced_message = replaced_message.replace('{日K}', '[暂无日K数据]')
        
        # 检查并替换 {周K}
        if '{周K}' in message:
            weekly_data = stock_service.get_stock_data_from_db(stock_code, 'weekly', days=60)
            if weekly_data:
                kline_str = self._format_kline_data(weekly_data)
                replaced_message = replaced_message.replace('{周K}', f'\n"""\n{kline_str}"""')
                variables_used['周K'] = kline_str
            else:
                replaced_message = replaced_message.replace('{周K}', '[暂无周K数据]')
        
        # 检查并替换 {MACD_日K}
        if '{MACD_日K}' in message:
            indicators = stock_service.get_indicators_from_db(stock_code, days=60)
            if indicators:
                macd_str = self._format_macd_data(indicators)
                replaced_message = replaced_message.replace('{MACD_日K}', f'\n"""\n{macd_str}"""')
                variables_used['MACD_日K'] = macd_str
            else:
                replaced_message = replaced_message.replace('{MACD_日K}', '[暂无MACD数据]')
        
        # 检查并替换 {1分钟K}（暂不支持）
        if '{1分钟K}' in message:
            replaced_message = replaced_message.replace('{1分钟K}', '[1分钟K线数据暂不支持]')
        
        return replaced_message, variables_used
    
    def _save_prompt_history(self, stock_code, user_message, ai_response, replaced_message):
        """保存Prompt历史到文件"""
        try:
            # 获取或创建股票目录
            stock_dir = os.path.join(self.prompt_history_dir, stock_code)
            os.makedirs(stock_dir, exist_ok=True)
            
            # 获取当前index
            index = self._get_history_index(stock_code)
            filename = os.path.join(stock_dir, f'history_{index}.md')
            
            # 构建内容
            timestamp = datetime.now().strftime('%Y/%m/%d %H:%M:%S')
            
            content = f"""# 对话历史 - {stock_code}

**时间**: {timestamp}
**历史索引**: {index}

---

## 用户输入（原始）

{user_message}

---

## 用户输入（变量替换后）

{replaced_message}

---

## AI回复

{ai_response}

---

*本文件由AI量化分析系统自动生成*
"""
            
            # 追加或创建文件
            mode = 'a' if os.path.exists(filename) else 'w'
            with open(filename, mode, encoding='utf-8') as f:
                if mode == 'a':
                    f.write('\n\n' + '='*80 + '\n\n')
                f.write(content)
            
            print(f"✅ Prompt历史已保存: {filename}")
            return filename
            
        except Exception as e:
            print(f"❌ 保存Prompt历史失败: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def chat_with_history(self, stock_code, user_message):
        """带历史记录的对话（支持变量替换和Prompt日志）"""
        # 1. 替换变量
        replaced_message, variables_used = self._replace_variables(stock_code, user_message)
        
        print(f"\n📝 用户输入: {user_message}")
        if variables_used:
            print(f"🔄 变量替换: {list(variables_used.keys())}")
        
        # 2. 获取历史记录
        history = self.get_chat_history(stock_code, limit=10)
        
        # 3. 构建消息列表
        messages = [
            {'role': 'system', 'content': '你是一位专业的股票分析助手，请基于历史对话和用户问题提供分析建议。'}
        ]
        
        for h in history:
            messages.append({
                'role': h['role'],
                'content': h['content']
            })
        
        # 使用替换后的消息
        messages.append({
            'role': 'user',
            'content': replaced_message
        })
        
        # 4. 调用AI
        response = self.chat(messages)
        
        # 5. 保存对话记录到数据库（保存原始消息）
        self.save_chat_history(stock_code, 'user', user_message)
        self.save_chat_history(stock_code, 'assistant', response)
        
        # 6. 保存Prompt历史到文件（保存替换后的完整内容）
        self._save_prompt_history(stock_code, user_message, response, replaced_message)
        
        return response
        return response


# 创建全局AI服务实例
ai_service = AIService()
