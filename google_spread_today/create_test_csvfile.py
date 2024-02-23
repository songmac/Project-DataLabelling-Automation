import pandas as pd
import csv  # csv 모듈: CSV (Comma-Separated Values) 파일을 읽고 쓰는 기능을 제공

# r'파일명' or / or \\ 를 사용하여 이스케이프 시퀀스 피하기
# 원본 CSV 파일 경로 
input_file = 'C:/Users/selena/songmac/Project-DataLabelling-Automation/ignore/data/neu_test_5000.csv'# 저장할 새 CSV 파일 경로
output_file = 'C:/Users/selena/songmac/Project-DataLabelling-Automation/ignore/data/neu_test_10.csv'

try:
    # CSV 파일 읽기
    df = pd.read_csv(input_file, delimiter='tab', quoting=csv.QUOTE_NONE, escapechar='\\')
    """
    csv 모듈의 QUOTE_NONE 상수를 올바르게 참조하여, 파이썬의 CSV 파서가 CSV 파일을 읽을 때 발생할 수 있는 따옴표 관련 문제를 해결     
    escapechar='\\'를 설정함으로써 이스케이프 문자를 지정하여 파일 내에서 특수 문자를 올바르게 처리
    """
    # 앞에서 3개의 행만 선택
    df_reduced = df.head(10)

    # 선택된 행을 새로운 CSV 파일로 저장
    df_reduced.to_csv(output_file, index=False)  

    print("파일 저장 완료:", output_file)

except Exception as e:
    print("파일 처리 중 오류 발생:", e)