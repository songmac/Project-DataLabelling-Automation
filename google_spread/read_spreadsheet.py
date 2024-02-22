import gspread  # gspread 라이브러리를 사용해 Google 스프레드시트 작업을 수행
from oauth2client.service_account import ServiceAccountCredentials  # Google API 인증을 위한 라이브러리

def read_spreadsheet(spreadsheet_url):
    # Google 스프레드시트 접근을 위한 스코프 설정
    scope = ['https://www.googleapis.com/auth/drive']
    # 서비스 계정 키 파일을 사용해 인증 정보 생성
    creds = ServiceAccountCredentials.from_json_keyfile_name('bustling-vim-415105-83d345abec9e.json', scope)
    """
    Google Cloud console API key 불러오기 절차
    1. Google Cloud Console에서 프로젝트를 선택하거나 생성
    2. API 및 서비스 -> 사용자 인증 정보로 이동하여 서비스 계정을 만듦
    3. 서비스 계정에 대해 키 생성을 선택하고 JSON 키 유형을 선택
    4. 생성된 JSON 키 파일을 다운로드하고, 스크립트가 있는 디렉토리에 저장
    5. 스크립트에서 from_json_keyfile_name 함수의 인자로 JSON 키 파일의 경로를 제공 (예: 'your-google-credentials.json')
    """
    client = gspread.authorize(creds)  # gspread 클라이언트 생성
    sheet = client.open_by_url(spreadsheet_url).sheet1  # 스프레드시트 URL로 첫 번째 시트 열기
    data = sheet.get_all_records()  # 모든 데이터를 딕셔너리 리스트로 읽기
    return data  # 읽은 데이터 반환
