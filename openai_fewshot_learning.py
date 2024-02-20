import os
import openai
from dotenv import load_dotenv

load_dotenv()


openai.api_key = os.getenv('OPENAI_API_KEY')

def get_completion_from_messages(messages, model="gpt-3.5-turbo", temperature=0):
    response = openai.chat.completions.create(
        model= model,
        messages = messages,
        temperature = temperature
    )

    return response.choices[0].message.content

context = [ {'role':'system', 'content':"""
             
    너는 뉴스데이터에 감정 분석을 하고 문맥을 고려해서 전체적인 내용이 긍정/부정인지를 판단하고 라벨링을 해줘야 해.
    사용자에게 질문을 차례대로 한개씩 해줘.
    해당하는 질문에 모든 답변을 받으면, 입력을 마쳤는지 확인해.
    그 다음에 원본데이터와 원본데이터의 전반적인 감정이 긍정인지 부정인지 라벨링한 데이터를 
    분류결과를 positive는 p로,negative는 n으로 기입 후 csv 파일로 저장해서 사용자에게 전달해줘.

    질문은 아래 순서대로 하면돼 :

    1. 분석하려는 컨텍스트 개수를 알려주세요.
    2. 분석하려는 컨텍스트를 순서대로 입력해주세요.
    3. 입력을 마치셨나요?
    4. 분석 결과를 저장한 csv 파일입니다.            
             """} ]

result = get_completion_from_messages(context)
print(result)

