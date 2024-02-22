import os
import openai
from dotenv import load_dotenv

load_dotenv()


def analyze_sentiment(data):
    openai.api_key = os.getenv('OPENAI_API_KEY')
    updated_data = []  # 갱신된 데이터를 저장할 리스트
    for item in data:
        text = item['sentence']  # 'sentence' 컬럼에서 분석할 텍스트 선택
        response = openai.chat.completions.create(
            engine="davinci",
            prompt=f"이 텍스트의 감정을 분석해주세요: {text}",
            temperature=0.7,
            max_tokens=60,
            top_p=1.0,
            frequency_penalty=0.0,
            presence_penalty=0.0
        )
        sentiment = response.choices[0].message.content
        
        # 여기서 응답을 긍정 또는 부정으로 해석하는 로직 추가
        # 예시 로직: 응답 텍스트에 따라 긍정 'p' 또는 부정 'n'으로 분류
        sentiment_label = 'p' if '긍정' in sentiment else 'n'
        
        # 결과를 원래 데이터에 추가
        item['openai_analysis'] = sentiment_label
        updated_data.append(item)
    return updated_data
