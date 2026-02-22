# AI对话功能模块 0.6 - Vision功能支持

## 问题背景

用户在使用图片上传功能时遇到两个问题：
1. ✅ **图片保存问题**（已在0.5版本解决）- 图片在对话中消失
2. ❌ **API调用404错误** - 使用不支持Vision的模型调用时报错：
   ```
   {"error":{"message":"No endpoints found that support image input","code":404}}
   ```

## 根本原因

**OpenRouter并非所有模型都支持Vision（图片输入）功能**。当前默认模型 `qwen/qwen3-235b-a22b-2507` 不支持图片输入，导致API调用失败。

## 解决方案

### 1. 数据库层 - 添加模型Vision支持标记

#### 修改表结构
```sql
-- 添加 supports_vision 字段
ALTER TABLE ai_models ADD COLUMN supports_vision INTEGER NOT NULL DEFAULT 0;
```

#### 更新已知模型
支持Vision的模型：
- ✅ `anthropic/claude-opus-4-20250514` - Claude Opus 4
- ✅ `anthropic/claude-3.5-sonnet` - Claude 3.5 Sonnet
- ✅ `google/gemini-2.0-flash-exp:free` - Gemini 2.0 Flash
- ✅ `openai/gpt-4o` - GPT-4o
- ✅ `openai/gpt-4o-mini` - GPT-4o Mini

不支持Vision的模型：
- ❌ `qwen/qwen3-235b-a22b-2507` - Qwen3
- ❌ `deepseek/deepseek-chat` - DeepSeek Chat

### 2. 后端层 - Vision检查和验证

#### AI服务增强 (`services/ai_service.py`)

**A. 查询模型时包含Vision标记**
```python
def get_available_models(self):
    query = """
    SELECT model_id, model_name, is_enabled, display_order, supports_vision
    FROM ai_models 
    WHERE is_enabled = 1 
    ORDER BY display_order, model_id
    """
```

**B. 新增Vision支持检查函数**
```python
def check_model_supports_vision(self, model_id):
    """检查模型是否支持vision（图像输入）"""
    query = """
    SELECT supports_vision 
    FROM ai_models 
    WHERE model_id = %s AND is_enabled = 1
    """
    result = db_manager.execute_query(query, (model_id,), fetch_one=True)
    
    if result:
        return bool(result.get('supports_vision', 0))
    
    # 默认已知支持 vision 的模型列表
    vision_models = [
        'anthropic/claude-opus-4-20250514',
        'anthropic/claude-3.5-sonnet',
        # ...
    ]
    return model_id in vision_models
```

**C. 在发送前检查**
```python
def chat_with_history(self, user_id, username, stock_code, user_message, model=None, images=None):
    # 检查模型是否支持图片输入
    if images and len(images) > 0:
        if not model:
            model = self.default_model
        
        if not self.check_model_supports_vision(model):
            error_msg = f"❌ 模型 {model} 不支持图片输入，请切换到支持Vision的模型"
            return error_msg
```

### 3. 前端层 - 用户体验优化

#### 模型选择显示 (`templates/index.html`)

**A. 存储完整模型信息**
```javascript
let availableModels = [];  // 存储所有可用模型信息（包括supports_vision）

async function loadModels() {
    availableModels = result.data;  // 保存完整模型信息
    
    // 添加 vision 标记到模型名称
    result.data.forEach(model => {
        const visionTag = model.supports_vision ? ' 🖼️' : '';
        option.textContent = model.model_name + visionTag;
    });
}
```

**B. 实时检查Vision支持**
```javascript
function checkVisionSupport() {
    if (uploadedImages.length === 0) return;
    
    const currentModel = availableModels.find(m => m.model_id === selectedModel);
    if (!currentModel || !currentModel.supports_vision) {
        const visionModels = availableModels.filter(m => m.supports_vision);
        const visionModelNames = visionModels.map(m => m.model_name).join('、');
        showMessage(`⚠️ 当前模型不支持图片输入，请切换到：${visionModelNames}`, 'warning');
    }
}
```

**C. 发送前验证**
```javascript
async function sendMessage() {
    // 如果有图片，检查当前模型是否支持vision
    if (uploadedImages.length > 0) {
        const currentModel = availableModels.find(m => m.model_id === selectedModel);
        if (!currentModel || !currentModel.supports_vision) {
            showMessage('❌ 当前模型不支持图片输入！请切换到支持Vision的模型', 'error');
            return;  // 阻止发送
        }
    }
}
```

**D. 上传图片时提示**
```javascript
function addImagePreview(base64) {
    uploadedImages.push(base64);
    // ... 添加预览 ...
    
    // 检查当前模型是否支持vision
    checkVisionSupport();
}
```

### 4. 管理界面 - 模型Vision配置

#### 模型管理页面增强 (`templates/models.html`)

