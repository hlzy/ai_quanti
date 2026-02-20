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
from utils.logger import ai_logger


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
        ai_logger.debug(f"调用AI API, 消息数: {len(messages)}, temperature: {temperature}")
        
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
                ai_logger.info(f"AI响应成功, tokens: {result.get('usage', {})}")
                return result['output']['choices'][0]['message']['content']
            else:
                error_msg = result.get('message', 'AI响应格式错误')
                ai_logger.error(f"API响应格式异常: {error_msg}")
                print(f"API响应格式异常: {error_msg}")
                return f"AI响应错误: {error_msg}"
        except requests.exceptions.RequestException as e:
            ai_logger.error(f"API调用失败: {e}", exc_info=True)
            print(f"API调用失败: {e}")
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
    
    def save_chat_history(self, user_id, stock_code, role, content):
        """保存聊天记录"""
        query = """
        INSERT INTO chat_history (user_id, stock_code, role, content)
        VALUES (%s, %s, %s, %s)
        """
        return db_manager.execute_update(query, (user_id, stock_code, role, content))
    
    def get_chat_history(self, user_id, stock_code, limit=50):
        """获取聊天记录"""
        query = """
        SELECT * FROM chat_history
        WHERE user_id = %s AND stock_code = %s
        ORDER BY created_at DESC
        LIMIT %s
        """
        history = db_manager.execute_query(query, (user_id, stock_code, limit))
        return list(reversed(history))
    
    def clear_chat_history(self, user_id, username, stock_code):
        """清除聊天记录，并增加历史索引"""
        # 删除数据库记录
        query = "DELETE FROM chat_history WHERE user_id = %s AND stock_code = %s"
        result = db_manager.execute_update(query, (user_id, stock_code))
        
        # 增加文件历史索引
        user_dir = os.path.join(self.prompt_history_dir, username)
        stock_dir = os.path.join(user_dir, stock_code)
        if os.path.exists(stock_dir):
            current_index = self._get_history_index(username, stock_code)
            # 创建新的空文件，index+1
            new_index = current_index + 1
            new_filename = os.path.join(stock_dir, f'history_{new_index}.md')
            
            timestamp = datetime.now().strftime('%Y/%m/%d %H:%M:%S')
            with open(new_filename, 'w', encoding='utf-8') as f:
                f.write(f"""# 对话历史 - {stock_code}

**创建时间**: {timestamp}
**历史索引**: {new_index}
**用户**: {username}

---

*对话记录已清除，开始新的对话轮次*

""")
            print(f"✅ 历史索引已更新: {username}/{stock_code} -> history_{new_index}.md")
        
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
    
    def _get_history_index(self, username, stock_code):
        """获取当前股票的历史记录索引"""
        user_dir = os.path.join(self.prompt_history_dir, username)
        stock_dir = os.path.join(user_dir, stock_code)
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
        
        result = "日期\tMACD\tMACD信号线\tMACD柱\n"
        
        for ind in indicators:
            result += f"{ind.get('trade_date', '-')}\t"
            result += f"{ind.get('macd', 0):.4f}\t"
            result += f"{ind.get('macd_signal', 0):.4f}\t"
            result += f"{ind.get('macd_hist', 0):.4f}\n"
        
        return result
    
    def _format_ema_data(self, indicators):
        """格式化EMA数据为表格字符串"""
        if not indicators:
            return "暂无数据"
        
        result = "日期\tEMA(12)\tEMA(26)\n"
        
        for ind in indicators:
            result += f"{ind.get('trade_date', '-')}\t"
            result += f"{ind.get('ema_12', 0):.2f}\t"
            result += f"{ind.get('ema_26', 0):.2f}\n"
        
        return result
    
    def _format_rsi_data(self, indicators):
        """格式化RSI数据为表格字符串"""
        if not indicators:
            return "暂无数据"
        
        result = "日期\tRSI(6)\tRSI(12)\tRSI(24)\n"
        
        for ind in indicators:
            result += f"{ind.get('trade_date', '-')}\t"
            result += f"{ind.get('rsi_6', 0):.2f}\t"
            result += f"{ind.get('rsi_12', 0):.2f}\t"
            result += f"{ind.get('rsi_24', 0):.2f}\n"
        
        return result
    
    def _format_positions_data(self, user_id, positions_summary):
        """格式化持仓数据为表格字符串"""
        if not positions_summary or not positions_summary.get('positions'):
            return "暂无持仓"
        
        positions = positions_summary['positions']
        result = "股票代码\t股票名称\t持仓数量\t成本价\t当前价\t市值\t盈亏金额\t盈亏比例\n"
        
        for pos in positions:
            current_price = pos.get('current_price') or pos.get('cost_price', 0)
            market_value = current_price * pos.get('quantity', 0)
            profit_loss = pos.get('profit_loss') or 0
            profit_loss_pct = pos.get('profit_loss_pct') or 0
            
            result += f"{pos.get('stock_code', '-')}\t"
            result += f"{pos.get('stock_name', '-')}\t"
            result += f"{pos.get('quantity', 0):,}\t"
            result += f"{pos.get('cost_price', 0):.2f}\t"
            result += f"{current_price:.2f}\t"
            result += f"{market_value:,.2f}\t"
            result += f"{profit_loss:,.2f}\t"
            result += f"{profit_loss_pct:.2f}%\n"
        
        # 添加汇总信息
        result += "\n--- 汇总 ---\n"
        result += f"持仓数量: {positions_summary.get('positions_count', 0)} 只\n"
        result += f"总市值: {positions_summary.get('total_market_value', 0):,.2f}\n"
        result += f"总成本: {positions_summary.get('total_cost', 0):,.2f}\n"
        result += f"总盈亏: {positions_summary.get('total_profit_loss', 0):,.2f}\n"
        
        return result
    
    def _format_cash_data(self, cash_balance):
        """格式化可用资金数据"""
        return f"可用资金: {cash_balance:,.2f} 元"
    
    def _replace_variables(self, user_id, stock_code, message):
        """替换消息中的变量占位符
        
        支持的变量格式：
        1. K线类型_股票_窗口_指标
           - K线类型（必填）：1分钟K、日K、周K
           - 股票（选填）：股票代码或名称，空则使用当前股票
           - 窗口（选填）：如"30天"、"360天"，空则使用默认值
           - 指标（选填）：如"MACD"、"EMA"、"MACD&EMA"等
        
        2. 持仓 - 获取所有持仓信息
        3. 可用资金 - 获取现金余额
        
        示例：
        - 日K_复旦微电_30天_MACD&EMA
        - 周K__360天_RSI
        - 1分钟K
        - 持仓
        - 可用资金
        """
        from services.stock_service import stock_service
        from services.position_service import position_service
        import re
        
        replaced_message = message
        variables_used = {}
        
        # 定义已知的技术指标
        KNOWN_INDICATORS = {'MACD', 'EMA', 'RSI', 'KDJ', 'BOLL', 'MA', 'VOL'}
        
        # 正则匹配变量格式：K线类型_股票_窗口_指标
        # 匹配整个变量字符串（排除花括号和空白符）
        pattern = r'(1分钟K|日K|周K)(?:(?:_[^_\s\n{}]+)+)?'
        
        matches = re.finditer(pattern, message)
        
        for match in matches:
            full_match = match.group(0)
            parts = full_match.split('_')
            
            kline_type = parts[0]  # K线类型
            
            # 解析剩余部分
            target_stock = None
            window_str = None
            indicators_str = None
            
            if len(parts) > 1:
                # 从后向前解析，优先识别"窗口"和"指标"
                remaining_parts = parts[1:]
                
                # 检查是否有指标（最后一部分，且匹配已知指标）
                if remaining_parts:
                    last_part = remaining_parts[-1]
                    # 支持多个指标，用&连接，如 "EMA&RSI"
                    indicators_in_last = [ind.strip() for ind in last_part.split('&')]
                    # 如果所有部分都是已知指标，则认为是指标
                    if all(ind in KNOWN_INDICATORS for ind in indicators_in_last):
                        indicators_str = last_part
                        remaining_parts = remaining_parts[:-1]
                
                # 检查是否有窗口（\d+天格式）
                if remaining_parts and re.match(r'^\d+天$', remaining_parts[-1]):
                    window_str = remaining_parts[-1]
                    remaining_parts = remaining_parts[:-1]
                
                # 剩余的就是股票代码/名称
                if remaining_parts:
                    target_stock = '_'.join(remaining_parts)  # 可能包含下划线的股票名
            
            # 确定使用的股票代码
            if target_stock:
                # 如果提供了股票名称/代码，需要查询
                info = stock_service.get_stock_info(target_stock)
                if info:
                    use_stock_code = info['ts_code']
                else:
                    replaced_message = replaced_message.replace(full_match, f'[股票"{target_stock}"不存在]')
                    continue
            else:
                # 使用当前股票
                use_stock_code = stock_code
            
            # 解析窗口（天数）
            if window_str:
                window_days = int(window_str.replace('天', ''))
            else:
                # 默认窗口
                if kline_type == '日K':
                    window_days = 60
                elif kline_type == '周K':
                    window_days = 360
                else:  # 1分钟K
                    window_days = 1440  # 2天的分钟数
            
            # 解析指标
            indicators = []
            if indicators_str:
                indicators = [ind.strip() for ind in indicators_str.split('&')]
            
            # 获取K线数据
            data = None
            if kline_type == '日K':
                data = stock_service.get_stock_data_from_db(use_stock_code, 'daily', window_days)
            elif kline_type == '周K':
                data = stock_service.get_stock_data_from_db(use_stock_code, 'weekly', window_days)
            elif kline_type == '1分钟K':
                data = stock_service.get_stock_data_from_db(use_stock_code, 'minute', window_days)
            
            if not data:
                replaced_message = replaced_message.replace(full_match, f'[{full_match}：暂无数据]')
                continue
            
            # 确保数据条数不超过window_days（二次保险）
            if len(data) > window_days:
                data = data[-window_days:]
            
            # 基础K线列
            columns = ['trade_date', 'open', 'close', 'high', 'low', 'volume']
            if kline_type == '1分钟K':
                columns[0] = 'trade_time'
            
            # 格式化K线数据
            kline_str = self._format_kline_data(data, columns)
            
            # 如果需要指标数据
            indicator_str = ''
            if indicators:
                indicator_data = None
                
                # 只支持日K的指标
                if kline_type == '日K':
                    indicator_data = stock_service.get_indicators_from_db(use_stock_code, window_days)
                    
                    # 确保指标数据条数不超过window_days（二次保险）
                    if indicator_data and len(indicator_data) > window_days:
                        indicator_data = indicator_data[-window_days:]
                
                if indicator_data:
                    # 根据指标类型格式化
                    if 'MACD' in indicators:
                        indicator_str += '\n\nMACD指标:\n'
                        indicator_str += self._format_macd_data(indicator_data)
                    
                    if 'EMA' in indicators:
                        indicator_str += '\n\nEMA指标:\n'
                        indicator_str += self._format_ema_data(indicator_data)
                    
                    if 'RSI' in indicators:
                        indicator_str += '\n\nRSI指标:\n'
                        indicator_str += self._format_rsi_data(indicator_data)
            
            # 组合结果
            result_str = f'\n"""\n{kline_str}{indicator_str}\n"""'
            replaced_message = replaced_message.replace(full_match, result_str)
            variables_used[full_match] = result_str
        
        # 处理"持仓"变量
        if '持仓' in message:
            positions_summary = position_service.get_portfolio_summary(user_id)
            positions_str = self._format_positions_data(user_id, positions_summary)
            replaced_message = replaced_message.replace('持仓', f'\n"""\n{positions_str}\n"""')
            variables_used['持仓'] = positions_str
        
        # 处理"可用资金"变量
        if '可用资金' in message:
            cash_balance = position_service.get_cash_balance(user_id)
            cash_str = self._format_cash_data(cash_balance)
            replaced_message = replaced_message.replace('可用资金', f'\n"""\n{cash_str}\n"""')
            variables_used['可用资金'] = cash_str
        
        return replaced_message, variables_used
    
    def _save_prompt_history(self, username, stock_code, user_message, ai_response, replaced_message):
        """保存Prompt历史到文件"""
        try:
            # 获取或创建用户目录
            user_dir = os.path.join(self.prompt_history_dir, username)
            os.makedirs(user_dir, exist_ok=True)
            
            # 获取或创建股票目录
            stock_dir = os.path.join(user_dir, stock_code)
            os.makedirs(stock_dir, exist_ok=True)
            
            # 获取当前index
            index = self._get_history_index(username, stock_code)
            filename = os.path.join(stock_dir, f'history_{index}.md')
            
            # 构建内容
            timestamp = datetime.now().strftime('%Y/%m/%d %H:%M:%S')
            
            content = f"""# 对话历史 - {stock_code}

**时间**: {timestamp}
**历史索引**: {index}
**用户**: {username}

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
    
    def chat_with_history(self, user_id, username, stock_code, user_message):
        """带历史记录的对话（支持变量替换和Prompt日志）"""
        # 1. 替换变量
        replaced_message, variables_used = self._replace_variables(user_id, stock_code, user_message)
        
        print(f"\n📝 用户输入: {user_message}")
        if variables_used:
            print(f"🔄 变量替换: {list(variables_used.keys())}")
        
        # 2. 获取历史记录
        history = self.get_chat_history(user_id, stock_code, limit=10)
        
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
        self.save_chat_history(user_id, stock_code, 'user', user_message)
        self.save_chat_history(user_id, stock_code, 'assistant', response)
        
        # 6. 保存Prompt历史到文件（保存替换后的完整内容）
        self._save_prompt_history(username, stock_code, user_message, response, replaced_message)
        
        return response


# 创建全局AI服务实例
ai_service = AIService()
