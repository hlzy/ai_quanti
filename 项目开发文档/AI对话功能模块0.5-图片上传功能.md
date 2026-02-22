# AI对话功能模块0.5 - 图片上传功能

## 功能概述

基于OpenRouter的Vision API，为AI对话功能添加图片上传和分析能力。用户可以上传股票K线图、财报截图等图片，让AI进行分析。

## 主要功能

### 1. 图片上传方式

#### 方式一：点击上传
- 点击输入框左侧的 📎 按钮
- 选择一个或多个图片文件
- 支持的格式：JPG、PNG、GIF、WebP等
- 单个文件大小限制：20MB

#### 方式二：粘贴上传（推荐）
- 从其他应用复制图片（Ctrl/Cmd+C）
- 在输入框中粘贴（Ctrl/Cmd+V）
- 自动识别并添加图片预览

### 2. 图片预览

- 上传后立即显示缩略图预览
- 可以上传多张图片
- 每张图片显示删除按钮（×）
- 预览区域自动显示/隐藏

### 3. 发送消息

- 可以只发图片（不输入文本）
- 可以图片+文本组合发送
- 发送后自动清空图片预览
- 聊天记录中显示图片缩略图

## 技术实现

### 前端实现

#### UI改进
```html
<div class="chat-input-area">
    <!-- 图片预览区域 -->
    <div id="imagePreviewContainer" class="image-preview-container hidden"></div>
    
    <!-- 输入行 -->
    <div class="input-row">
        <input type="file" id="imageInput" accept="image/*" multiple>
        <button class="btn btn-icon" onclick="uploadImage()">📎</button>
        <textarea id="chatInput" placeholder="输入您的问题或粘贴图片（Ctrl+V）..."></textarea>
        <button class="btn" onclick="sendMessage()">发送</button>
    </div>
</div>
```

#### JavaScript功能
1. **文件选择处理**
   - 监听file input的change事件
   - 验证文件类型和大小
   - 转换为base64格式

2. **粘贴事件处理**
   - 监听textarea的paste事件
   - 提取clipboard中的图片
   - 阻止默认粘贴行为

3. **图片预览管理**
   - 添加图片到预览区
   - 删除单张图片
   - 清空所有图片

4. **发送消息增强**
   - 支持纯文本、纯图片、图文混合
   - 将图片base64随消息一起发送
   - 在聊天记录中显示图片缩略图

### 后端实现

#### API修改（app.py）
```python
@app.route('/api/chat/send', methods=['POST'])
@login_required
def send_chat():
    data = request.json
    message = data.get('message', '')  # 可选
    images = data.get('images', [])    # base64图片列表
    
    # 验证：消息或图片至少有一个
    if not message and not images:
        return jsonify({'success': False, 'message': '请输入消息或上传图片'})
    
    # 调用AI服务
    response = ai_service.chat_with_history(
        user_id, username, stock_code, message, 
        model=model, images=images
    )
```

#### AI服务增强（ai_service.py）
```python
def chat_with_history(self, user_id, username, stock_code, 
                     user_message, model=None, images=None):
    # 构建Vision格式的消息
    if images and len(images) > 0:
        content = []
        
        # 添加文本
        if user_message:
            content.append({
                'type': 'text',
                'text': user_message
            })
        
        # 添加图片
        for img_base64 in images:
            content.append({
                'type': 'image_url',
                'image_url': {
                    'url': img_base64  # data:image/jpeg;base64,...
                }
            })
        
        messages.append({
            'role': 'user',
            'content': content  # Vision格式
        })
    else:
        # 传统文本格式
        messages.append({
            'role': 'user',
            'content': user_message
        })
```

## OpenRouter Vision API格式

### 标准Vision消息格式
```json
{
  "model": "anthropic/claude-3.5-sonnet",
  "messages": [
    {
      "role": "user",
      "content": [
        {
          "type": "text",
          "text": "请分析这张K线图的走势"
        },
        {
          "type": "image_url",
          "image_url": {
            "url": "data:image/jpeg;base64,/9j/4AAQSkZJRg..."
          }
        }
      ]
    }
  ]
}
```

### 支持Vision的模型
- ✅ `anthropic/claude-opus-4-20250514`
- ✅ `anthropic/claude-3.5-sonnet`
- ✅ `openai/gpt-4-vision-preview`
- ✅ `google/gemini-pro-vision`
- ❌ `deepseek/deepseek-chat` (不支持)

## 使用场景

### 1. 股票K线分析
- 上传股票走势图
- AI识别图表形态（头肩顶、双底等）
- 分析支撑位和阻力位

### 2. 财报数据分析
- 上传财务报表截图
- AI提取关键数据
- 进行财务比率分析

### 3. 技术指标分析
- 上传带有MACD、RSI等指标的图表
- AI解读指标信号
- 给出交易建议

### 4. 新闻截图分析
- 上传财经新闻截图
- AI提取关键信息
- 评估对股票的影响

## 注意事项

### 1. 图片大小限制
- 单张图片最大20MB
- 建议压缩后上传（提高速度）
- 太大的图片会导致请求超时

### 2. 图片格式
- 推荐JPG/PNG格式
- base64编码会增加约33%大小
- 确保图片清晰可辨

### 3. 模型选择
- 优先选择支持Vision的模型
- Claude Opus 4和Sonnet 3.5效果最好
- DeepSeek等纯文本模型会忽略图片

### 4. 隐私安全
- 图片不会保存到数据库
- 仅在当前对话中传输
- 敏感信息请谨慎上传

## 文件修改清单

### 前端文件
- ✅ `templates/index.html`
  - 添加图片上传UI
  - 实现粘贴功能
  - 图片预览管理
  - 修改sendMessage函数

### 后端文件
- ✅ `app.py`
  - 修改`/api/chat/send`接口
  - 支持images参数

- ✅ `services/ai_service.py`
  - 修改`chat_with_history`方法
  - 支持Vision消息格式
  - 添加images参数

## 测试建议

### 测试用例1：纯文本消息
- ✅ 输入文本后点击发送
- ✅ 验证消息正常发送和接收

### 测试用例2：纯图片消息
- ✅ 只上传图片不输入文本
- ✅ 验证AI能识别和描述图片

### 测试用例3：图文混合
- ✅ 上传图片并输入提问
- ✅ 验证AI结合图片和文本回答

### 测试用例4：多图片上传
- ✅ 上传2-3张图片
- ✅ 验证所有图片都显示预览
- ✅ 验证AI能分析所有图片

### 测试用例5：粘贴功能
- ✅ 从浏览器复制图片粘贴
- ✅ 从截图工具粘贴
- ✅ 验证自动添加到预览区

### 测试用例6：删除图片
- ✅ 上传多张图片后删除部分
- ✅ 验证预览区正确更新

## 未来改进方向

1. **图片编辑功能**
   - 裁剪和旋转
   - 添加标注和箭头
   - 高亮关键区域

2. **OCR文字提取**
   - 提取图片中的文字
   - 支持表格识别
   - 导出为文本

3. **图片历史**
   - 保存上传的图片
   - 建立图片库
   - 快速引用历史图片

4. **批量分析**
   - 上传多张图片批量分析
   - 对比分析功能
   - 生成分析报告

## 相关文档
- [AI对话功能模块0.4](./AI对话功能模块0.4.md)
- [OpenRouter API文档](https://openrouter.ai/docs)
- [Vision API使用指南](https://openrouter.ai/docs/vision)