**A. 显示Vision支持状态**
```javascript
// 表头添加列
<th>Vision支持</th>

// 表格渲染
const visionText = model.supports_vision ? '✅ 支持' : '❌ 不支持';
```

**B. 添加/编辑模型时可配置Vision**
```html
<div class="input-group">
    <label>支持Vision（图片输入）</label>
    <select id="newSupportsVision">
        <option value="0">不支持</option>
        <option value="1">支持</option>
    </select>
</div>
```

**C. 后端API接受Vision参数**
```python
@app.route('/api/admin/models', methods=['POST'])
def add_model():
    supports_vision = data.get('supports_vision', 0)
    query = """
    INSERT INTO ai_models (model_id, model_name, is_enabled, display_order, supports_vision) 
    VALUES (%s, %s, 1, %s, %s)
    """
```

## 测试步骤

### 1. 测试不支持Vision的模型
1. 选择 "qwen3" 或 "DeepSeek Chat" 模型
2. 上传一张图片
3. ✅ **期望**：看到警告提示 "⚠️ 当前模型不支持图片输入..."
4. 点击发送
5. ✅ **期望**：被阻止发送，显示错误提示

### 2. 测试支持Vision的模型
1. 选择 "Claude Opus 4 🖼️" 模型
2. 上传一张图片
3. ✅ **期望**：无警告提示
4. 输入文本 "分析这张图片"
5. 点击发送
6. ✅ **期望**：成功发送，AI返回图片分析结果

### 3. 测试管理员配置
1. 登录管理员账户
2. 进入 "模型管理" 页面
3. ✅ **期望**：看到 "Vision支持" 列，显示各模型的支持状态
4. 添加新模型时可以选择是否支持Vision
5. 编辑现有模型时可以修改Vision支持状态

## 关键文件修改

### 数据库层
- `database/db_manager_sqlite.py` - 添加 `supports_vision` 字段和迁移逻辑

### 后端层
- `services/ai_service.py`
  - `get_available_models()` - 查询时包含 `supports_vision`
  - `check_model_supports_vision()` - 新增检查函数
  - `chat_with_history()` - 发送前验证
- `app.py`
  - `get_models()` - 返回 `supports_vision` 字段
  - `add_model()` - 接受 `supports_vision` 参数
  - `update_model()` - 更新 `supports_vision` 参数

### 前端层
- `templates/index.html`
  - 存储完整模型信息（包括 `supports_vision`）
  - 模型名称显示 🖼️ 标记
  - `checkVisionSupport()` - 实时检查
  - `sendMessage()` - 发送前验证
  - `addImagePreview()` - 上传时提示
- `templates/models.html`
  - 表格显示Vision支持状态
  - 添加/编辑表单包含Vision选项

## 用户体验提升

### 明确的视觉反馈
- ✅ 支持Vision的模型显示 🖼️ 图标
- ⚠️ 上传图片时，不支持的模型会立即警告
- ❌ 发送前双重验证，防止API错误

### 智能提示
- 当用户选择不支持Vision的模型时，提示可用的Vision模型名称
- 例如："请切换到：Claude Opus 4、GPT-4o"

### 管理员灵活配置
- 可以为新模型设置Vision支持
- 可以修改现有模型的Vision状态
- 一目了然的表格显示

## 技术要点

### 防御式编程
```python
# 后端：即使前端检查通过，后端仍然验证
if images and not self.check_model_supports_vision(model):
    return error_msg

# 前端：发送前双重检查
if (uploadedImages.length > 0 && !currentModel.supports_vision) {
    return;  // 阻止发送
}
```

### 向后兼容
```python
# 数据库迁移：自动添加字段
if 'supports_vision' not in columns:
    cursor.execute("ALTER TABLE ai_models ADD COLUMN supports_vision INTEGER NOT NULL DEFAULT 0")

# 默认值：未知模型默认不支持Vision
return bool(result.get('supports_vision', 0))
```

### 已知模型列表
```python
# 硬编码常见支持Vision的模型，作为备用
vision_models = [
    'anthropic/claude-opus-4-20250514',
    'openai/gpt-4o',
    # ...
]
```

## 下一步优化建议

### 1. 动态获取模型能力
- 调用 OpenRouter Models API 获取最新模型列表和能力
- 自动更新数据库中的 `supports_vision` 字段

### 2. 更细粒度的能力标记
- 支持的最大图片数量
- 支持的图片大小限制
- 支持的图片格式

### 3. 智能模型切换
- 当用户上传图片时，自动建议切换到支持Vision的模型
- 一键切换功能

### 4. 图片优化
- 自动压缩图片以减少API调用成本
- 支持多种图片格式转换

## 总结

通过本次更新，彻底解决了Vision功能的兼容性问题：
1. ✅ 数据库层标记模型Vision支持
2. ✅ 后端层验证模型能力
3. ✅ 前端层提供明确的用户反馈
4. ✅ 管理员可灵活配置

用户现在可以清楚地知道哪些模型支持图片输入，避免了API调用错误。
