# 필요한 모듈 임포트
from googleapiclient.discovery import build # Google API 클라이언트 라이브러리를 사용하여 Google APIs 호출
from googleapiclient.http import MediaIoBaseDownload  # Google API 다운로드 기능을 사용하기 위한 클래스
import io 
import pandas as pd 
import gspread
from gspread.exceptions import APIError
from google.oauth2 import service_account # 서비스 계정을 통한 Google API 인증을 위한 라이브러리
import os 
import openai 
import time
import random
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from dotenv import load_dotenv # .env 파일에서 환경 변수를 로드하기 위한 Python 라이브러리
import tiktoken

load_dotenv('./project/credentials/.env')  # env 파일은 credentials에 위치
openai.api_key = os.getenv("OPENAI_API_KEY")
SERVICE_ACCOUNT_FILE = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

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

        # 여기서 파일 이름을 수정하여 .csv를 제거
        # 파일 이름에서 .csv를 제거 (예: "data.csv.xlsx" -> "data.xlsx")
        modified_file_name = file_name.replace('.csv', '') + '.xlsx'  # .csv를 제거하고, 확장자로 .xlsx를 추가
        
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
        spreadsheet_body = {'properties': {'title': modified_file_name}}
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

        time.sleep(1)  # API 호출 사이에 1초 지연 추가

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

# 텍스트 감정 분석 결과를 저장하기 위한 캐시 딕셔너리
sentiment_analysis_cache = {}
def get_sentiment_analysis(text):
    """
    주어진 텍스트에 대한 감정 분석 결과를 반환합니다. 
    결과가 캐시에 있으면 캐시된 값을 사용하고, 그렇지 않으면 perform_sentiment_analysis를 호출합니다.
    """
    if text in sentiment_analysis_cache:
        return sentiment_analysis_cache[text]
    else:
        response = perform_sentiment_analysis(text)
        sentiment_analysis_cache[text] = response
        return response

def perform_sentiment_analysis(text):
    """
    주어진 텍스트에 대해 실제 감정 분석을 수행하고 결과를 반환합니다.
    여기서는 OpenAI API를 사용해 감정 분석을 진행합니다.
    """
    # 텍스트를 적절한 크기의 부분으로 나누기 (예: 1000단어 단위)
    parts = [text[i:i+1000] for i in range(0, len(text), 1000)]
    for part in parts:
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo", 
            messages=[{"role": "system", "content": 
                        """
                        이 텍스트는 한국 웹사이트인 네이버에서 크롤링하고 정제하지 않은 다양한 영화에 대한 리뷰 댓글입니다.
                        이 텍스트의 감정을 분석하고 그 근거를 요약해서 기술하세요.

                        다음 4가지 가이드라인을 따라 분석하세요.
                        1. 영화 리뷰 데이터 평가기준은 다음과 같습니다.
                            영화 평점을 매길 때 고려할 수 있는 평가 요소는 여러 가지가 있으며, 
                            개인적인 취향, 영화의 예술적 및 기술적 특성 등이 포함될 수 있습니다.

                        2. 평가 요소는 다음과 같습니다.
                            - 스토리/대본: 영화의 스토리라인, 구조, 원작에 대한 충실도, 대본의 강도 및 창의성 등이 이에 해당
                            - 연출: 감독의 연출 능력, 장면 전환, 시각적 스타일, 촬영 기법, 전체적인 흐름과 분위기 관리 등
                            - 연기: 주연 및 조연 배우의 연기력, 캐릭터와의 일치도, 캐스팅의 적절성 등이 평가
                            - 시각적 효과: 특수 효과, CGI(컴퓨터 생성 이미지), 메이크업, 의상, 셋 디자인 등 영화의 시각적 요소의 질과 창의성
                            - 음악/사운드트랙: 영화 음악, 배경 음악, 사운드 이펙트, 음향 효과의 품질 및 영화와의 조화를 포함
                            - 편집: 영화의 편집 품질, 장면 전환의 자연스러움, 시간 관리 등이 이에 해당
                            - 감정 이입과 몰입도: 영화가 관객에게 감정적으로 얼마나 큰 영향을 주는지, 관객이 스토리에 얼마나 몰입하는지 등
                            - 주제와 메시지: 영화가 다루는 주제의 중요성, 메시지의 전달 방식 및 효과, 사회적/문화적 의미 등
                            - 오리지널리티와 창의성: 영화의 독창성, 창의적인 요소, 기존 작품들과의 차별점 등
                            - 총괄적 만족도: 영화 전체에 대한 개인적인 만족감, 재관람 의사, 타인 추천 의사 등이 이에 해당

                        3. 아래는 퓨샷 러닝을 위한 코드입니다.
                            1) 첫번째 예시
                                리뷰:정말 재미있는 영화였어요. 다시 보고 싶어요.
                                감정:p
                                근거:영화에 대한 높은 만족도와 긍정적인 감정이 드러남
                            2) 두번째 예시
                                리뷰:최악이었어요. 돈과 시간을 낭비했네요.
                                감정:n
                                근거:영화에 대한 심각한 불만 표현
                            3) 세번째 예시
                                리뷰:괜찮았어요. 하지만 기대했던 것만큼은 아니었어요.
                                감정:o
                                근거:미충족된 기대를 나타냄
                            참고로, 중립적인 감정은 긍정적이거나 부정적인 감정이 명확하지 않은 상태로, 
                            객관적 정보 전달 또는 상황설명에 주로 사용됩니다.

                        4. 근거 요약해서 기술할 때는 한 문장이면서 15자 내로 서술식이 아닌 개조식으로 마침표 없이 작성합니다.

                        출력 형식은 다음과 같이 유지합니다.
                            리뷰:{morphs_sentence}
                            감정:{sentiment_label}
                            근거:{reason}

                        """}, 
                        {"role": "user", "content": text}], 
            temperature=1.0, # 1일 경우, 모델은 훈련 시 가장 자연스럽고 예측 가능한 결과를 생성하는 데 도움
                                # 1보다 큰 값으로 설정되면, 더 다양하고 예측하기 어려운 텍스트를 생성할 수 있게 함
            max_tokens=1500,
            top_p=1.0 # top_p=1은 확률 분포의 100%를 고려하겠다는 의미
                )
    
    sentiment_analysis = response.choices[0].message.content
    sentiment_label = 'p' if '긍정' in sentiment_analysis else 'n' if '부정' in sentiment_analysis else 'o'
    reason = sentiment_analysis.split('근거:', 1)[-1].strip() # '근거:' 문자열 이후의 텍스트만 추출
  
    return response, sentiment_analysis, sentiment_label, reason


