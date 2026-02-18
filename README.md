# AI量化股票分析工具

一个基于大模型的量化股票分析系统，集成股票数据获取、技术指标分析、AI智能对话和持仓管理等功能。

## 功能特性

### 📊 股票分析
- **K线图展示**：1分钟K、日K、周K三种周期K线图
- **交互功能**：十字星光标、键盘缩放、鼠标拖拽
- **多市场支持**：支持A股（上海/深圳）、港股
- **自选股管理**：支持添加/删除自选股
- **实时数据获取**：通过Tushare API获取股票K线数据
- **技术指标分析**：MACD、RSI、EMA等多种技术指标
- **AI智能对话**：基于通义千问大模型的智能股票分析
- **自动更新**：1分钟K每5分钟更新，日K/周K每24小时更新

### 💼 持仓管理
- **持仓记录**：记录股票代码、数量、成本价
- **实时盈亏**：自动计算盈亏金额和比例
- **现金管理**：管理可用现金余额
- **投资组合总览**：一键查看总资产、持仓市值、总盈亏

### 📝 对话模版
- **模版管理**：创建、编辑、删除对话模版
- **快速启动**：使用预设模版快速开始股票分析
- **个性化定制**：根据需求自定义分析话术

## 技术栈

- **后端**：Flask 3.0 + Python 3.8+
- **数据库**：SQLite / MySQL
- **数据源**：Tushare金融数据接口
- **AI模型**：通义千问API
- **前端**：原生HTML/CSS/JavaScript
- **图表库**：ECharts 5.x
- **定时任务**：Python threading

## 项目结构

```
ai_quanti/
├── app.py                 # Flask主应用
├── config.py              # 配置文件
├── requirements.txt       # Python依赖
├── .env.example          # 环境变量示例
├── database/             # 数据库模块
│   ├── __init__.py
│   └── db_manager.py     # 数据库管理器
├── services/             # 业务服务层
│   ├── __init__.py
│   ├── stock_service.py      # 股票数据服务
│   ├── position_service.py   # 持仓管理服务
│   ├── ai_service.py         # AI对话服务
│   ├── template_service.py   # 模版管理服务
│   ├── watchlist_service.py  # 自选股服务
│   └── scheduler_service.py  # 定时任务服务
├── templates/            # HTML模板
│   ├── base.html
│   ├── index.html        # 股票分析界面
│   ├── positions.html    # 持仓管理界面
│   └── templates.html    # 对话模版界面
└── strategy/             # 策略报告存储目录
```

## 安装部署

### 1. 环境准备

```bash
# 克隆项目
cd ai_quanti

# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置环境变量

复制 `.env.example` 为 `.env` 并填写配置：

```bash
cp .env.example .env
```

编辑 `.env` 文件：

```ini
# Tushare API Token（从 https://tushare.pro/ 获取）
TUSHARE_TOKEN=your_tushare_token_here

# 通义千问 API配置（从 https://dashscope.aliyun.com/ 获取）
QWEN_API_KEY=your_qwen_api_key_here
QWEN_API_URL=https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation

# 数据库类型配置 (mysql 或 sqlite)
# 推荐：开发环境使用 sqlite，生产环境使用 mysql
DATABASE_TYPE=sqlite

# MySQL数据库配置（仅当DATABASE_TYPE=mysql时需要）
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=quanti_stock

# Flask配置
FLASK_SECRET_KEY=your_secret_key_here
FLASK_DEBUG=True
```

### 3. 数据库配置

项目支持两种数据库：

#### 方案A：SQLite（推荐，开箱即用）

**优点**：无需安装数据库服务，适合开发和测试

```bash
# 在.env中设置
DATABASE_TYPE=sqlite
```

数据将自动存储在 `data/quanti_stock.db` 文件中。

#### 方案B：MySQL（适合生产环境）

**优点**：性能更好，适合大数据量和多用户

```bash
# 在.env中设置
DATABASE_TYPE=mysql

# 安装MySQL
brew install mysql
brew services start mysql

# 创建数据库
mysql -u root -p -e "CREATE DATABASE quanti_stock;"
```

### 4. 环境检查

运行环境检查脚本，确保所有配置正确：

```bash
python check_env.py
```

### 5. 运行应用

```bash
python app.py
```

访问 `http://localhost:5000` 即可使用系统。

## 使用指南

### 股票分析流程

1. **添加自选股**
   - 在左侧面板输入股票代码
   - **A股**: `600000` (浦发银行), `000001` (平安银行), `300001` (特锐德)
   - **港股**: `00700` (腾讯), `02050` (三花智控), `9988` (阿里巴巴)
   - 支持带后缀格式: `600000.SH`, `00700.HK`
   - 点击"添加"按钮

