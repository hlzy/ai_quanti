"""
AI服务模块 - OpenRouter API集成
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
    """AI服务类 - 使用OpenRouter API"""
    
    def __init__(self):
        # OpenRouter配置
        self.api_key = config.OPENROUTER_API_KEY
        self.api_url = "https://openrouter.ai/api/v1/chat/completions"
        self.site_url = config.SITE_URL or "https://ai-quant.example.com"
        self.site_name = config.SITE_NAME or "AI量化股票分析工具"
        
        # 默认模型
        self.default_model = "deepseek/deepseek-chat"
        
        self.prompt_history_dir = os.path.join(config.BASE_DIR, 'prompt_history')
        
        # 确保prompt_history目录存在
        os.makedirs(self.prompt_history_dir, exist_ok=True)
        
        if not self.api_key:
            raise ValueError("OpenRouter API Key未配置，请在.env文件中设置OPENROUTER_API_KEY")
    
    def get_available_models(self):
        """获取可用的模型列表"""
        try:
            query = """
            SELECT model_id, model_name, is_enabled, display_order, supports_vision
            FROM ai_models 
            WHERE is_enabled = 1 
            ORDER BY display_order, model_id
            """
            models = db_manager.execute_query(query)
            
            if not models:
                # 如果数据库中没有配置，返回默认模型
                return [
                    {'model_id': 'deepseek/deepseek-chat', 'model_name': 'DeepSeek Chat', 'is_enabled': 1, 'display_order': 1, 'supports_vision': 0},
                    {'model_id': 'anthropic/claude-opus-4-20250514', 'model_name': 'Claude Opus 4', 'is_enabled': 1, 'display_order': 2, 'supports_vision': 1}
                ]
            
            return models
        except Exception as e:
            ai_logger.error(f"获取模型列表失败: {e}")
            # 返回默认模型
            return [
                {'model_id': 'deepseek/deepseek-chat', 'model_name': 'DeepSeek Chat', 'is_enabled': 1, 'display_order': 1, 'supports_vision': 0},
                {'model_id': 'anthropic/claude-opus-4-20250514', 'model_name': 'Claude Opus 4', 'is_enabled': 1, 'display_order': 2, 'supports_vision': 1}
            ]
    
    def check_model_supports_vision(self, model_id):
        """检查模型是否支持vision（图像输入）"""
        try:
            query = """
            SELECT supports_vision 
            FROM ai_models 
            WHERE model_id = %s AND is_enabled = 1
            """
            result = db_manager.execute_query(query, (model_id,), fetch_one=True)
            
            if result:
                return bool(result.get('supports_vision', 0))
            
            # 默认已知支持 vision 的模型
            vision_models = [
                'anthropic/claude-opus-4-20250514',
                'anthropic/claude-3.5-sonnet',
                'anthropic/claude-3-opus',
                'google/gemini-2.0-flash-exp:free',
                'google/gemini-pro-vision',
                'openai/gpt-4-vision-preview',
                'openai/gpt-4o',
                'openai/gpt-4o-mini'
            ]
            return model_id in vision_models
            
        except Exception as e:
            ai_logger.error(f"检查模型vision支持失败: {e}")
            return False
    
    def chat(self, messages, model=None, temperature=0.7, max_tokens=2000):
        """调用OpenRouter API进行对话
        
        Args:
            messages: 对话消息列表
            model: 模型ID，如果为None则使用默认模型
            temperature: 温度参数
            max_tokens: 最大token数
        """
        # 如果没有指定模型，使用默认模型
        if not model:
            model = self.default_model
        
        ai_logger.debug(f"调用OpenRouter API, 模型: {model}, 消息数: {len(messages)}, temperature: {temperature}")
        
        # 检查消息格式
        for i, msg in enumerate(messages):
            if msg.get('role') == 'user' and isinstance(msg.get('content'), list):
                print(f"🖼️ 消息 {i} 包含 vision content, 类型数: {len(msg['content'])}")
                for j, item in enumerate(msg['content']):
                    if item.get('type') == 'image_url':
                        url = item['image_url']['url']
                        print(f"   图片 {j}: {url[:100]}...")  # 只打印前100字符
        
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_key}',
            'HTTP-Referer': self.site_url
        }
        
        payload = {
            'model': model,
            'messages': messages,
            'temperature': temperature,
            'max_tokens': max_tokens
        }
        
        try:
            print(f"🌐 发送请求到 OpenRouter API...")
            print(f"   URL: {self.api_url}")
            print(f"   模型: {model}")
            print(f"   消息数: {len(messages)}")
            
            response = requests.post(self.api_url, headers=headers, json=payload, timeout=60)
            
            print(f"📥 收到响应: status={response.status_code}")
            
            # 如果不是200，打印完整响应内容
            if response.status_code != 200:
                print(f"❌ API错误响应: {response.text}")
            
            response.raise_for_status()
            
            result = response.json()
            
            # 打印调试信息
            print(f"API响应 - 模型: {model}")
            
            # 解析响应 - OpenRouter使用标准OpenAI格式
            if result.get('choices') and len(result['choices']) > 0:
                content = result['choices'][0]['message']['content']
                ai_logger.info(f"AI响应成功, 模型: {model}, tokens: {result.get('usage', {})}")
                return content
            else:
                error_msg = result.get('error', {}).get('message', 'AI响应格式错误')
                ai_logger.error(f"API响应格式异常: {error_msg}")
                print(f"API响应格式异常: {error_msg}")
                return f"AI响应错误: {error_msg}"
        except requests.exceptions.RequestException as e:
            ai_logger.error(f"API调用失败: {e}", exc_info=True)
            print(f"API调用失败: {e}")
            return f"AI服务暂时不可用: {str(e)}"
    
    def analyze_stock(self, stock_code, stock_name, stock_data, indicators, user_message=None, model=None):
        """分析股票数据并生成交易策略"""
        # 构建系统提示
        system_prompt = ""
#         system_prompt = """你是一位专业的量化交易分析师，擅长技术分析和交易策略制定。
# 请基于提供的股票K线数据和技术指标，进行深入分析并给出交易建议。

