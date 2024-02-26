import os
import openai
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

# OpenAI API 키 설정
openai.api_key = os.getenv('OPENAI_API_KEY')

def chat_with_gpt(messages, model="gpt-3.5-turbo", temperature=0.5):
    """
    GPT 모델과의 연속적인 대화를 위한 함수.
    
    Args:
    - messages (list): 대화 내역을 담은 리스트. 각 메시지는 {'role': 'system/user', 'content': '메시지 내용'} 형식의 딕셔너리.
    - model (str): 사용할 모델의 이름.
    - temperature (float): 응답의 다양성을 결정하는 온도값.
    
    Returns:
    - str: 모델의 최신 응답.
    """

    response = openai.chat.completions.create(
        model=model,
        prompt="\n".join([f"{msg['role']}: {msg['content']}" for msg in messages]),
        temperature=temperature,
        max_tokens=150,
        n=1,
        stop=["\n", " User:", " AI:"]
    )
    return response.choices[0].text.strip()

# 초기 시스템 메시지 설정
context = [{'role': 'system', 'content': "너는 데이터 감정 라벨링 전문가야."}]

# 연속적인 대화를 위한 반복문
for _ in range(3):  # 3번의 질문과 응답을 진행
    user_input = input("User: ")  # 사용자 입력 받기
    context.append({'role': 'user', 'content': user_input})  # 사용자 입력을 컨텍스트에 추가
    
    # AI 응답 받기
    ai_response = chat_with_gpt(context)
    print("AI:", ai_response)
    
    # AI 응답을 컨텍스트에 추가
    context.append({'role': 'assistant', 'content': ai_response})