2. **查看股票数据**
   - 点击自选股列表中的股票
   - 系统自动加载K线数据和技术指标
   - 可点击"更新数据"获取最新数据

3. **AI智能分析**
   - 点击"AI分析"按钮
   - AI将基于当前数据生成分析报告
   - 分析结果显示在右侧对话区

4. **自由对话**
   - 在对话框输入问题
   - AI会结合历史对话和股票数据回答
   - 支持 Ctrl+Enter 快捷发送

### 持仓管理流程

1. **设置现金**
   - 点击"设置现金"按钮
   - 输入可用现金金额

2. **添加持仓**
   - 点击"添加持仓"按钮
   - 输入股票代码、名称、数量、成本价
   - 系统自动计算盈亏

3. **更新价格**
   - 点击"更新价格"按钮
   - 系统自动获取最新价格并更新盈亏

### 对话模版管理

1. **创建模版**
   - 点击"新建模版"
   - 输入模版名称和内容
   - 保存模版

2. **使用模版**
   - 在股票分析界面可选择模版
   - 快速启动预设的分析话术

## API接口

### 自选股相关
- `GET /api/watchlist` - 获取自选股列表
- `POST /api/watchlist` - 添加自选股
- `DELETE /api/watchlist/<stock_code>` - 删除自选股

### 股票数据相关
- `GET /api/stock/info/<stock_code>` - 获取股票信息
- `GET /api/stock/data/<stock_code>` - 获取K线数据
- `GET /api/stock/indicators/<stock_code>` - 获取技术指标
- `POST /api/stock/update/<stock_code>` - 更新股票数据

### AI对话相关
- `GET /api/chat/history/<stock_code>` - 获取聊天记录
- `POST /api/chat/send` - 发送消息
- `POST /api/chat/analyze/<stock_code>` - AI分析股票
- `DELETE /api/chat/clear/<stock_code>` - 清除聊天记录

### 持仓管理相关
- `GET /api/positions` - 获取持仓列表
- `POST /api/positions` - 添加/更新持仓
- `DELETE /api/positions/<stock_code>` - 删除持仓
- `POST /api/positions/update-prices` - 更新所有持仓价格
- `GET /api/cash` - 获取现金余额
- `PUT /api/cash` - 更新现金余额

### 对话模版相关
- `GET /api/templates` - 获取模版列表
- `POST /api/templates` - 创建模版
- `PUT /api/templates/<id>` - 更新模版
- `DELETE /api/templates/<id>` - 删除模版

## 注意事项

1. **Tushare Token**：需要注册Tushare账号并获取token，免费版有积分限制
2. **通义千问API**：需要阿里云账号并开通DashScope服务
3. **数据更新频率**：建议不要过于频繁调用API，避免超出限额
4. **数据库备份**：定期备份MySQL数据库，防止数据丢失
5. **安全性**：生产环境请修改默认的SECRET_KEY和数据库密码

## 常见问题

**Q: 添加自选股失败？**  
A: 
- **A股**: 确保代码格式正确（6位数字），如 `600000`, `000001`
- **港股**: 使用5位或以下数字，如 `00700`, `02050`, `9988`
- 检查Tushare Token是否有效
- 港股可能需要Tushare积分权限

**Q: AI分析返回错误？**  
A: 检查通义千问API Key是否正确，以及账户余额是否充足。

**Q: 数据库连接失败？**  
A: 
- 使用SQLite：确认 `.env` 中设置了 `DATABASE_TYPE=sqlite`
- 使用MySQL：确认MySQL服务已启动，配置信息正确，数据库用户有创建数据库和表的权限

**Q: 持仓盈亏不准确？**  
A: 点击"更新价格"按钮，系统会从Tushare获取最新价格重新计算。

**Q: 应用启动失败？**  
A: 
1. 运行 `python check_env.py` 检查环境
2. 查看错误日志，确认是否缺少依赖或配置错误
3. 参考 `项目开发文档/调试报告1.md` 中的解决方案

**Q: SQLite和MySQL如何选择？**  
A: 
- **开发/测试**：推荐SQLite，无需安装数据库服务
- **生产环境**：推荐MySQL，性能更好，支持并发访问
- **快速演示**：推荐SQLite，开箱即用

## 开发计划

- [ ] 支持分时K线图表可视化
- [ ] 增加更多技术指标（KDJ、BOLL等）
- [ ] 支持多种AI模型切换
- [ ] 增加回测功能
- [ ] 支持导出分析报告
- [ ] 移动端适配

## 许可证

MIT License

## 作者

AI量化股票分析工具开发团队

---

**免责声明**：本系统仅供学习研究使用，不构成投资建议。股市有风险，投资需谨慎。
