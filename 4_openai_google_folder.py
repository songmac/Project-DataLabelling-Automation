# 필요한 모듈 임포트
from googleapiclient.discovery import build # Google API 클라이언트 라이브러리를 사용하여 Google APIs 호출
from googleapiclient.http import MediaIoBaseDownload  # Google API 다운로드 기능을 사용하기 위한 클래스
import io 
import pandas as pd 
import gspread 
from google.oauth2 import service_account # 서비스 계정을 통한 Google API 인증을 위한 라이브러리 # pip install --upgrade google-auth으로 업그레이드
import os 
import openai 
from utils import calculate_cost
from dotenv import load_dotenv # .env 파일에서 환경 변수를 로드하기 위한 Python 라이브러리

# .env 파일 및 서비스 계정 정보 로드
load_dotenv('./project/credentials/.env')  # env 파일은 credentials에 위치

# Google Cloud Platform 설정
SERVICE_ACCOUNT_FILE = './project/credentials/bustling-vim-415105-83d345abec9e.json' #[개별입력] json key file명
"""
서비스 계정 파일 (SERVICE_ACCOUNT_FILE) 설정 방법
: 다운로드한 JSON 파일을 프로젝트의 credentials 폴더 내에 저장하고, 
  파일 경로를 SERVICE_ACCOUNT_FILE 변수에 할당
"""
SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
drive_service = build('drive', 'v3', credentials=credentials)
sheets_service = build('sheets', 'v4', credentials=credentials)
gspread_client = gspread.authorize(credentials)

# Google Drive 폴더 내 CSV 파일 탐색 및 변환 로직
def find_and_convert_csv_files(folder_id):
    """
    함수 설명
    1. 구글 폴더 id를 입력하여 폴더 내 모든 csv파일을 스프레드 시트 형식으로 변환
    2. 생성한 스프레드 시트 url 저장
    """
    response = drive_service.files().list(q=f"'{folder_id}' in parents and mimeType='text/csv'", spaces='drive', fields='nextPageToken, files(id, name)').execute()
    csv_files = response.get('files', [])
    spreadsheet_info = []

    for file in csv_files:
        file_id = file['id']
        file_name = file['name']
        
        # CSV 파일 다운로드 및 내용 읽기
        request = drive_service.files().get_media(fileId=file_id)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()
        fh.seek(0)
        df = pd.read_csv(fh)
        
        # 새 스프레드시트 생성 및 스프레드시트에 CSV 내용 쓰기
        spreadsheet_body = {'properties': {'title': file_name}}
        spreadsheet = sheets_service.spreadsheets().create(body=spreadsheet_body).execute()
        spreadsheet_id = spreadsheet.get('spreadsheetId')
        move_file_to_folder(spreadsheet_id, folder_id)  # 파일을 지정한 폴더로 이동
        range_name = 'A1'
        value_input_option = 'RAW'
        values = [df.columns.values.tolist()] + df.values.tolist()
        body = {'values': values}
        sheets_service.spreadsheets().values().update(spreadsheetId=spreadsheet_id, range=range_name, valueInputOption=value_input_option, body=body).execute()
        
        # 생성된 스프레드시트 URL 저장
        spreadsheet_url = f'https://docs.google.com/spreadsheets/d/{spreadsheet_id}'
        spreadsheet_info.append((file_name, spreadsheet_url))
    
    return spreadsheet_info

# 파일을 새로운 폴더로 이동하는 함수
def move_file_to_folder(file_id, folder_id):
    """
    함수 설명 
    1. 스프레드시트 생성 후 해당 스프레드시트를 지정한 폴더로 이동
    """
    file = drive_service.files().get(fileId=file_id, fields='parents').execute()
    previous_parents = ",".join(file.get('parents'))
    drive_service.files().update(fileId=file_id, addParents=folder_id, removeParents=previous_parents, fields='id, parents').execute()

# 스프레드시트 읽기 및 감정 분석 함수
def read_spreadsheet(spreadsheet_url):
    spreadsheet = gspread_client.open_by_url(spreadsheet_url)
    sheet = spreadsheet.sheet1
    return sheet.get_all_records()

def analyze_sentiment(data, file_name):
    openai.api_key = os.getenv('OPENAI_API_KEY')
    updated_data = []
    total_prompt_length, total_response_length = 0, 0

    for item in data:
        text = item['morphs_sentence']
        response = openai.chat.completions.create(model="gpt-3.5-turbo", messages=[{"role": "system", "content": "분석 요청"}, {"role": "user", "content": text}], temperature=0, max_tokens=1000)
        sentiment = response.choices[0].message.content
        sentiment_label = 'p' if '긍정' in sentiment else 'n' if '부정' in sentiment else 'o'
        item['gpt_analysis'] = sentiment_label 
        updated_data.append(item)
        total_prompt_length += len(text)
        total_response_length += len(sentiment)

    total_cost = calculate_cost(total_prompt_length, total_response_length, "gpt-3.5-turbo")
    return updated_data, total_cost

# 스프레드시트에 결과 저장 함수
def save_results(spreadsheet_url, data):
    """
    함수 설명
    1. D1 열에 gpt_analysis 라는 column명 생성
    2. D2 열부터 감정분석 결과를 차례로 입력
    """
    spreadsheet = gspread_client.open_by_url(spreadsheet_url)
    sheet = spreadsheet.sheet1
    sheet.update_acell('D1', 'gpt_analysis')
    for i, item in enumerate(data, start=2):
        sheet.update_acell(f'D{i}', item['gpt_analysis'])

# 메인 로직
if __name__ == '__main__':
    folder_id = '1y97vUbZ4wFMjWLLF5bEJ2-jr-0lMIUva'  # [개별입력] 서비스 계정과 굥유한 구글 폴더id
    """
    Google Drive 폴더 ID (folder_id) 확인 방법
    : Google Drive에서 해당 폴더를 열고 브라우저의 주소창에서 폴더 ID를 확인
      (주소 형식: https://drive.google.com/drive/folders/folder-id?usp=sharing)
    """
    spreadsheet_info = find_and_convert_csv_files(folder_id)
    for file_name, spreadsheet_url in spreadsheet_info:
        data = read_spreadsheet(spreadsheet_url)
        sentiment_analysis_results, total_cost = analyze_sentiment(data, file_name)
        save_results(spreadsheet_url, sentiment_analysis_results)
        print(f"파일명: {file_name}, 스프레드시트 URL: {spreadsheet_url}, 총 비용: ${total_cost:.4f}")
    print("모든 파일의 분석이 완료되었습니다. 각 스프레드 시트를 확인해주세요.")
