from openai import OpenAI
import os

api_key = os.getenv("GPT_API_KEY")
if not api_key:
    raise RuntimeError("GPT_API_KEY 未設定")

client = OpenAI(api_key=api_key)

print(">> call start")
resp = client.chat.completions.create(
    model="gpt-3.5-turbo",  # 改成你有權限的模型
    messages=[{"role": "user", "content": "ping"}],
    max_tokens=8,
    timeout=30,             # 避免卡住
)
print("<< call done")
print(resp)
