import gspread  # gspread 라이브러리를 사용해 Google 스프레드시트 작업을 수행
from oauth2client.service_account import ServiceAccountCredentials  # Google API 인증을 위한 라이브러리
import os
import openai
from utils import calculate_cost # 토큰 비용 계산 모듈
from utils import column_index_to_letter # Column 인덱스를 문자로 변환하는 모듈
from dotenv import load_dotenv 
load_dotenv('./project/credentials/.env') # env 파일 위치는 credentials 로 설정



def read_spreadsheet(spreadsheet_url):
    """
    함수 설명
    1. 구글 스프레드 시트 파일 1개 단위로 데이터를 읽어옴
    2. Google Cloud Platform에 프로젝트 생성, 서비스 계정 생성, json 파일 다운로드 후 정상 실행 가능
    3. Google Cloud Platform에서 2가지 API(Google Sheets API, Google Drive API) 활성화 필요
    """

    # Google 스프레드시트 접근을 위한 스코프 설정
    scope = ['https://www.googleapis.com/auth/drive']

    # [개별입력] 서비스 계정에서 json 키 파일을 credentials 폴더에 다운로드 후 json 파일명 입력 
    creds = ServiceAccountCredentials.from_json_keyfile_name('./project/credentials/bustling-vim-415105-83d345abec9e.json', scope)

    client = gspread.authorize(creds)  # gspread 클라이언트 생성
    sheet = client.open_by_url(spreadsheet_url).sheet1  # 스프레드시트 URL로 첫 번째 시트 열기
    data = sheet.get_all_records()  # 모든 데이터를 딕셔너리 리스트로 읽기
    return data  # 읽은 데이터 반환


def analyze_sentiment(data):
    """
    함수 설명
    1. 전처리된 데이터를 OpenAI API에 전송하여 감정 분석을 수행
    2. 라벨링한 결과를 원본 구글 스프레드 시트의 새로운 column에 저장
    3. 토큰 사용길이에 따른 예상 청구 비용 출력
    """

    openai.api_key = os.getenv('OPENAI_API_KEY')
    updated_data = []  # 갱신된 데이터를 저장할 리스트
    total_prompt_length = 0  # 프롬프트 길이 합계 초기화
    total_response_length = 0  # 응답 길이 합계 초기화

    for item in data:
        text = item['morphs_sentence']  # 'morphs_sentence' 컬럼에서 분석할 텍스트 선택

        # 대화 시작을 위한 시스템 메시지 추가
        messages = [{"role": "system", "content": """이 텍스트의 감정을 분석해주세요. 
                     중립적인 감정은 긍정적이거나 부정적인 감정이 명확하지 않은 상태로, 
                     객관적 정보 전달 또는 상황설명에 주로 사용됩니다.
                     """},
                    {"role": "user", "content": text}]  # 사용자 메시지 추가

        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            temperature=0,
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

        
        # 결과를 원래 데이터 파일에 추가
        item['gpt_analysis'] = sentiment_label 
        updated_data.append(item)

    # 분석 완료 후 총 비용 계산
    total_cost = calculate_cost(total_prompt_length, total_response_length, "gpt-3.5-turbo")
    print(f"총 비용: ${total_cost:.4f}")

    return updated_data  # for 루프가 종료된 후 결과 반환



def save_results(spreadsheet_url, data):
    # Google 스프레드시트와의 인증 및 연결 설정
    scope = ['https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name('./project/credentials/bustling-vim-415105-83d345abec9e.json', scope)
    client = gspread.authorize(creds)
    sheet = client.open_by_url(spreadsheet_url).sheet1

    # 새로운 컬럼명을 'D1'에 추가
    new_column_name = 'gpt_analysis'
    new_column_index = 4  # 'D' 열의 인덱스
    new_column_letter = column_index_to_letter(new_column_index)  # 'D'
    
    # 'D1'에 새로운 컬럼명 기입
    sheet.update_acell(f'{new_column_letter}1', new_column_name)

    # 'D2'부터 시작하여 데이터 저장
    for i, item in enumerate(data, start=2):  # 데이터 리스트의 인덱스 시작을 2로 설정
        # 해당 열의 행에 데이터 항목의 'gpt_analysis' 값 저장
        sheet.update_acell(f'{new_column_letter}{i}', item['gpt_analysis'])


if __name__ == '__main__':
    spreadsheet_url = 'https://docs.google.com/spreadsheets/d/1bh33yfvQnevEuT64DX9EREtgTm4bMsFeqz-mS_qyMD0/edit#gid=1619758602'
    data = read_spreadsheet(spreadsheet_url)
    sentiment_analysis_results = analyze_sentiment(data)  # 데이터에 대한 감정 분석 수행
    save_results(spreadsheet_url, data)
    print("분석이 완료되었습니다. 스프레드 시트를 확인해주세요.")