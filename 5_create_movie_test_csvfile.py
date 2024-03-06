import pandas as pd

if __name__ == '__main__':

    input_file = './project/original_data/train_data.csv'  # 원본 CSV 파일 경로
    output_file = './project/test_data/movie_test_30.csv'  # 저장할 샘플 CSV 파일 경로

    # CSV 파일 읽기, 컬럼명과 인덱스 변경
    df = pd.read_csv(input_file, delimiter=',')  # 필드가 쉼표로 구분
    df.rename(columns={'document': 'morphs_sentence', 'label': 'polarity_naver'}, inplace=True)
    df['polarity_term'] = df['polarity_term'].map({1: 'p', 0: 'n'})
    
    # n개의 행을 새로운 CSV 파일로 저장
    df_random_sample = df.sample(n=30, random_state=42) # 데이터를 랜덤으로 100개 선택
    df_random_sample.to_csv(output_file, index=False)
    print("파일 저장 완료:", output_file)

    # p,n 라벨링 개수 확인
    print(df_random_sample.groupby('polarity_term').size().reset_index(name = 'count')) 

    """
    # movie_test_100
    polarity_term  count
    0             n     45
    1             p     55

    # movie_test_30
    polarity_term  count
    0             n     11
    1             p     19

    """


