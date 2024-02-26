import gspread  # gspread 라이브러리를 사용해 Google 스프레드시트 작업을 수행
from oauth2client.service_account import ServiceAccountCredentials  # Google API 인증을 위한 라이브러리
import os
import openai

from dotenv import load_dotenv
load_dotenv()

import sys
sys.path.append('C:/Users/selena/songmac/Project-DataLabelling-Automation/')
from check_token import calculate_cost





def read_spreadsheet(spreadsheet_url):
    # Google 스프레드시트 접근을 위한 스코프 설정
    scope = ['https://www.googleapis.com/auth/drive']

    # 서비스 계정 키 파일을 사용해 인증 정보 생성
    creds = ServiceAccountCredentials.from_json_keyfile_name('C:/Users/selena/songmac/Project-DataLabelling-Automation/credentials/bustling-vim-415105-83d345abec9e.json', scope)

    client = gspread.authorize(creds)  # gspread 클라이언트 생성
    sheet = client.open_by_url(spreadsheet_url).sheet1  # 스프레드시트 URL로 첫 번째 시트 열기
    data = sheet.get_all_records()  # 모든 데이터를 딕셔너리 리스트로 읽기
    return data  # 읽은 데이터 반환


def analyze_sentiment(data):
    openai.api_key = os.getenv('OPENAI_API_KEY')
    updated_data = []  # 갱신된 데이터를 저장할 리스트
    total_prompt_length = 0  # 프롬프트 길이 합계 초기화
    total_response_length = 0  # 응답 길이 합계 초기화

    for item in data:
        text = item['morphs_sentence']  # 'morphs_sentence' 컬럼에서 분석할 텍스트 선택

        # 대화 시작을 위한 시스템 메시지 추가
        messages = [{"role": "system", "content": """이 텍스트의 감정을 분석해주세요. 
                     중립적인 감정은 긍정적이거나 부정적인 감정이 명확하지 않은 상태로, 객관적 정보 전달 또는 상황설명에 주로 사용됩니다.
                     """},
                    {"role": "user", "content": text}]  # 사용자 메시지 추가

        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            temperature=0.5,
            max_tokens=1000
        )

        sentiment = response.choices[0].message.content

        # 분석 후 응답 길이를 합산
        total_prompt_length += len(text) 
        total_response_length += len(sentiment) 



        # 응답을 긍정(p)/부정(n)으로 해석
        # sentiment_label = 'p' if '긍정' in sentiment else 'n'

        # 응답을 긍정(p)/부정(n)/중립(o)으로 해석
        sentiment_label = 'p' if '긍정' in sentiment else ('n' if '부정' in sentiment else 'o')

        
        # 결과를 원래 데이터에 추가
        item['gpt_analysis'] = sentiment_label  # 'gpt_analysis'로 컬럼 이름 변경
        updated_data.append(item)

    # 분석 완료 후 총 비용 계산
    total_cost = calculate_cost(total_prompt_length, total_response_length, "gpt-3.5-turbo")
    print(f"총 비용: ${total_cost:.4f}")

    return updated_data  # for 루프가 종료된 후 결과 반환


def save_results(spreadsheet_url, data):
    scope = ['https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name('C:/Users/selena/songmac/Project-DataLabelling-Automation/credentials/bustling-vim-415105-83d345abec9e.json', scope)
    client = gspread.authorize(creds)
    sheet = client.open_by_url(spreadsheet_url).sheet1

    # 'gpt_analysis' 결과를 저장할 열을 지정
    column_letter_for_analysis = 'D'  
    analysis_results = [item['gpt_analysis'] for item in data]
    
    # 업데이트할 셀 범위를 지정
    range_to_update = f'{column_letter_for_analysis}2:{column_letter_for_analysis}{len(data)+1}'
    
    # 범위와 함께 결과 데이터를 업데이트
    sheet.update(range_to_update, [[result] for result in analysis_results])





spreadsheet_url = 'https://docs.google.com/spreadsheets/d/1fFARxEcogbDVDG-VdwsEIf9Z2neBnVCblT2xkO_Je88/edit#gid=516480554'
data = read_spreadsheet(spreadsheet_url)  # 스프레드시트에서 데이터 읽기
sentiment_analysis_results = analyze_sentiment(data)  # 데이터에 대한 감정 분석 수행
save_results(spreadsheet_url, sentiment_analysis_results)  # 분석 결과를 스프레드시트에 저장
print("분석이 완료되었습니다. 스프레드 시트를 확인해주세요.")

