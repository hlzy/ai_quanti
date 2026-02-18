"""
Flask主应用
"""
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from config import config
from database import db_manager
from services import stock_service, position_service, ai_service, template_service
from services.watchlist_service import watchlist_service
from services.scheduler_service import scheduler_service
from services.db_browser_service import db_browser_service
import traceback

app = Flask(__name__)
app.config['SECRET_KEY'] = config.SECRET_KEY
CORS(app)


# ========== 主页路由 ==========
@app.route('/')
def index():
    """股票分析主界面"""
    return render_template('index.html')


@app.route('/positions')
def positions_page():
    """持仓管理界面"""
    return render_template('positions.html')


@app.route('/templates')
def templates_page():
    """对话模版管理界面"""
    return render_template('templates.html')


@app.route('/database')
def database_page():
    """数据库浏览界面"""
    return render_template('database.html')


# ========== 自选股API ==========
@app.route('/api/watchlist', methods=['GET'])
def get_watchlist():
    """获取自选股列表"""
    try:
        watchlist = watchlist_service.get_all_watchlist()
        return jsonify({'success': True, 'data': watchlist})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/watchlist', methods=['POST'])
def add_watchlist():
    """添加自选股"""
    try:
        data = request.json
        stock_code = data.get('stock_code')
        
        if not stock_code:
            return jsonify({'success': False, 'message': '股票代码不能为空'}), 400
        
        result = watchlist_service.add_to_watchlist(stock_code)
        if result:
            return jsonify({'success': True, 'message': '添加成功'})
        else:
            return jsonify({'success': False, 'message': '股票代码无效或已存在'}), 400
    except Exception as e:
        traceback.print_exc()
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/watchlist/<stock_code>', methods=['DELETE'])
def delete_watchlist(stock_code):
    """删除自选股"""
    try:
        result = watchlist_service.remove_from_watchlist(stock_code)
        if result:
            return jsonify({'success': True, 'message': '删除成功'})
        else:
            return jsonify({'success': False, 'message': '删除失败'}), 400
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


# ========== 股票数据API ==========
@app.route('/api/stock/info/<stock_code>', methods=['GET'])
def get_stock_info(stock_code):
    """获取股票基本信息"""
    try:
        info = stock_service.get_stock_info(stock_code)
        if info:
            return jsonify({'success': True, 'data': info})
        else:
            return jsonify({'success': False, 'message': '股票不存在'}), 404
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/stock/data/<stock_code>', methods=['GET'])
def get_stock_data(stock_code):
    """获取股票K线数据（仅从数据库读取，不触发API调用）"""
    try:
        period = request.args.get('period', 'daily')
        days = int(request.args.get('days', 60))
        
        # 从数据库获取数据（不再自动触发API更新）
        data = stock_service.get_stock_data_from_db(stock_code, period, days)
        
        return jsonify({'success': True, 'data': data})
    except Exception as e:
        traceback.print_exc()
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/stock/indicators/<stock_code>', methods=['GET'])
def get_stock_indicators(stock_code):
    """获取股票技术指标"""
    try:
        days = int(request.args.get('days', 60))
        indicators = stock_service.get_indicators_from_db(stock_code, days)
        
        return jsonify({'success': True, 'data': indicators})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/stock/update/<stock_code>', methods=['POST'])
def update_stock_data(stock_code):
    """更新股票数据"""
    try:
        result = stock_service.update_stock_data(stock_code)
        if result:
            return jsonify({'success': True, 'message': '数据更新成功'})
        else:
            return jsonify({'success': False, 'message': '数据更新失败'}), 400
    except Exception as e:
        traceback.print_exc()
        return jsonify({'success': False, 'message': str(e)}), 500


# ========== AI对话API ==========
@app.route('/api/chat/history/<stock_code>', methods=['GET'])
def get_chat_history(stock_code):
    """获取聊天记录"""
    try:
        history = ai_service.get_chat_history(stock_code)
        return jsonify({'success': True, 'data': history})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/chat/send', methods=['POST'])
