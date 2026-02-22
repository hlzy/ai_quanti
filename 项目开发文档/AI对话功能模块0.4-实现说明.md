# AI对话功能模块0.4 - OpenRouter集成与模型选择

## 功能概述

本次更新将AI服务从**通义千问**切换到**OpenRouter**聚合平台，并添加了**模型选择**功能，允许用户在对话时选择不同的AI模型。

## 主要变更

### 1. AI服务提供商切换
- **原平台**：通义千问 (Qwen)
- **新平台**：OpenRouter（支持多个AI模型提供商）
- **优势**：
  - 统一接口访问多个AI模型（DeepSeek、Claude、GPT等）
  - 更灵活的模型选择
  - 更好的性价比

### 2. 模型选择功能
用户可以在AI对话界面选择不同的AI模型进行对话：
- **位置**：AI对话记录面板标题栏，清除按钮左侧
- **默认模型**：
  - `deepseek/deepseek-chat` - DeepSeek Chat
  - `anthropic/claude-opus-4-20250514` - Claude Opus 4
- **管理员可配置**：管理员可以添加、启用/禁用模型

## 技术实现

### 1. 数据库变更

#### 新增表：`ai_models`
```sql
CREATE TABLE ai_models (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    model_id TEXT NOT NULL UNIQUE,          -- 模型ID（如：deepseek/deepseek-chat）
    model_name TEXT NOT NULL,                -- 显示名称（如：DeepSeek Chat）
    is_enabled INTEGER NOT NULL DEFAULT 1,   -- 是否启用
    display_order INTEGER NOT NULL DEFAULT 0, -- 显示顺序
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**默认数据**：
- `deepseek/deepseek-chat` - DeepSeek Chat
- `anthropic/claude-opus-4-20250514` - Claude Opus 4

### 2. 后端 API 修改

#### AIService 类改造 (`services/ai_service.py`)

**主要变更**：
```python
class AIService:
    def __init__(self):
        # OpenRouter配置
        self.api_key = config.OPENROUTER_API_KEY
        self.api_url = "https://openrouter.ai/api/v1/chat/completions"
        self.site_url = config.SITE_URL
        self.site_name = config.SITE_NAME
        self.default_model = "deepseek/deepseek-chat"
    
    def get_available_models(self):
        """获取可用的模型列表"""
        # 从数据库查询已启用的模型
        
    def chat(self, messages, model=None, temperature=0.7, max_tokens=2000):
        """调用OpenRouter API进行对话"""
        # 使用标准OpenAI格式调用OpenRouter
```

**方法签名更新**：
- `analyze_stock(...)` 增加 `model` 参数
- `chat_with_history(...)` 增加 `model` 参数
- 新增 `get_available_models()` 方法

#### 新增 API 端点

**用户端点**：
```python
# 获取可用模型列表
GET /api/chat/models
Response: {
    "success": true,
    "data": [
        {"model_id": "deepseek/deepseek-chat", "model_name": "DeepSeek Chat", ...},
        {"model_id": "anthropic/claude-opus-4-20250514", "model_name": "Claude Opus 4", ...}
    ]
}

# 发送消息（增加model参数）
POST /api/chat/send
Body: {
    "stock_code": "601127.SH",
    "message": "分析一下",
    "model": "deepseek/deepseek-chat"  // 可选，不传则使用默认模型
}
```

**管理员端点**：
```python
# 获取所有模型配置
GET /api/admin/models

# 添加新模型
POST /api/admin/models
Body: {
    "model_id": "openai/gpt-4",
    "model_name": "GPT-4",
    "display_order": 3
}

# 更新模型配置
PUT /api/admin/models/<model_id>
Body: {
    "model_name": "GPT-4 Turbo",
    "is_enabled": 1,
    "display_order": 2
}

# 删除模型
DELETE /api/admin/models/<model_id>
```

### 3. 前端实现

#### 模型选择下拉框 (`templates/index.html`)

**位置**：AI对话记录面板标题栏
```html
<select id="modelSelect" style="float: right; ...">
    <option value="">加载中...</option>
</select>
```

**JavaScript 实现**：
```javascript
// 全局变量
let selectedModel = null;  // 当前选择的模型

// 页面加载时加载模型列表
async function loadModels() {
    const response = await fetch('/api/chat/models');
    const result = await response.json();
    // 填充下拉框选项
    // 监听选择变化
}

