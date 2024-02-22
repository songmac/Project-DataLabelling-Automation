import gspread
from oauth2client.service_account import ServiceAccountCredentials

def save_results(spreadsheet_url, data):
    scope = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name('your-google-credentials.json', scope)
    client = gspread.authorize(creds)
    sheet = client.open_by_url(spreadsheet_url).sheet1
    for index, item in enumerate(data, start=2):  # 결과 저장 시작 행 설정
        sheet.update_cell(index, 2, item)  # 결과를 스프레드시트의 지정된 셀에 저장
