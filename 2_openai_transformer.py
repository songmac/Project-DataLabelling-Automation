# 기본 스크립트 (예: main.py)
import os
import openai
from dotenv import load_dotenv
from check_token import calculate_cost  # 모듈 import

# 환경 변수 로드
load_dotenv()

# OpenAI API 키 설정
openai.api_key = os.getenv('OPENAI_API_KEY')

def chat_with_gpt(messages, model="gpt-3.5-turbo", temperature=0.5):
    """
    GPT 모델과의 연속적인 대화를 위한 함수입니다.
    """
    response =  openai.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=150,
        n=1,
        stop=None
    )
    response_text = response.choices[0].message.content
    response_tokens = len(response_text.split())  # 응답의 토큰 수 계산
    cost = calculate_cost(0, response_tokens, model)  # 비용 계산, 프롬프트 길이는 0으로 가정
    print("AI:", response_text)
    print(f"이 요청에 대한 비용: ${cost:.4f}")
    return response_text

# 사용 예시
context = [
    {"role": "system", "content": """당신은 뉴스 데이터(csv 파일) 감정 분석을 하고 문맥을 고려하여 
                                     내용이 긍정적인지 부정적인지 판단하고 라벨링하는 전문 분석가입니다."""},
    {"role": "user", "content": """소셜미디어 교류는 인스턴트 음식을 먹는 것과 같습니다. 
                                   이 문장의 감정을 긍정/부정/중립으로 분석해줘. 이유는 말하지 않아도 돼."""}
]

ai_response = chat_with_gpt(context, "gpt-3.5-turbo")