// 发送消息时携带模型参数
async function sendMessage() {
    const response = await fetch('/api/chat/send', {
        method: 'POST',
        body: JSON.stringify({
            stock_code: currentStock.code,
            message: message,
            model: selectedModel  // 发送选择的模型
        })
    });
}
```

### 4. 配置文件更新

#### `.env` 文件
```bash
# OpenRouter API配置（替代通义千问）
OPENROUTER_API_KEY=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
SITE_URL=https://ai-quant.example.com
SITE_NAME=AI量化股票分析工具
```

#### `config.py` 更新
```python
class Config:
    # OpenRouter配置
    OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY', '')
    SITE_URL = os.getenv('SITE_URL', 'https://ai-quant.example.com')
    SITE_NAME = os.getenv('SITE_NAME', 'AI量化股票分析工具')
```

## 使用说明

### 用户端使用

1. **选择股票**：在自选股列表中选择一只股票
2. **选择模型**：在AI对话面板顶部的下拉框中选择AI模型
3. **发送消息**：输入问题并发送，系统将使用选择的模型进行回复

### 管理员配置

1. **访问管理界面**：进入"用户管理"页面
2. **管理模型**：
   - 查看所有已配置的模型
   - 添加新模型（输入模型ID和显示名称）
   - 启用/禁用模型
   - 调整显示顺序
   - 删除不需要的模型

## 支持的模型示例

根据 OpenRouter 平台，可配置的模型包括但不限于：

### DeepSeek 系列
- `deepseek/deepseek-chat` - DeepSeek Chat（默认）
- `deepseek/deepseek-coder` - DeepSeek Coder

### Anthropic Claude 系列
- `anthropic/claude-opus-4-20250514` - Claude Opus 4（默认）
- `anthropic/claude-sonnet-4-20250514` - Claude Sonnet 4
- `anthropic/claude-3.5-sonnet` - Claude 3.5 Sonnet

### OpenAI 系列
- `openai/gpt-4-turbo` - GPT-4 Turbo
- `openai/gpt-4o` - GPT-4o
- `openai/gpt-3.5-turbo` - GPT-3.5 Turbo

### Google 系列
- `google/gemini-pro-1.5` - Gemini Pro 1.5
- `google/gemini-flash-1.5` - Gemini Flash 1.5

### Meta 系列
- `meta-llama/llama-3.1-405b-instruct` - Llama 3.1 405B

## 注意事项

1. **API Key 配置**：
   - 必须在 `.env` 文件中配置有效的 `OPENROUTER_API_KEY`
   - 可从 [OpenRouter](https://openrouter.ai/) 注册获取

2. **模型配置**：
   - 模型ID必须是OpenRouter支持的有效模型
   - 可在 [OpenRouter Models](https://openrouter.ai/models) 查看所有支持的模型

3. **费用管理**：
   - 不同模型的调用成本不同
   - 建议根据实际需求选择合适的模型
   - DeepSeek系列模型性价比较高

4. **兼容性**：
   - 所有历史对话记录保持不变
   - 新对话将使用选择的模型
   - 对话历史中不记录使用的模型（未来版本可增加）

## 迁移说明

从通义千问迁移到OpenRouter：

1. **环境变量更新**：
   ```bash
   # 旧配置（可删除）
   QWEN_API_KEY=...
   QWEN_API_URL=...
   
   # 新配置
   OPENROUTER_API_KEY=sk-or-v1-...
   SITE_URL=https://ai-quant.example.com
   SITE_NAME=AI量化股票分析工具
   ```

2. **数据库初始化**：
   ```bash
   python -c "from database.db_manager_sqlite import db_manager; db_manager.init_database()"
   ```

3. **重启应用**：
   ```bash
   python app.py
   ```

## 后续优化建议

1. **模型元数据**：在数据库中记录每次对话使用的模型
2. **成本统计**：统计每个模型的使用次数和预估成本
3. **模型推荐**：根据问题类型自动推荐合适的模型
4. **响应时间**：显示不同模型的平均响应时间
5. **用户偏好**：记住用户的模型偏好设置

## 相关文件

### 修改的文件
- `services/ai_service.py` - AI服务核心逻辑
- `database/db_manager_sqlite.py` - 数据库表结构
- `app.py` - API端点
- `config.py` - 配置文件
- `.env` - 环境变量
- `templates/index.html` - 前端界面

### 参考文件
- `参考代码/openrouter.py` - OpenRouter API调用示例

## 版本信息
- **版本号**：0.4
- **更新日期**：2026-02-20
- **更新内容**：切换到OpenRouter平台，添加模型选择功能
