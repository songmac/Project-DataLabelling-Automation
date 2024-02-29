# pack of modules

import time 
def safe_api_call(api_method, *args, **kwargs):
    """API 호출 실패 시 최대 3회까지 재시도하는 함수"""
    max_attempts = 3
    for attempt in range(1, max_attempts + 1):
        try:
            return api_method(*args, **kwargs)
        except Exception as e:
            print(f"API 호출 중 오류 발생 (시도 {attempt}/{max_attempts}): {e}")
            if attempt == max_attempts:
                raise
            time.sleep(2**attempt)  # 지수 백오프로 대기 시간 증가



def column_index_to_letter(column_index):
    """
    함수 설명 : Column 인덱스를 문자로 변환하는 모듈
    동작 방식 : 열 번호(1부터 시작)를 엑셀의 열 문자로 변환. 예: 1 -> 'A', 27 -> 'AA'
    """
    letter = ''
    while column_index > 0:
        column_index, remainder = divmod(column_index - 1, 26)
        letter = chr(65 + remainder) + letter
    return letter


def calculate_cost(prompt_length, response_length, model):
    """
    함수 설먕 : 토큰 비용 계산 모듈
    툭이 사항 : 모델별 기본 토큰 비용 설정하여 계산
    """
    model_costs = {
        "gpt-3.5-turbo": 0.002,  # (instruct모델) output cost
    }
    
    total_tokens = prompt_length + response_length  # 프롬프트와 응답의 토큰 수 합계
    cost_per_1000_tokens = model_costs.get(model, 0)  # 프롬프트 토큰 수 고려해야 할 때 사용
    total_cost = (total_tokens / 1000) * cost_per_1000_tokens  # 총 비용 계산
    
    return total_cost
