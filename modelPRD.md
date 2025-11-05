## 1. 개요
**모델명:** GPA Simulator  
**목표:**  
NestJS 백엔드로부터 현재 성적과 목표 GPA를 받아, **남은 학기별로 받아야 하는 평균 평점(required_avg)** 을 계산하여 JSON으로 반환한다.

---

## 2. 환경
- **언어:** Python 3.11+
- **Framework:** FastAPI
- **배포:** Docker container
- **호출:** POST `/simulate`
- **연동:** NestJS 서버가 내부 HTTP 요청으로 호출

---

## 3. 입력(JSON)
```json
{
  "scale_max": 4.5,
  "G_t": 4.2,
  "C_tot": 130,
  "history": [
    {"term_id": "S1", "credits": 18, "achieved_avg": 3.8},
    {"term_id": "S2", "credits": 18, "achieved_avg": 3.9}
  ],
  "terms": [
    {"id":"S3","type":"regular","planned_credits":18,"max_credits":21},
    {"id":"S4","type":"regular","planned_credits":18,"max_credits":21},
    {"id":"S5","type":"regular","planned_credits":18,"max_credits":21},
    {"id":"S6","type":"regular","planned_credits":18,"max_credits":21},
    {"id":"S7","type":"regular","planned_credits":18,"max_credits":21},
    {"id":"S8","type":"regular","planned_credits":18,"max_credits":21}
  ]
}
```

---

## 4. 출력(JSON)
```json
[
  {"term_id":"S3","credits":18,"required_avg":4.18},
  {"term_id":"S4","credits":18,"required_avg":4.18},
  {"term_id":"S5","credits":18,"required_avg":4.18},
  {"term_id":"S6","credits":18,"required_avg":4.18},
  {"term_id":"S7","credits":18,"required_avg":4.18},
  {"term_id":"S8","credits":18,"required_avg":4.18}
]
```

---

## 5. 계산 로직

### Step 1. 현재 상태 계산
```python
C_e = sum(h["credits"] for h in history)
G_c = sum(h["credits"] * h["achieved_avg"] for h in history) / C_e
C_r = C_tot - C_e
g_need = (G_t * C_tot - G_c * C_e) / C_r
```

### Step 2. 남은 학점 합계 보정
- `sum(term["planned_credits"]) < C_r` → 자동 계절학기 추가
- `> C_r` → 뒤에서부터 planned_credits 감소

### Step 3. 균등분배
```python
for t in terms:
    t["required_avg"] = g_need
```

### Step 4. 현실성 조정 (water-filling)
```python
caps = [t.get("max_credits", 21) for t in terms]
scale = scale_max
# 만약 g_need > scale, 자동 계절학기 추가 및 재계산
# 불가능하면 raise HTTP 422
```

### Step 5. 라운딩
소수 둘째 자리로 반올림  
마지막 학기에 ±0.01 보정하여 목표 GPA 정확히 일치

---

## 6. FastAPI 엔드포인트 설계
```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List

app = FastAPI()

class HistoryItem(BaseModel):
    term_id: str
    credits: float
    achieved_avg: float

class TermItem(BaseModel):
    id: str
    type: str
    planned_credits: float
    max_credits: float = 21

class InputData(BaseModel):
    scale_max: float
    G_t: float
    C_tot: float
    history: List[HistoryItem]
    terms: List[TermItem]

@app.post("/simulate")
def simulate(data: InputData):
    # 로직: g_need, 분배, 보정
    # 결과 생성
    return results  # [{term_id, credits, required_avg}]
```

---

## 7. 오류 처리
| 상황 | 코드 | 메시지 |
|------|------|---------|
| 목표 GPA 불가능 | 422 | "Target GPA exceeds scale limit" |
| 입력 불충분 | 400 | "Missing required fields" |
| 내부 계산 오류 | 500 | "Internal calculation error" |

---

## 8. 통신
- **Request:** JSON (UTF-8)
- **Response:** JSON Array
- **Latency 목표:** < 300ms (평균)
- **보안:** 내부 네트워크 전용 (Docker bridge)

---

## 9. 로깅 및 검증
- 입력·출력 JSON 모두 로깅
- 단위 테스트: pytest 기반  
  - 입력 검증, 총 GPA 일치율(±0.01), 상한 캡 검증 포함
- Postman test case 제공 (NestJS 연동 확인용)

---

## 10. 향후 확장
- 시나리오 기반 분배(보수/공격/중립)
- Monte Carlo 기반 목표 달성 확률 계산
- 과거 성적 기반 가중분배 (rolling avg 적용)@ 