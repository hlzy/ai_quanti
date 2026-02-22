import requests
import json

# 設置您的 OpenRouter API 金鑰
api_key = "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"  # 請替換為您的實際 API 金鑰

# API 請求的 URL
url = "https://openrouter.ai/api/v1/chat/completions"

# 請求頭部
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json",
    # 以下兩個頭部為可選，用於在 OpenRouter 排行榜上顯示您的應用信息
    "HTTP-Referer": "<YOUR_SITE_URL>",    # 可選：您的網站 URL
    "X-Title": "<YOUR_SITE_NAME>",        # 可選：您的網站名稱
}

# 請求數據（對話內容）
data = {
    "model": "anthropic/claude-opus-4.6",  # 可選：指定模型，如不指定，OpenRouter 會自動選擇性價比最高的模型
    "messages": [
        {
            "role": "user",
            "content": "你是谁"  # 用戶的輸入訊息
        }
    ]
}

# 發送 POST 請求
response = requests.post(url, headers=headers, data=json.dumps(data))

# 檢查響應狀態
if response.status_code == 200:
    # 解析響應數據
    result = response.json()
    # 提取模型返回的訊息內容
    assistant_reply = result['choices'][0]['message']['content']
    print("模型回覆：", assistant_reply)
else:
    print(f"請求失敗，狀態碼：{response.status_code}")
    print("錯誤信息：", response.text)
