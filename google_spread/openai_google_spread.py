from read_spreadsheet import read_spreadsheet
from analyze_sentiment import analyze_sentiment
from save_results import save_results

spreadsheet_url = '여기에 스프레드 시트 URL 입력'
data = read_spreadsheet(spreadsheet_url)  # 스프레드시트에서 데이터 읽기
sentiment_analysis_results = analyze_sentiment(data)  # 데이터에 대한 감정 분석 수행
save_results(spreadsheet_url, sentiment_analysis_results)  # 분석 결과를 스프레드시트에 저장
print("분석이 완료되었습니다. 스프레드 시트를 확인해주세요.")