# 分析要点：
# 1. 趋势分析：基于K线形态和均线系统判断当前趋势
# 2. 技术指标分析：MACD、RSI等指标的信号解读
# 3. 支撑位和阻力位分析
# 4. 交易建议：买入、卖出或持有，并给出理由和目标价位
# 5. 风险提示

# 请用专业但易懂的语言进行分析。"""
        
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
        response = self.chat(messages, model=model, temperature=0.7, max_tokens=2000)
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
    
    def _format_realtime_price_data(self, stock_code, price_data):
        """格式化完整实时行情数据（包括股价和估值）"""
        if not price_data:
            return f"股票 {stock_code} 暂无实时行情数据"
        
        from datetime import datetime
        
        result = f"=== 实时行情数据 ===\n\n"
        result += f"股票代码: {price_data.get('ts_code', stock_code)}\n"
        
        if price_data.get('stock_name'):
            result += f"股票名称: {price_data['stock_name']}\n"
        
        result += "\n--- 价格信息 ---\n"
        
        # 当前价格和涨跌
        price = price_data.get('price')
        if price:
            result += f"当前价: {price:.2f} 元\n"
        
        change = price_data.get('change')
        change_pct = price_data.get('change_percent')
        if change is not None:
            result += f"涨跌额: {change:+.2f} 元\n"
        if change_pct is not None:
            result += f"涨跌幅: {change_pct:+.2f}%\n"
        
        # 四价
        if price_data.get('open'):
            result += f"开盘价: {price_data['open']:.2f} 元\n"
        if price_data.get('pre_close'):
            result += f"昨收价: {price_data['pre_close']:.2f} 元\n"
        if price_data.get('high'):
            result += f"最高价: {price_data['high']:.2f} 元\n"
        if price_data.get('low'):
            result += f"最低价: {price_data['low']:.2f} 元\n"
        
        # 振幅
        if price_data.get('amplitude'):
            result += f"振幅: {price_data['amplitude']:.2f}%\n"
        
        # 成交信息
        result += "\n--- 成交信息 ---\n"
        
        volume = price_data.get('volume')
        if volume:
            result += f"成交量: {volume / 100000000:.2f} 亿手\n"
        
        amount = price_data.get('amount')
        if amount:
            result += f"成交额: {amount / 100000000:.2f} 亿元\n"
        
        turnover = price_data.get('turnover_ratio')
        if turnover:
            result += f"换手率: {turnover:.2f}%\n"
        
        # 估值信息
        has_valuation = any([
            price_data.get('total_mv'),
            price_data.get('circ_mv'),
            price_data.get('pe'),
            price_data.get('pe_ttm'),
            price_data.get('pb'),
            price_data.get('dv_ratio')
        ])
        
        if has_valuation:
            result += "\n--- 估值信息 ---\n"
            
            if price_data.get('total_mv'):
                result += f"总市值: {price_data['total_mv'] / 10000:.2f} 亿元\n"
            if price_data.get('circ_mv'):
                result += f"流通市值: {price_data['circ_mv'] / 10000:.2f} 亿元\n"
            if price_data.get('pe'):
                result += f"市盈率(动): {price_data['pe']:.2f}\n"
            if price_data.get('pe_ttm'):
                result += f"市盈率(TTM): {price_data['pe_ttm']:.2f}\n"
            if price_data.get('pb'):
                result += f"市净率: {price_data['pb']:.2f}\n"
            if price_data.get('dv_ratio'):
                result += f"股息率: {price_data['dv_ratio']:.2f}%\n"
        
        # 更新时间
        result += "\n--- 数据时间 ---\n"
        if price_data.get('trade_date'):
            result += f"交易日期: {price_data['trade_date']}\n"
        
        if price_data.get('updated_at'):
            try:
                update_time = datetime.strptime(price_data['updated_at'], '%Y-%m-%d %H:%M:%S')
                result += f"更新时间: {update_time.strftime('%Y年%m月%d日 %H:%M:%S')}\n"
            except:
                result += f"更新时间: {price_data['updated_at']}\n"
        
        return result
    
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
        4. 当前价格 - 获取当前股票的实时价格（简化版，仅价格）
        5. 实时行情 - 获取当前股票的完整实时行情（价格+估值+成交）
        
        示例：
        - 日K_复旦微电_30天_MACD&EMA
        - 周K__360天_RSI
        - 1分钟K
        - 持仓
        - 可用资金
        - 当前价格
        - 实时行情
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
        
        # 处理"当前价格"变量（简化版，仅显示价格）
        if '当前价格' in message:
            price_data = stock_service.get_realtime_price(stock_code)
            if price_data and price_data.get('price'):
                price_str = f"当前价格: {price_data['price']:.2f} 元"
                if price_data.get('trade_date'):
                    price_str += f" (交易日: {price_data['trade_date']})"
                if price_data.get('updated_at'):
                    try:
                        update_time = datetime.strptime(price_data['updated_at'], '%Y-%m-%d %H:%M:%S')
                        price_str += f"\n更新时间: {update_time.strftime('%Y年%m月%d日 %H:%M:%S')}"
                    except:
                        price_str += f"\n更新时间: {price_data['updated_at']}"
            else:
                price_str = f"股票 {stock_code} 暂无当前价格数据"
            
            replaced_message = replaced_message.replace('当前价格', f'\n"""\n{price_str}\n"""')
            variables_used['当前价格'] = price_str
        
        # 处理"实时行情"变量（完整版，包括价格+估值+成交）
        if '实时行情' in message:
            price_data = stock_service.get_realtime_price(stock_code)
            realtime_str = self._format_realtime_price_data(stock_code, price_data)
            replaced_message = replaced_message.replace('实时行情', f'\n"""\n{realtime_str}\n"""')
            variables_used['实时行情'] = realtime_str
        
        return replaced_message, variables_used
    
    def _save_prompt_history(self, username, stock_code, user_message, ai_response, replaced_message, images=None):
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
            
            # 图片信息
            image_info = ''
            if images and len(images) > 0:
                image_info = f"\n\n**图片数量**: {len(images)} 张"
            
            content = f"""# 对话历史 - {stock_code}

**时间**: {timestamp}
**历史索引**: {index}
**用户**: {username}{image_info}

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
    
    def chat_with_history(self, user_id, username, stock_code, user_message, model=None, images=None):
        """带历史记录的对话（支持变量替换、图片和Prompt日志）
        
        Args:
            user_id: 用户ID
            username: 用户名
            stock_code: 股票代码
            user_message: 用户消息文本
            model: 模型ID，如果为None则使用默认模型
            images: 图片列表（base64格式），可选
        """
        # 0. 检查模型是否支持图片输入（仅警告，不阻止）
        if images and len(images) > 0:
            if not model:
                model = self.default_model
            
            if not self.check_model_supports_vision(model):
                warning_msg = f"⚠️ 警告：模型 {model} 可能不支持图片输入，如果API返回错误，请切换到支持Vision的模型"
                print(warning_msg)
                # 不返回错误，让API调用来决定是否成功
        
        # 1. 替换变量
        replaced_message, variables_used = self._replace_variables(user_id, stock_code, user_message)
        
        print(f"\n📝 用户输入: {user_message}")
        if variables_used:
            print(f"🔄 变量替换: {list(variables_used.keys())}")
        if images:
            print(f"🖼️ 图片数量: {len(images)}")
        
        # 2. 获取历史记录
        history = self.get_chat_history(user_id, stock_code, limit=10)
        
        # 3. 构建消息列表
        messages = [
            #{'role': 'system', 'content': '你是一位专业的股票分析助手，可以分析图片中的股票走势、财报数据等信息。请基于历史对话和用户问题提供分析建议。'}
            {'role': 'system', 'content': ''}
        ]
        
        for h in history:
            messages.append({
                'role': h['role'],
                'content': h['content']
            })
        
        # 4. 构建用户消息（支持vision格式）
        if images and len(images) > 0:
            # Vision格式：包含文本和图片
            content = []
            
            # 添加文本（如果有）
            if replaced_message:
                content.append({
                    'type': 'text',
                    'text': replaced_message
                })
            
            # 添加图片
            for img_base64 in images:
                # 确保base64格式正确（data:image/xxx;base64,xxx）
                if not img_base64.startswith('data:image'):
                    print(f"⚠️ 图片格式错误，应该以 'data:image' 开头")
                    continue
                
                content.append({
                    'type': 'image_url',
                    'image_url': {
                        'url': img_base64  # OpenRouter支持data:image格式的base64
                    }
                })
            
            messages.append({
                'role': 'user',
                'content': content
            })
        else:
            # 纯文本格式
            messages.append({
                'role': 'user',
                'content': replaced_message
            })
        
        # 5. 调用AI
        response = self.chat(messages, model=model)
        
        # 6. 保存对话记录到数据库（保存原始消息和图片信息）
        # 构建完整的用户消息（包含文本和图片标记）
        if images and len(images) > 0:
            import json
            # 将图片和文本一起保存为JSON格式
            save_content = json.dumps({
                'text': user_message,
                'images': images  # 保存完整的base64图片数据
            }, ensure_ascii=False)
            self.save_chat_history(user_id, stock_code, 'user', save_content)
        else:
            # 纯文本消息
            self.save_chat_history(user_id, stock_code, 'user', user_message)
        
        self.save_chat_history(user_id, stock_code, 'assistant', response)
        
        # 7. 保存Prompt历史到文件（保存替换后的完整内容和图片信息）
        save_text = user_message if user_message else f"[发送了{len(images)}张图片]"
        self._save_prompt_history(username, stock_code, save_text, response, replaced_message, images=images)
        
        return response


# 创建全局AI服务实例
ai_service = AIService()
