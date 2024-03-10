# 프로젝트 계획서
데이터셋 감정분석 카테고리 분류 자동화 및 개선 프로젝트

# 프로젝트명
## (영문) Data Labelling Automation Process with ChatGPT (D-LAP)
## (국문) ChatGPT를 활용한 데이터 라벨링 자동화 프로세스 개발


# 프로젝트 목표
- 자연어처리에 특화된 OpenAI의 Transformer모델을 사용한 프로세스 간소화/자동화

# 프로젝트의 목적
- 기존의 감정분석 방법의 개선
    - 현재는 사람의 주관적인 의견으로 편향되어있고 작업 속도 저하 및 정확도에 대한 이슈가 있음 → 질 좋은 데이터를 보장하지 못함
    - 라벨링에 많은 인력 투입으로 인한 시간소모와 비용 발생
- 뉴스데이터의 감정 데이터를 분석하여 긍정/부정/중립 혹은 그 이상의 카테고리로 분류/검수하는 방법을 자동화 하기 위함
- 시간/비용 소모적인 감정분석 라벨링을 ChatGPT를 활용하여 수행함으로써 업무 효율성 증대를 꾀함

# 프로젝트 개념도
- Google 스프레드 시트의 데이터를 Python과 OpenAI API를 활용해 감정 분석하는 자동화 프로세스를 구현

![감정 분석 프로세스](https://prod-files-secure.s3.us-west-2.amazonaws.com/81a3ccac-627f-46a3-b35f-93293d540f36/944f03d4-ba46-4eae-a040-5611a46d92d5/Untitled.png)

![랭체인을 활용한 데이터셋 감정사전 카테고리 분류 자동화 프로세스(예시)](https://velog.velcdn.com/images/ji1kang/post/18511b9c-7b5f-44de-9ba2-b5572d4df149/image.png)

1. Input Data : 라벨링할 Raw Text
2. Give Instruction : 라벨링 가이드라인을 프롬프트에 작성 
3. Set Classifiers : 라벨링할 카테고리 종류 설정
4. Request API & Adjust Parameters : Temperature, message(user/assistant/system), sentiment etc.
5. Tuning Errors : N명의 사람이 논의 후 승인/결정
