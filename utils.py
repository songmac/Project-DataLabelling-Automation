# pack of modules

def calculate_cost(prompt_length, response_length, model):
    """
    모델별 기본 토큰 비용 설정
    """
    model_costs = {
        "gpt-3.5-turbo": 0.002,  # (instruct모델) output cost
    }
    
    total_tokens = prompt_length + response_length  # 프롬프트와 응답의 토큰 수 합계
    cost_per_1000_tokens = model_costs.get(model, 0)  # 프롬프트 토큰 수 고려해야 할 때 사용
    total_cost = (total_tokens / 1000) * cost_per_1000_tokens  # 총 비용 계산
    
    return total_cost
