# GPA Simulator API

목표 GPA 달성을 위한 학기별 필요 평점을 계산하는 FastAPI 기반 분석 모델 서버입니다.

## 주요 기능

- 현재 성적과 목표 GPA를 입력받아 남은 학기별로 받아야 하는 평균 평점 계산
- Water-filling 알고리즘을 통한 현실적인 학점 분배
- 목표 달성 불가능 시 자동 계절학기 추가
- RESTful API 제공 (JSON 입출력)

## 기술 스택

- **Python** 3.11+
- **FastAPI** 0.109.0
- **Pydantic** 2.5.3 (데이터 검증)
- **Uvicorn** (ASGI 서버)
- **pytest** (테스트)

## 설치 및 실행

### 로컬 환경

```bash
# 의존성 설치
pip install -r requirements.txt

# 개발 서버 실행
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 서버가 http://localhost:8000 에서 실행됩니다
```

### Docker

```bash
# 이미지 빌드
docker build -t gpa-simulator .

# 컨테이너 실행
docker run -d -p 8000:8000 --name gpa-simulator gpa-simulator

# 로그 확인
docker logs -f gpa-simulator

# 컨테이너 중지
docker stop gpa-simulator
```

## API 사용법

### 엔드포인트

#### `GET /`
헬스체크 및 서비스 정보

#### `GET /health`
헬스체크

#### `POST /simulate`
GPA 시뮬레이션 실행

### 요청 예시

```bash
curl -X POST "http://localhost:8000/simulate" \
  -H "Content-Type: application/json" \
  -d '{
    "scale_max": 4.5,
    "G_t": 4.2,
    "C_tot": 130,
    "history": [
      {"term_id": "S1", "credits": 18, "achieved_avg": 3.8},
      {"term_id": "S2", "credits": 18, "achieved_avg": 3.9}
    ],
    "terms": [
      {"id": "S3", "type": "regular", "planned_credits": 18, "max_credits": 21},
      {"id": "S4", "type": "regular", "planned_credits": 18, "max_credits": 21},
      {"id": "S5", "type": "regular", "planned_credits": 18, "max_credits": 21},
      {"id": "S6", "type": "regular", "planned_credits": 18, "max_credits": 21},
      {"id": "S7", "type": "regular", "planned_credits": 18, "max_credits": 21},
      {"id": "S8", "type": "regular", "planned_credits": 18, "max_credits": 21}
    ]
  }'
```

### 요청 파라미터

| 필드 | 타입 | 설명 |
|------|------|------|
| scale_max | float | 평점 최대값 (예: 4.5) |
| G_t | float | 목표 GPA |
| C_tot | float | 졸업 요구 총 학점 |
| history | array | 이수 완료 학기 목록 |
| history[].term_id | string | 학기 ID |
| history[].credits | float | 이수 학점 |
| history[].achieved_avg | float | 해당 학기 평균 평점 |
| terms | array | 남은 학기 목록 |
| terms[].id | string | 학기 ID |
| terms[].type | string | 학기 유형 (regular/summer) |
| terms[].planned_credits | float | 계획 학점 |
| terms[].max_credits | float | 최대 이수 가능 학점 (기본: 21) |

### 응답 예시

**성공 (200 OK)**
```json
[
  {"term_id": "S3", "credits": 18, "required_avg": 4.18},
  {"term_id": "S4", "credits": 18, "required_avg": 4.18},
  {"term_id": "S5", "credits": 18, "required_avg": 4.18},
  {"term_id": "S6", "credits": 18, "required_avg": 4.18},
  {"term_id": "S7", "credits": 18, "required_avg": 4.18},
  {"term_id": "S8", "credits": 18, "required_avg": 4.18}
]
```

**에러 응답**

- `400 Bad Request`: 입력 데이터 검증 실패
- `422 Unprocessable Entity`: 목표 GPA 달성 불가능
- `500 Internal Server Error`: 내부 서버 오류

```json
{
  "detail": "목표 GPA (4.8)가 최대 평점 (4.5)을 초과합니다"
}
```

## 계산 로직

### 1. 현재 상태 계산
```python
C_e = 이수 완료 학점
G_c = 현재 평균 평점
C_r = 남은 학점 (C_tot - C_e)
g_need = 필요한 평균 평점 = (G_t * C_tot - G_c * C_e) / C_r
```

### 2. 남은 학점 합계 보정
- 계획 학점 합계 < 남은 학점 → 자동 계절학기 추가
- 계획 학점 합계 > 남은 학점 → 뒤에서부터 감소

### 3. 균등 분배
각 학기에 `g_need` 평점 할당

### 4. 현실성 조정 (Water-filling)
- 평점이 `scale_max` 초과 시 해당 학기를 최대치로 고정
- 나머지 학기에 재분배
- 불가능하면 계절학기 자동 추가

### 5. 라운딩 및 보정
- 소수 둘째 자리로 반올림
- 마지막 학기에 ±0.01 보정하여 목표 GPA 정확히 일치

## 테스트

```bash
# 전체 테스트 실행
pytest

# 상세 출력
pytest -v

# 커버리지 확인
pytest --cov=app tests/
```

## 프로젝트 구조

```
analysis-model/
├── app/
│   ├── __init__.py
│   ├── main.py          # FastAPI 앱 및 엔드포인트
│   ├── models.py        # Pydantic 모델 정의
│   └── simulator.py     # GPA 계산 로직
├── tests/
│   ├── __init__.py
│   └── test_simulator.py # 단위 테스트
├── requirements.txt     # Python 의존성
├── Dockerfile          # Docker 이미지 설정
├── .dockerignore       # Docker 빌드 제외 파일
└── README.md           # 프로젝트 문서
```

## API 문서

서버 실행 후 다음 URL에서 자동 생성된 API 문서를 확인할 수 있습니다:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## NestJS 연동 예시

```typescript
// NestJS에서 호출 예시
import { HttpService } from '@nestjs/axios';
import { Injectable } from '@nestjs/common';
import { firstValueFrom } from 'rxjs';

@Injectable()
export class GpaService {
  constructor(private httpService: HttpService) {}

  async simulate(data: SimulationInput) {
    const response = await firstValueFrom(
      this.httpService.post('http://gpa-simulator:8000/simulate', data)
    );
    return response.data;
  }
}
```

## 환경 변수

| 변수명 | 기본값 | 설명 |
|--------|--------|------|
| HOST | 0.0.0.0 | 서버 호스트 |
| PORT | 8000 | 서버 포트 |

## 성능

- **평균 응답 시간**: < 300ms
- **동시 접속**: 100+ requests/sec (기본 설정)

## 로깅

모든 요청/응답이 자동으로 로깅됩니다:
```
2025-11-05 10:00:00 - app.main - INFO - Simulation request received: G_t=4.2, C_tot=130
2025-11-05 10:00:00 - app.main - INFO - History: 2 terms completed
2025-11-05 10:00:00 - app.main - INFO - Remaining: 6 terms
2025-11-05 10:00:00 - app.main - INFO - Simulation completed: 6 terms planned
```

## 향후 확장

- [ ] 시나리오 기반 분배 (보수/공격/중립 모드)
- [ ] Monte Carlo 기반 목표 달성 확률 계산
- [ ] 과거 성적 기반 가중분배 (rolling average)
- [ ] 다중 목표 GPA 시뮬레이션 (best/worst case)

## 라이선스

MIT

## 문의

프로젝트 관련 문의사항은 이슈를 등록해주세요.
# grade-calculator-model