def analyze_sentiment_with_few_shot(data):
    updated_data = []
    total_prompt_length, total_response_length = 0, 0
    encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
    for item in data:
        text = item['morphs_sentence']
        response, _, sentiment_label, reason = perform_sentiment_analysis(text)
        item['gpt_analysis'] = sentiment_label 
        item['gpt_reason'] = reason
        updated_data.append(item)

        total_prompt_length += response.usage.prompt_tokens
        total_response_length += response.usage.completion_tokens

        text_token = encoding.encode(text)
        len_token = len(text_token)
        print("분석 텍스트 토큰의 개수: ",len_token)

        prompt_input_text = response.usage.prompt_tokens
        prompt_output_text = response.usage.completion_tokens
        cost_by_text = (0.0015/1000) * (prompt_input_text) + (0.0020/1000)*(prompt_output_text)

        print('Prompt 결과')
        print(f"리뷰:{text}\n감정:{sentiment_label}\n근거:{reason}\n")
        print("텍스트 분석 비용: ", cost_by_text,"\n")
        print("==========")

    total_cost, total_tokens = calculate_cost(total_prompt_length, total_response_length, "gpt-3.5-turbo")
    
    return updated_data, total_cost, total_tokens

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
    sheet.update_acell('E1', 'gpt_reason')

     # 데이터를 작은 단위로 나누어 업데이트
    batch_size = 10  # 한 번에 업데이트할 행의 수
    for i in range(0, len(data), batch_size):
        batch_data = data[i:i+batch_size]
        cell_list = sheet.range(f'D{i+2}:E{i+len(batch_data)+1}')
        for j, item in enumerate(batch_data):
            cell_list[j*2].value = item['gpt_analysis']
            cell_list[j*2+1].value = item['gpt_reason']
        # 기존 코드 대신 safe_update_cells 함수 사용
        try:
            safe_update_cells(sheet, cell_list)
        except gspread.exceptions.APIError as e:
            print(f"여러 번의 재시도 후에도 셀을 업데이트하지 못했습니다: {e}")
            break  # 추가 처리가 필요할 수 있음
            
        time.sleep(1)  # API 호출 사이에 지연 추가

