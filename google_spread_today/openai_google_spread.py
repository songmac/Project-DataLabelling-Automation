import gspread  # gspread 라이브러리를 사용해 Google 스프레드시트 작업을 수행
from oauth2client.service_account import ServiceAccountCredentials  # Google API 인증을 위한 라이브러리
import os
import openai
from dotenv import load_dotenv

load_dotenv()


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
    for item in data:
        text = item['morphs_sentence']  # 'morphs_sentence' 컬럼에서 분석할 텍스트 선택
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
        
        # 응답을 긍정 또는 부정으로 해석
        # 예시 로직: 응답 텍스트에 따라 긍정 'p' 또는 부정 'n'으로 분류
        sentiment_label = 'p' if '긍정' in sentiment else 'n'
        
        # 결과를 원래 데이터에 추가
        item['openai_analysis'] = sentiment_label
        updated_data.append(item)
    return updated_data





def save_results(spreadsheet_url, data):
    scope = ['https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name('C:/Users/selena/songmac/Project-DataLabelling-Automation/credentials/bustling-vim-415105-83d345abec9e.json', scope)
    client = gspread.authorize(creds)
    sheet = client.open_by_url(spreadsheet_url).sheet1
    for index, item in enumerate(data, start=2):  # 결과 저장 시작 행 설정
        sheet.update_cell(index, 2, item)  # 결과를 스프레드시트의 지정된 셀에 저장




spreadsheet_url = 'https://docs.google.com/spreadsheets/d/1_Pcu2ZXgnwa_gkGpU7nWUgTIUuXrWkGz_LeV96OWKtA/edit#gid=1394694346'

data = read_spreadsheet(spreadsheet_url)  # 스프레드시트에서 데이터 읽기
sentiment_analysis_results = analyze_sentiment(data)  # 데이터에 대한 감정 분석 수행
save_results(spreadsheet_url, sentiment_analysis_results)  # 분석 결과를 스프레드시트에 저장
print("분석이 완료되었습니다. 스프레드 시트를 확인해주세요.")

