import base64
import requests
import json
# 读取并编码本地图片
with open("local_image.jpg", "rb") as image_file:
    base64_image = base64.b64encode(image_file.read()).decode('utf-8')
response = requests.post(
  url="https://openrouter.ai/api/v1/chat/completions",
  headers={
    "Authorization": "Bearer <OPENROUTER_API_KEY>",
    "Content-Type": "application/json"
  },
  data=json.dumps({
    "model": "openai/gpt-4-vision-preview",
    "messages": [
      {
        "role": "user", 
        "content": [
          {
            "type": "text",
            "text": "请描述这张图片"
          },
          {
            "type": "image_url",
            "image_url": {
              "url": f"data:image/jpeg;base64,{base64_image}"
            }
          }
        ]
      }
    ]
  })
)