def safe_update_cells(sheet, cell_list):
    """API 호출 실패 시 지수 백오프를 사용하여 셀 업데이트를 재시도하는 함수"""
    max_attempts = 5
    for attempt in range(max_attempts):
        try:
            sheet.update_cells(cell_list)
            print("업데이트 성공")
            return  # 업데이트가 성공하면 루프를 빠져나옴
        except gspread.exceptions.APIError as e:
            if e.response.status_code == 503 and attempt < max_attempts - 1:
                # 지수 백오프 전략을 사용하여 재시도 대기 시간 설정
                wait_time = (2 ** attempt) + (random.randint(0, 1000) / 1000)
                print(f"서비스를 이용할 수 없습니다. {wait_time}초 후에 다시 시도합니다...")
                time.sleep(wait_time)
            else:
                raise  # 마지막 시도에서도 실패하거나 다른 종류의 APIError인 경우 예외를 다시 발생

# 감정 분석 결과에 대한 평가 지표 계산 함수
def calculate_evaluation_metrics(data):
    polarity = [item['polarity_naver'] for item in data]  # [개별입력] F1 score의 기준이 되는 column명
    gpt_analysis = [item['gpt_analysis'] for item in data]  # 모델에 의한 라벨
    """
    정확도(accuracy) : 전체 항목 중에서 올바르게 예측된 항목의 비율
    정밀도(precision) : 모델이 True라고 예측한 항목 중 실제로 True인 항목의 비율
    재현율(recall) : 실제 True인 항목 중 모델이 True로 예측한 항목의 비율
    F1 스코어: 정밀도와 재현율의 조화 평균을 나타내는 지표로, 
               분류 모델의 성능을 종합적으로 평가할 때 사용
               0에서 1 사이의 값으로 나타나며, 1에 가까울수록 모델의 성능이 뛰어난 것으로 간주
               특히 데이터 라벨 간의 균형이 맞지 않거나 한쪽 라벨의 성능이 더 중요한 경우에 유용
               - 계산식: F1=2*{(precision*recall)/(precision+recall)}
    """
    accuracy = accuracy_score(polarity, gpt_analysis)
    precision = precision_score(polarity, gpt_analysis, average='weighted', labels=['p', 'n', 'o'], zero_division=0)
    recall = recall_score(polarity, gpt_analysis, average='weighted', labels=['p', 'n', 'o'], zero_division=0)
    f1 = f1_score(polarity, gpt_analysis, average='weighted', labels=['p', 'n', 'o'], zero_division=0)

    return accuracy, precision, recall, f1

def calculate_cost(total_prompt_length, total_response_length, model):
    """
    함수 설명: 토큰 비용 계산 모듈
    특이 사항: 모델별 기본 토큰 비용 설정하여 계산
    input: 0.0015/1K tokens 
    output: 0.0020/1K tokens
    """
    # "gpt-3.5-turbo" 모델의 입력 및 출력 토큰당 비용
    token_price = {"gpt-3.5-turbo": {"input":0.0015,
                                      "output":0.002},} # instruct모델 

    # 총 비용
    total_cost = token_price[model]["input"] * (total_prompt_length/1000) + (token_price[model]["output"]*total_response_length/1000)
    # 총 토큰 수
    total_tokens = total_prompt_length + total_response_length
    
    return total_cost, total_tokens




# 메인 로직
if __name__ == '__main__':
    start_time = time.time()  # 분석 시작 시간 측정
    
    folder_id = os.getenv("GOOGLE_FOLDER_ID")
    """
    Google Drive 폴더 ID (folder_id) 확인 방법
    : Google Drive에서 해당 폴더를 열고 브라우저의 주소창에서 폴더 ID를 확인
      (주소 형식: https://drive.google.com/drive/folders/folder-id?usp=sharing)
    """
    spreadsheet_info = find_and_convert_csv_files(folder_id)
    for file_name, spreadsheet_url in spreadsheet_info:
        data = read_spreadsheet(spreadsheet_url)
        updated_data, total_cost, total_tokens = analyze_sentiment_with_few_shot(data)
        save_results(spreadsheet_url, updated_data)
        accuracy, precision, recall, f1 = calculate_evaluation_metrics(updated_data)
        time.sleep(2)  # 각 스프레드시트 처리 사이에 n초 지연 추가


    end_time = time.time()  # 분석 종료 시간 측정
    total_time = end_time - start_time  # 총 소요 시간 계산

    print(f"파일명: {file_name}, 스프레드시트 URL: {spreadsheet_url}")
    print(f"총 비용: ${total_cost:.4f}, 총 토큰 : {total_tokens: .1f}, 총 분석 시간: {total_time:.2f}초")
    print(f"정확도: {accuracy:.2f}, 정밀도: {precision:.2f}, 재현율: {recall:.2f}, F1 스코어: {f1:.2f}") 
    print("모든 파일의 분석이 완료되었습니다. 각 스프레드 시트를 확인해주세요.")
