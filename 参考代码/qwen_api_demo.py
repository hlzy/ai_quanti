import requests
import json

# 配置参数
API_KEY = "sk-123f849c635e4a3dbd9f0d4f14cb8720"  # 替换为你的实际密钥
API_URL = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"  # 阿里云千问API地址

# 请求头
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {API_KEY}"
}

# 请求数据
data = {
    "model": "qwen-max",  # 可选模型：qwen-max, qwen-plus, qwen-turbo 等
    "input": {
        "messages": [
            {"role": "user", "content": "请用中文介绍一下你自己"}
        ]
    },
    "parameters": {
        "result_format": "message"  # 返回格式
    }
}

# 发送请求
response = requests.post(API_URL, headers=headers, json=data)

# 处理响应
if response.status_code == 200:
    result = response.json()
    print("回复:", result["output"]["choices"][0]["message"]["content"])
else:
    print("请求失败:", response.status_code, response.text)