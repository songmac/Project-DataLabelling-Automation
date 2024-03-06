import pickle
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import urllib.request
from tqdm import tqdm

# 데이터 다운로드
urllib.request.urlretrieve("https://raw.githubusercontent.com/e9t/nsmc/master/ratings_train.txt", filename="ratings_train.txt")
urllib.request.urlretrieve("https://raw.githubusercontent.com/e9t/nsmc/master/ratings_test.txt", filename="ratings_test.txt")
train_data = pd.read_table('ratings_train.txt')
test_data = pd.read_table('ratings_test.txt')


# train/test data 개수 확인
print('훈련용 리뷰 개수 :',len(train_data)) # 훈련용 리뷰 개수 출력
# print('테스트용 리뷰 개수 :',len(test_data)) # 테스트용 리뷰 개수 출력


# train data 정제
print(train_data['document'].nunique(), train_data['label'].nunique()) # document 열과 label 열의 중복을 제외한 값의 개수
train_data.drop_duplicates(subset=['document'], inplace=True) # document 열의 중복 제거
train_data = train_data.dropna(how = 'any') # Null 값이 존재하는 행 제거

print('총 샘플의 수 :',len(train_data)) # 중복, Null 값 제거 확인


# train data 전처리 (생략)
"""
전처리를 생략한 이유 : 
    1. 문맥 포착: Transformer 모델은 문장 전체의 문맥을 이해하는 데 탁월하므로,
        특히 한국어와 같이 문맥에 따라 의미가 크게 변할 수 있는 언어에서는 
        원본 텍스트의 형태를 유지하는 것이 중요한 의미를 가질 수 있음
    2. 어조와 뉘앙스: 어조나 띄어쓰기 같은 언어적 뉘앙스가 의미를 결정하는 데 중요한 역할을 함

그럼에도 불구하고, 
노이즈와 같은 완전히 관련 없는 정보(예: 과도한 특수 문자, 스팸 메시지의 특징 등)는
 모델의 성능에 부정적인 영향을 미칠 수 있으므로 제거할 필요가 있음
"""

# train data csv로 저장
train_data.to_csv('./project/original_data/movie_train_data.csv', index=False)

print(train_data.head()) 
print('데이터의 전체 샘플 수:', len(train_data)) # train data의 총 샘플 수를 확인



