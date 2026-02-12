from google import genai

# {/* 配置 API易 服务 */}
client = genai.Client(
    api_key="api-key",  # 您的 API易 密钥
    http_options={"base_url": "https://api.apiyi.com"},
)

# {/* 使用 Gemini 模型生成内容 */}
response = client.models.generate_content(
    model="gemini-3-pro-preview", contents="您的提示词"
)
print(response.text)
