## 1. 서비스 개요
**서비스명:** GPA Path  
**목표:**  
사용자가 PDF 성적표를 업로드하면 OCR과 분석 모델을 통해 **목표 GPA 달성을 위해 각 남은 학기별로 받아야 하는 평균 학점**을 계산·시각화하는 웹 서비스.

---

## 2. 전체 아키텍처
```mermaid
flowchart LR
  U[User] --> FE[Frontend (Next.js)]
  FE --> BE[NestJS Backend]
  BE --> OCR[OCR 모듈 (PaddleOCR or Cloud Vision)]
  OCR --> PARSER[GPT 파서]
  PARSER --> DB[(Supabase DB)]
  DB --> PY[Python Model Server (FastAPI)]
  BE --> PY
  PY --> BE
  BE --> FE
```

- **Frontend:** Next.js + Tailwind → 업로드, 목표 입력, 시각화  
- **Backend:** NestJS → API 게이트웨이, OCR·파싱 호출, 모델 통신  
- **Model Server:** Python(FastAPI) → 데이터 분석 모델 구동  
- **DB:** Supabase(Postgres) → 사용자/성적/계획 데이터 관리  
- **Storage:** Supabase Storage 또는 AWS S3 (PDF 보관)

---

## 3. 주요 사용자 플로우
1. **성적표 업로드**
   - 사용자 PDF 업로드 → OCR → GPT 파서로 성적 데이터(JSON) 생성  
   - DB 저장 (`transcript` 테이블)
2. **목표 설정**
   - 사용자 입력: `G_t`, `C_tot`, `scale_max`, `max_credits` 등  
3. **예측 실행**
   - NestJS → Python Model API(`/simulate`) 호출  
   - 모델이 남은 학기별 `required_avg` 계산 후 JSON 반환  
4. **결과 표시**
   - 학기별 카드 UI (예: “S5: 4.18 / S6: 4.20 / S7: 4.21”)  
   - 불가능 시 자동 계절학기 추가 결과 표시  
5. **리포트 다운로드**
   - 계산 결과 PDF로 저장 (향후 확장)

---

## 4. 주요 API 명세 (NestJS ↔ Python 포함)
| 구분 | 메서드 | 경로 | 설명 |
|------|--------|------|------|
| FE → BE | POST | `/api/transcripts/upload` | 성적표 업로드 및 파싱 |
| FE → BE | POST | `/api/targets` | 목표 GPA, 총학점, 스케일 입력 |
| FE → BE | POST | `/api/simulate-target` | 모델 실행 요청 |
| BE → PY | POST | `/simulate` | Python 모델 서버 호출 |
| PY → BE | JSON Response | `{term_id, credits, required_avg}` |

---

## 5. 데이터베이스 스키마 요약
| 테이블 | 주요 필드 | 설명 |
|---------|------------|------|
| users | id, email | 사용자 정보 |
| transcripts | id, user_id, gpa, credits | OCR 결과 |
| targets | id, user_id, G_t, C_tot, scale_max | 목표 설정 |
| plans | id, user_id, json_result | 모델 출력 저장 |

---

## 6. 예시 입출력

**요청 (NestJS → Python)**
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

**응답 (Python → NestJS)**
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

## 7. 통신 방식
- HTTP/REST (JSON)
- `Content-Type: application/json`
- Timeout 5s
- Status code
  - 200: 성공
  - 400: 입력 검증 실패
  - 422: 모델 계산 불가 (목표 불가능)
  - 500: 내부 오류

---

## 8. 보안/운영
- 사용자 파일 24시간 내 자동 삭제
- NestJS ↔ Python 간 내부 네트워크 통신만 허용 (Docker bridge)
- KMS 암호화(환경변수: OPENAI_KEY, DB_KEY)

---

## 9. 향후 확장
- “성적 향상 시뮬레이터” 추가 (가상 과목별 점수 조정)
- “AI 과목 추천” 기능 (고득점 확률 기반)
- 멀티캠퍼스 포맷 자동 인식 (학교별 OCR 규칙)