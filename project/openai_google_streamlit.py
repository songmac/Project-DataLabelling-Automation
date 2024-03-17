import streamlit as st
from googleapiclient.discovery import build # Google API 클라이언트 라이브러리를 사용하여 Google APIs 호출 
import pandas as pd 
import gspread
from google.oauth2 import service_account # 서비스 계정을 통한 Google API 인증을 위한 라이브러리
import os 
import openai 
import time
import random
from dotenv import load_dotenv # .env 파일에서 환경 변수를 로드하기 위한 Python 라이브러리
from datetime import datetime

# 환경변수 로드
load_dotenv('./project/credentials/.env') 
# OpenAI API 인증
openai.api_key = os.getenv("OPENAI_API_KEY")
# Google API 인증
SERVICE_ACCOUNT_FILE = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
SCOPES = ['https://www.googleapis.com/auth/drive', 'https://www.googleapis.com/auth/spreadsheets']
credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
drive_service = build('drive', 'v3', credentials=credentials)
sheets_service = build('sheets', 'v4', credentials=credentials)
gspread_client = gspread.authorize(credentials)



# 스트림릿 UI 설정
def main():
    st.title("감정 분석 웹 서비스")

    mode = st.sidebar.selectbox("모드 선택", ["텍스트 입력", "파일 업로드"])

    if mode == "텍스트 입력":
        text = st.text_area("리뷰를 입력하세요.")
        if st.button("분석하기"):
            if text:
                sentiment, reason = perform_sentiment_analysis(text)
                st.write("### 분석 결과")
                st.markdown(f"""
                **문장:** {text}

                **감정:** {sentiment}

                **결과 해석:** {reason}
                """)
            else:
                st.error("텍스트를 입력해주세요.")

    elif mode == "파일 업로드":
        uploaded_files = st.file_uploader("CSV 또는 Excel 파일을 업로드하세요.", type=["csv", "xlsx"], accept_multiple_files=True)
        column_name = st.text_input("리뷰가 포함된 열의 이름을 입력하세요.", "morphs_sentence")
        if uploaded_files and st.button("분석 요청"):
            save_and_analyze_file(uploaded_files, column_name)  # 수정된 호출 방식

def save_and_analyze_file(uploaded_files, column_name):
    """
    1. 업로드된 파일을 저장
    2. 감정 분석을 수행
    3. 스프레드시트에 결과를 저장
    """
    for uploaded_file in uploaded_files:
        try:
            # 파일 확장자를 기반으로 파일 타입 결정
            file_name = uploaded_file.name
            if file_name.endswith('.csv'):
                df = pd.read_csv(uploaded_file)
            elif file_name.endswith('.xlsx'):
                df = pd.read_excel(uploaded_file)
            else:
                st.error("지원되지 않는 파일 형식입니다: " + file_name)
                continue

            if column_name not in df.columns:
                st.error(f"'{column_name}' 열이 파일에 없습니다: " + file_name)
                continue

            df['gpt_analysis'], df['reason'] = zip(*df[column_name].apply(get_sentiment_analysis))

            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            new_file_name = f"{os.path.splitext(file_name)[0]}_{timestamp}.csv"

            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button(label=f"결과 다운로드 ({new_file_name})", data=csv, file_name=new_file_name, mime="text/csv")
            
        except Exception as e:
            st.error(f"파일 '{file_name}' 처리 중 오류가 발생했습니다: {e}")

# 텍스트 감정 분석 결과를 저장하기 위한 캐시 딕셔너리
sentiment_analysis_cache = {}
def get_sentiment_analysis(text):
    """
    주어진 텍스트에 대한 감정 분석 결과를 반환
    결과가 캐시에 있으면 캐시된 값을 사용하고, 그렇지 않으면 perform_sentiment_analysis를 호출
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
            temperature=0.5, # 1일 경우, 모델은 훈련 시 가장 자연스럽고 예측 가능한 결과를 생성하는 데 도움
                            # 1보다 큰 값으로 설정되면, 더 다양하고 예측하기 어려운 텍스트를 생성할 수 있게 함
            max_tokens=4096, # gpt-3.5-turbo의 최대 토큰
            top_p=0.1 # top_p=1은 확률 분포의 100%를 고려하겠다는 의미
                )
    
    sentiment_analysis = response.choices[0].message.content
    sentiment_label = 'p' if '긍정' in sentiment_analysis else 'n' if '부정' in sentiment_analysis else 'o'
    reason = sentiment_analysis.split('근거:', 1)[-1].strip() # '근거:' 문자열 이후의 텍스트만 추출
  
    return sentiment_label, reason

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

if __name__ == "__main__":
    main()