def send_chat():
    """发送聊天消息"""
    try:
        data = request.json
        stock_code = data.get('stock_code')
        message = data.get('message')
        
        if not stock_code or not message:
            return jsonify({'success': False, 'message': '参数不完整'}), 400
        
        # 带历史记录的对话
        response = ai_service.chat_with_history(stock_code, message)
        
        return jsonify({'success': True, 'data': {'response': response}})
    except Exception as e:
        traceback.print_exc()
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/chat/analyze/<stock_code>', methods=['POST'])
def analyze_stock(stock_code):
    """分析股票并生成策略"""
    try:
        # 获取股票数据
        stock_info = stock_service.get_stock_info(stock_code)
        if not stock_info:
            return jsonify({'success': False, 'message': '股票不存在'}), 404
        
        stock_data = stock_service.get_stock_data_from_db(stock_code, 'daily', 60)
        indicators = stock_service.get_indicators_from_db(stock_code, 60)
        
        if not stock_data or not indicators:
            return jsonify({'success': False, 'message': '股票数据不足，请先更新数据'}), 400
        
        # 获取用户自定义消息
        data = request.json or {}
        user_message = data.get('message')
        
        # AI分析
        analysis = ai_service.analyze_stock(
            stock_code,
            stock_info['name'],
            stock_data,
            indicators,
            user_message
        )
        
        # 保存对话记录
        if user_message:
            ai_service.save_chat_history(stock_code, 'user', user_message)
        ai_service.save_chat_history(stock_code, 'assistant', analysis)
        
        # 生成指标摘要
        latest = indicators[-1]
        indicators_summary = f"""
最新MACD: {latest['macd']:.4f} (信号线: {latest['macd_signal']:.4f})
最新RSI(6): {latest['rsi_6']:.2f}, RSI(12): {latest['rsi_12']:.2f}
EMA(12): {latest['ema_12']:.2f}, EMA(26): {latest['ema_26']:.2f}
"""
        
        # 保存策略文件
        strategy_file = ai_service.save_strategy(
            stock_code,
            stock_info['name'],
            analysis,
            indicators_summary
        )
        
        return jsonify({
            'success': True,
            'data': {
                'analysis': analysis,
                'strategy_file': strategy_file
            }
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/chat/clear/<stock_code>', methods=['DELETE'])
def clear_chat_history(stock_code):
    """清除聊天记录"""
    try:
        ai_service.clear_chat_history(stock_code)
        return jsonify({'success': True, 'message': '聊天记录已清除'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


# ========== 持仓管理API ==========
@app.route('/api/positions', methods=['GET'])
def get_positions():
    """获取所有持仓"""
    try:
        summary = position_service.get_portfolio_summary()
        return jsonify({'success': True, 'data': summary})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/positions', methods=['POST'])
def add_position():
    """添加或更新持仓"""
    try:
        data = request.json
        stock_code = data.get('stock_code')
        stock_name = data.get('stock_name')
        quantity = int(data.get('quantity', 0))
        cost_price = float(data.get('cost_price', 0))
        
        if not stock_code or quantity <= 0 or cost_price <= 0:
            return jsonify({'success': False, 'message': '参数无效'}), 400
        
        result = position_service.add_or_update_position(stock_code, stock_name, quantity, cost_price)
        if result:
            return jsonify({'success': True, 'message': '操作成功'})
        else:
            return jsonify({'success': False, 'message': '操作失败'}), 400
    except Exception as e:
        traceback.print_exc()
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/positions/<stock_code>', methods=['DELETE'])
def delete_position(stock_code):
    """删除持仓"""
    try:
        result = position_service.delete_position(stock_code)
        if result:
            return jsonify({'success': True, 'message': '删除成功'})
        else:
            return jsonify({'success': False, 'message': '删除失败'}), 400
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/positions/update-prices', methods=['POST'])
def update_positions_prices():
    """更新所有持仓价格"""
    try:
        position_service.update_all_positions_price()
        return jsonify({'success': True, 'message': '价格更新成功'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/cash', methods=['GET'])
def get_cash():
    """获取现金余额"""
    try:
        balance = position_service.get_cash_balance()
        return jsonify({'success': True, 'data': {'balance': float(balance)}})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/cash', methods=['PUT'])
def update_cash():
    """更新现金余额"""
    try:
        data = request.json
        balance = float(data.get('balance', 0))
        
        if balance < 0:
            return jsonify({'success': False, 'message': '余额不能为负'}), 400
        
        result = position_service.update_cash_balance(balance)
        if result:
            return jsonify({'success': True, 'message': '更新成功'})
        else:
            return jsonify({'success': False, 'message': '更新失败'}), 400
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


# ========== 数据库浏览API ==========
@app.route('/api/database/tables', methods=['GET'])
def get_database_tables():
    """获取所有表信息"""
    try:
        tables = db_browser_service.get_all_tables()
        return jsonify({'success': True, 'data': tables})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/database/table/<table_name>/structure', methods=['GET'])
def get_table_structure(table_name):
    """获取表结构"""
    try:
        structure = db_browser_service.get_table_structure(table_name)
        return jsonify({'success': True, 'data': structure})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/database/table/<table_name>/data', methods=['GET'])
def get_table_data(table_name):
    """获取表数据"""
    try:
        limit = int(request.args.get('limit', 100))
        offset = int(request.args.get('offset', 0))
        order_by = request.args.get('order_by')
        
        data = db_browser_service.get_table_data(table_name, limit, offset, order_by)
        total = db_browser_service.get_table_count(table_name)
        
        return jsonify({
            'success': True,
            'data': data,
            'total': total,
            'limit': limit,
            'offset': offset
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/database/query', methods=['POST'])
def execute_custom_query():
    """执行自定义查询"""
    try:
        data = request.json
        query = data.get('query')
        
        if not query:
            return jsonify({'success': False, 'message': '查询语句不能为空'}), 400
        
        result = db_browser_service.execute_custom_query(query)
        return jsonify({'success': True, 'data': result})
    except Exception as e:
        traceback.print_exc()
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/database/stats', methods=['GET'])
def get_database_stats():
    """获取数据库统计信息"""
    try:
        stats = db_browser_service.get_database_stats()
        return jsonify({'success': True, 'data': stats})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


# ========== 对话模版API ==========
@app.route('/api/templates', methods=['GET'])
def get_templates():
    """获取所有模版"""
    try:
        templates = template_service.get_all_templates()
        return jsonify({'success': True, 'data': templates})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/templates', methods=['POST'])
def create_template():
    """创建模版"""
    try:
        data = request.json
        name = data.get('name')
        content = data.get('content')
        
        if not name or not content:
            return jsonify({'success': False, 'message': '参数不完整'}), 400
        
        result = template_service.create_template(name, content)
        if result:
            return jsonify({'success': True, 'message': '创建成功'})
        else:
            return jsonify({'success': False, 'message': '创建失败'}), 400
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/templates/<int:template_id>', methods=['PUT'])
def update_template(template_id):
    """更新模版"""
    try:
        data = request.json
        name = data.get('name')
        content = data.get('content')
        
        if not name or not content:
            return jsonify({'success': False, 'message': '参数不完整'}), 400
        
        result = template_service.update_template(template_id, name, content)
        if result:
            return jsonify({'success': True, 'message': '更新成功'})
        else:
            return jsonify({'success': False, 'message': '更新失败'}), 400
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/templates/<int:template_id>', methods=['DELETE'])
def delete_template(template_id):
    """删除模版"""
    try:
        result = template_service.delete_template(template_id)
        if result:
            return jsonify({'success': True, 'message': '删除成功'})
        else:
            return jsonify({'success': False, 'message': '删除失败'}), 400
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


# ========== 初始化 ==========
def init_app():
    """初始化应用"""
    try:
        # 初始化数据库
        print("正在初始化数据库...")
        db_manager.init_database()
        print("数据库初始化完成！")
        
        # 初始化目录
        config.init_directories()
        print("目录初始化完成！")
        
        # 启动定时任务
        print("正在启动定时任务...")
        scheduler_service.start()
        print("定时任务启动完成！")
        
    except Exception as e:
        print(f"初始化失败: {e}")
        traceback.print_exc()


if __name__ == '__main__':
    init_app()
    try:
        app.run(host='0.0.0.0', port=5000, debug=config.DEBUG)
    finally:
        # 应用退出时停止定时任务
        scheduler_service.stop()
