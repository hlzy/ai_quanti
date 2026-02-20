# 用户信息显示功能

## 功能描述
在页面右上角添加当前登录用户信息和退出登录按钮。

## 实现效果

### 导航栏布局
```
┌──────────────────────────────────────────────────────────────────────┐
│  🚀 AI量化股票分析工具                                                  │
│  ┌────────────────────────────┐  ┌──────────────────────────────────┐│
│  │ 股票分析 | 持仓管理 | ...   │  │ 👤 admin [管理员] [退出登录]    ││
│  └────────────────────────────┘  └──────────────────────────────────┘│
└──────────────────────────────────────────────────────────────────────┘
```

### 管理员视图
- **用户名显示**：👤 admin
- **角色徽章**：`[管理员]`（半透明白色背景）
- **菜单项**：显示"用户管理"菜单
- **退出按钮**：右上角"退出登录"按钮

### 普通用户视图
- **用户名显示**：👤 用户名
- **角色徽章**：`[用户]`（半透明白色背景）
- **菜单项**：不显示"用户管理"菜单
- **退出按钮**：右上角"退出登录"按钮

## 修改的文件

### 1. templates/base.html
修改导航栏结构，添加用户信息区域：

#### CSS样式新增
```css
.navbar-content {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-top: 1rem;
}

.user-info {
    display: flex;
    align-items: center;
    gap: 1rem;
}

.user-name {
    color: white;
    font-size: 0.95rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

.user-name::before {
    content: '👤';
    font-size: 1.2rem;
}

.role-badge {
    background: rgba(255, 255, 255, 0.3);
    padding: 0.2rem 0.6rem;
    border-radius: 12px;
    font-size: 0.8rem;
    font-weight: 500;
}

.logout-btn {
    color: white;
    background: rgba(255, 255, 255, 0.2);
    border: 1px solid rgba(255, 255, 255, 0.3);
    padding: 0.5rem 1rem;
    border-radius: 5px;
    text-decoration: none;
    font-size: 0.9rem;
    transition: all 0.3s;
    cursor: pointer;
}

.logout-btn:hover {
    background: rgba(255, 255, 255, 0.3);
    transform: translateY(-1px);
}
```

#### HTML结构
```html
<nav class="navbar">
    <h1>🚀 AI量化股票分析工具</h1>
    <div class="navbar-content">
        <div class="nav-links">
            <a href="/">股票分析</a>
            <a href="/positions">持仓管理</a>
            <a href="/templates">对话模版</a>
            <a href="/database">数据库浏览</a>
            {% if session.get('role') == 'admin' %}
            <a href="/admin">用户管理</a>
            {% endif %}
        </div>
        
        <div class="user-info">
            <div class="user-name">
                {{ session.get('username', '访客') }}
                {% if session.get('role') == 'admin' %}
                <span class="role-badge">管理员</span>
                {% else %}
                <span class="role-badge">用户</span>
                {% endif %}
            </div>
            <a href="/logout" class="logout-btn">退出登录</a>
        </div>
    </div>
</nav>
```

### 2. templates/admin.html
更新管理员界面的用户信息显示：

```html
<div class="navbar">
    <h1>👤 用户管理</h1>
    <div class="navbar-right">
        <span id="userInfo">
            👤 {{ session.get('username', 'admin') }}
            <span style="...">管理员</span>
        </span>
        <a href="/" class="nav-btn">返回首页</a>
        <a href="/logout" class="nav-btn">退出登录</a>
    </div>
</div>
```

## 功能特性

### 1. 动态用户信息
- 从Flask session中读取用户名和角色
- 实时显示当前登录用户

### 2. 角色区分
- **管理员**：显示"管理员"徽章，可见"用户管理"菜单
- **普通用户**：显示"用户"徽章，不可见"用户管理"菜单

### 3. 退出登录
- 点击"退出登录"按钮
- 跳转到 `/logout` 路由
- 清除session并返回登录页

### 4. 响应式设计
- 鼠标悬停时按钮有轻微上浮效果
- 半透明背景增强视觉层次
- 与整体设计风格一致

## 使用说明

### 启动应用
```bash
cd /Users/sunjie/CodeBuddy/ai_quanti
python app.py
```

### 登录并查看
1. 访问 http://localhost:5000/login
2. 使用管理员账户登录：
   - 用户名：`admin`
   - 密码：`admin123`
3. 登录后查看右上角用户信息

### 预览页面
打开 `test_navbar_preview.html` 可以预览导航栏效果（不需要启动服务器）

## 技术实现

### Session数据使用
```python
# app.py 登录时设置session
session['user_id'] = user['id']
session['username'] = user['username']
session['role'] = user['role']
```

### Jinja2模板语法
```jinja2
{# 获取session数据 #}
{{ session.get('username', '访客') }}

{# 条件判断 #}
{% if session.get('role') == 'admin' %}
    <a href="/admin">用户管理</a>
{% endif %}

{# 当前路径高亮 #}
<a class="{% if request.path == '/' %}active{% endif %}">
```

### 样式设计原则
- **一致性**：与现有渐变紫色主题一致
- **清晰性**：用户信息清晰可见
- **交互性**：悬停效果提供视觉反馈
- **层次性**：半透明背景区分不同元素

## 效果展示

### 管理员导航栏
```
┌────────────────────────────────────────────────────────────┐
│  🚀 AI量化股票分析工具                                        │
├────────────────────────────────────────────────────────────┤
│  股票分析  持仓管理  对话模版  数据库浏览  用户管理            │
│                                  👤 admin [管理员] [退出登录]│
└────────────────────────────────────────────────────────────┘
```

### 普通用户导航栏
```
┌────────────────────────────────────────────────────────────┐
│  🚀 AI量化股票分析工具                                        │
├────────────────────────────────────────────────────────────┤
│  股票分析  持仓管理  对话模版  数据库浏览                      │
│                                  👤 张三 [用户] [退出登录]   │
└────────────────────────────────────────────────────────────┘
```

## 测试清单

- [x] 管理员登录后显示正确的用户名和角色
- [x] 普通用户登录后显示正确的用户名和角色
- [x] 管理员可以看到"用户管理"菜单
- [x] 普通用户看不到"用户管理"菜单
- [x] 点击"退出登录"可以正常退出
- [x] 退出后跳转到登录页面
- [x] 未登录用户访问受保护页面会跳转到登录页
- [x] 样式在不同浏览器中显示一致

## 未来改进

### 可选增强功能
1. **下拉菜单**：点击用户名显示下拉菜单（修改密码、个人设置等）
2. **头像显示**：添加用户头像图片
3. **在线状态**：显示在线状态指示器
4. **消息通知**：显示未读消息数量
5. **快捷操作**：常用功能快捷入口

### 移动端适配
- 小屏幕时隐藏部分菜单文字，只显示图标
- 汉堡菜单折叠导航链接
- 用户信息简化显示

## 总结
✅ 已成功为系统添加用户信息显示功能
✅ 支持管理员和普通用户角色区分
✅ 提供快捷退出登录功能
✅ 界面美观，交互流畅
