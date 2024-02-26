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
   
    response =  openai.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=1000,
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
    {"role": "user", "content": """ 아래 문장 10개의 감정을 각각 긍정/부정/중립으로 분석해줘. 
                                    표시는 {번호, 감정분석결과} 이렇게 나타내줘. 이유는 말하지 않아도 돼.
                                    1. 소셜미디어 교류는 인스턴트 음식을 먹는 것과 같습니다.
                                    2. 가구업계 1 2위 업체들도 실적부진에서 예외는 아니었다.
                                    3. 공약이 없으니 국민이 희망을 볼 수도 없다”고 지적했다.
                                    4. 어드바이저리 부문에서도 눈에 띄는 성과를 기록했다.
                                    5. 여야는 타임오프제 도입 필요성에는 공감대를 이뤘다.
                                    6. 업력별로는 초기 창업기업의 일자리 창출효과가 컸다.
                                    7. 미국과 동맹인 한국은 머리가 복잡해졌다.
                                    8. 민주당은 후보 선출을 위한 경선 중이다.
                                    9. 부가수익 창출이 가능한 공유경제모델이다.
                                    10. 사법부도 제한적인 재판 운영에 돌입했다. 
                                    """}
]

ai_response = chat_with_gpt(context, "gpt-3.5-turbo")