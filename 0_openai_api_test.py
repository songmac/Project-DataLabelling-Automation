# OpenAI 라이브러리 버전이 1.0.0 이상으로 업데이트 되었음
# 코드베이스를 새 API 인터페이스로 자동 업그레이드하거나, 
# 구 버전의 라이브러리를 사용하도록 설치를 고정하는 두 가지 해결방법 존재

import os
import openai
# from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()


openai.api_key = os.getenv('OPENAI_API_KEY')
# client = OpenAI(
#     api_key = os.getenv('OPENAI_API_KEY')
# )

def get_completion_from_messages(messages, model="gpt-3.5-turbo", temperature=0):
    response = openai.chat.completions.create( #openai.ChatCompletion.create
        model= model,
        messages = messages,
        temperature = temperature
    )

    return response.choices[0].message.content
            # response.choices[0].text.strip()
            # response.choices[0].message['content']

context = [ {'role':'system', 'content':"나한테 인사해줘."} ]

result = get_completion_from_messages(context)
print(result)