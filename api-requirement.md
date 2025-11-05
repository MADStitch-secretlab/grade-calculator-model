# GPA Simulator API - Backend Integration Guide

NestJS 백엔드에서 Python 분석 모델 서버와 통신하기 위한 API 가이드라인

---

## 1. 서비스 정보

| 항목 | 값 |
|------|-----|
| 서비스명 | GPA Simulator |
| 프로토콜 | HTTP/REST |
| Content-Type | application/json |
| 기본 포트 | 8000 |
| Docker 네트워크 | bridge (내부 통신) |
| 평균 응답 시간 | < 300ms |

---

## 2. API 엔드포인트

### 2.1 헬스체크

**GET /**

서비스 정보 조회

```bash
curl http://localhost:8000/
```

**응답 (200 OK)**
```json
{
  "service": "GPA Simulator",
  "status": "running",
  "version": "1.0.0"
}
```

**GET /health**

헬스체크

```bash
curl http://localhost:8000/health
```

**응답 (200 OK)**
```json
{
  "status": "healthy"
}
```

---

### 2.2 GPA 시뮬레이션

**POST /simulate**

목표 GPA 달성을 위한 학기별 필요 평점 계산

```bash
curl -X POST http://localhost:8000/simulate \
  -H "Content-Type: application/json" \
  -d @input.json
```

---

## 3. 요청 스키마

### SimulationInput

| 필드 | 타입 | 필수 | 설명 | 예시 |
|------|------|------|------|------|
| scale_max | number | ✅ | 평점 최대값 | 4.5 |
| G_t | number | ✅ | 목표 GPA | 4.2 |
| C_tot | number | ✅ | 졸업 요구 총 학점 | 130 |
| history | array | ✅ | 이수 완료 학기 목록 | [] |
| terms | array | ✅ | 남은 학기 목록 | [] |

### HistoryItem

| 필드 | 타입 | 필수 | 설명 | 제약 |
|------|------|------|------|------|
| term_id | string | ✅ | 학기 ID | "S1", "S2" 등 |
| credits | number | ✅ | 이수 학점 | > 0 |
| achieved_avg | number | ✅ | 해당 학기 평균 평점 | >= 0 |

### TermItem

| 필드 | 타입 | 필수 | 설명 | 기본값 |
|------|------|------|------|--------|
| id | string | ✅ | 학기 ID | - |
| type | string | ✅ | 학기 유형 | "regular" or "summer" |
| planned_credits | number | ✅ | 계획 학점 | - |
| max_credits | number | ❌ | 최대 이수 가능 학점 | 21 |

---

## 4. 요청 예시

### 4.1 기본 시나리오

```json
{
  "scale_max": 4.5,
  "G_t": 4.2,
  "C_tot": 130,
  "history": [
    {
      "term_id": "S1",
      "credits": 18,
      "achieved_avg": 3.8
    },
    {
      "term_id": "S2",
      "credits": 18,
      "achieved_avg": 3.9
    }
  ],
  "terms": [
    {
      "id": "S3",
      "type": "regular",
      "planned_credits": 18,
      "max_credits": 21
    },
    {
      "id": "S4",
      "type": "regular",
      "planned_credits": 18,
      "max_credits": 21
    },
    {
      "id": "S5",
      "type": "regular",
      "planned_credits": 18,
      "max_credits": 21
    },
    {
      "id": "S6",
      "type": "regular",
      "planned_credits": 18,
      "max_credits": 21
    }
  ]
}
```

### 4.2 신입생 (이수 이력 없음)

```json
{
  "scale_max": 4.5,
  "G_t": 4.0,
  "C_tot": 130,
  "history": [],
  "terms": [
    {"id": "S1", "type": "regular", "planned_credits": 18, "max_credits": 21},
    {"id": "S2", "type": "regular", "planned_credits": 18, "max_credits": 21}
  ]
}
```

### 4.3 계절학기 포함

```json
{
  "scale_max": 4.5,
  "G_t": 4.3,
  "C_tot": 130,
  "history": [
    {"term_id": "S1", "credits": 18, "achieved_avg": 3.5}
  ],
  "terms": [
    {"id": "S2", "type": "regular", "planned_credits": 18, "max_credits": 21},
    {"id": "Summer1", "type": "summer", "planned_credits": 6, "max_credits": 9},
    {"id": "S3", "type": "regular", "planned_credits": 18, "max_credits": 21}
  ]
}
```

---

## 5. 응답 스키마

### 성공 응답 (200 OK)

**SimulationResult 배열**

| 필드 | 타입 | 설명 |
|------|------|------|
| term_id | string | 학기 ID |
| credits | number | 할당된 학점 |
| required_avg | number | 필요한 평균 평점 (소수 둘째 자리) |

**예시**
```json
[
  {
    "term_id": "S3",
    "credits": 18.0,
    "required_avg": 4.33
  },
  {
    "term_id": "S4",
    "credits": 18.0,
    "required_avg": 4.33
  },
  {
    "term_id": "S5",
    "credits": 18.0,
    "required_avg": 4.33
  },
  {
    "term_id": "S6",
    "credits": 18.0,
    "required_avg": 4.33
  }
]
```

### 에러 응답

**ErrorResponse**

| 필드 | 타입 | 설명 |
|------|------|------|
| detail | string | 에러 메시지 |

---

## 6. HTTP 상태 코드

| 코드 | 의미 | 발생 상황 | 처리 방법 |
|------|------|-----------|-----------|
| 200 | OK | 시뮬레이션 성공 | 결과 사용 |
| 400 | Bad Request | 입력 데이터 검증 실패 | 입력값 확인 및 수정 |
| 422 | Unprocessable Entity | 목표 GPA 달성 불가능 | 사용자에게 목표 조정 요청 |
| 500 | Internal Server Error | 서버 내부 오류 | 재시도 또는 관리자 알림 |
| 503 | Service Unavailable | 서버 다운 | 재시도 로직 구현 |

### 6.1 400 Bad Request

**발생 케이스**
- 목표 GPA가 최대 평점을 초과
- 목표 GPA가 0 이하
- 필수 필드 누락
- 데이터 타입 불일치

**응답 예시**
```json
{
  "detail": "목표 GPA (5.0)가 최대 평점 (4.5)을 초과합니다"
}
```

### 6.2 422 Unprocessable Entity

**발생 케이스**
- 목표 GPA 달성을 위해 필요한 평점이 최대 평점 초과
- 남은 학점으로 목표 달성이 수학적으로 불가능
- 이미 졸업 요구 학점 충족

**응답 예시**
```json
{
  "detail": "목표 GPA 4.5를 달성하려면 평균 4.85이 필요하지만, 최대 평점은 4.5입니다"
}
```

### 6.3 500 Internal Server Error

**발생 케이스**
- 예상치 못한 서버 오류
- 계산 로직 버그

**응답 예시**
```json
{
  "detail": "내부 서버 오류: division by zero"
}
```

---

## 7. NestJS 통합 예시

### 7.1 서비스 구현 (gpa.service.ts)

```typescript
import { Injectable, Logger } from '@nestjs/common';
import { HttpService } from '@nestjs/axios';
import { ConfigService } from '@nestjs/config';
import { firstValueFrom } from 'rxjs';

interface SimulationInput {
  scale_max: number;
  G_t: number;
  C_tot: number;
  history: HistoryItem[];
  terms: TermItem[];
}

interface HistoryItem {
  term_id: string;
  credits: number;
  achieved_avg: number;
}

interface TermItem {
  id: string;
  type: 'regular' | 'summer';
  planned_credits: number;
  max_credits?: number;
}

interface SimulationResult {
  term_id: string;
  credits: number;
  required_avg: number;
}

@Injectable()
export class GpaService {
  private readonly logger = new Logger(GpaService.name);
  private readonly simulatorUrl: string;

  constructor(
    private readonly httpService: HttpService,
    private readonly configService: ConfigService,
  ) {
    this.simulatorUrl = this.configService.get<string>(
      'GPA_SIMULATOR_URL',
      'http://localhost:8000',
    );
  }

  async healthCheck(): Promise<boolean> {
    try {
      const response = await firstValueFrom(
        this.httpService.get(`${this.simulatorUrl}/health`),
      );
      return response.data.status === 'healthy';
    } catch (error) {
      this.logger.error('GPA Simulator health check failed', error);
      return false;
    }
  }

  async simulate(input: SimulationInput): Promise<SimulationResult[]> {
    try {
      this.logger.log(`Simulating GPA: target=${input.G_t}, total=${input.C_tot}`);

      const response = await firstValueFrom(
        this.httpService.post<SimulationResult[]>(
          `${this.simulatorUrl}/simulate`,
          input,
          {
            headers: {
              'Content-Type': 'application/json',
            },
          },
        ),
      );

      this.logger.log(`Simulation completed: ${response.data.length} terms`);
      return response.data;

    } catch (error) {
      this.handleSimulationError(error);
    }
  }

  private handleSimulationError(error: any): never {
    if (error.response) {
      const status = error.response.status;
      const detail = error.response.data?.detail || 'Unknown error';

      this.logger.error(`Simulation error [${status}]: ${detail}`);

      switch (status) {
        case 400:
          throw new BadRequestException(detail);
        case 422:
          throw new UnprocessableEntityException(detail);
        case 500:
          throw new InternalServerErrorException('시뮬레이션 중 오류가 발생했습니다');
        default:
          throw new InternalServerErrorException('예상치 못한 오류가 발생했습니다');
      }
    }

    this.logger.error('Network error connecting to GPA Simulator', error);
    throw new ServiceUnavailableException('GPA 시뮬레이터 서버에 연결할 수 없습니다');
  }
}
```

### 7.2 컨트롤러 구현 (gpa.controller.ts)

```typescript
import { Controller, Post, Body, Get } from '@nestjs/common';
import { GpaService } from './gpa.service';

@Controller('api/gpa')
export class GpaController {
  constructor(private readonly gpaService: GpaService) {}

  @Get('health')
  async healthCheck() {
    const isHealthy = await this.gpaService.healthCheck();
    return {
      service: 'GPA Simulator',
      status: isHealthy ? 'healthy' : 'unhealthy',
    };
  }

  @Post('simulate')
  async simulate(@Body() input: SimulationInput) {
    const results = await this.gpaService.simulate(input);
    return {
      success: true,
      data: results,
      message: '시뮬레이션이 완료되었습니다',
    };
  }
}
```

### 7.3 DTO 정의 (simulation-input.dto.ts)

```typescript
import { IsNumber, IsArray, ValidateNested, Min, Max, IsString, IsOptional } from 'class-validator';
import { Type } from 'class-transformer';

export class HistoryItemDto {
  @IsString()
  term_id: string;

  @IsNumber()
  @Min(0.1)
  credits: number;

  @IsNumber()
  @Min(0)
  achieved_avg: number;
}

export class TermItemDto {
  @IsString()
  id: string;

  @IsString()
  type: 'regular' | 'summer';

  @IsNumber()
  @Min(0.1)
  planned_credits: number;

  @IsNumber()
  @Min(0.1)
  @IsOptional()
  max_credits?: number = 21;
}

export class SimulationInputDto {
  @IsNumber()
  @Min(0.1)
  scale_max: number;

  @IsNumber()
  @Min(0.1)
  @Max(5.0)
  G_t: number;

  @IsNumber()
  @Min(1)
  C_tot: number;

  @IsArray()
  @ValidateNested({ each: true })
  @Type(() => HistoryItemDto)
  history: HistoryItemDto[];

  @IsArray()
  @ValidateNested({ each: true })
  @Type(() => TermItemDto)
  terms: TermItemDto[];
}
```

---

## 8. Docker 네트워크 설정

### docker-compose.yml

```yaml
version: '3.8'

services:
  nestjs-backend:
    build: ./backend
    ports:
      - "3000:3000"
    environment:
      - GPA_SIMULATOR_URL=http://gpa-simulator:8000
    depends_on:
      - gpa-simulator
    networks:
      - app-network

  gpa-simulator:
    build: ./analysis-model
    expose:
      - "8000"
    networks:
      - app-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 5s
      retries: 3

networks:
  app-network:
    driver: bridge
```

### 환경변수 설정 (.env)

```bash
# 로컬 개발
GPA_SIMULATOR_URL=http://localhost:8000

# Docker 환경
# GPA_SIMULATOR_URL=http://gpa-simulator:8000
```

---

## 9. 에러 처리 전략

### NestJS에서 에러 처리

```typescript
async simulate(input: SimulationInput) {
  try {
    const results = await this.gpaService.simulate(input);
    return {
      success: true,
      data: results,
    };
  } catch (error) {
    if (error.response?.status === 400) {
      return {
        success: false,
        error: 'INVALID_INPUT',
        message: error.response.data.detail,
      };
    }

    if (error.response?.status === 422) {
      return {
        success: false,
        error: 'TARGET_IMPOSSIBLE',
        message: '목표 GPA를 달성할 수 없습니다. 목표를 낮추거나 계절학기를 추가하세요.',
        detail: error.response.data.detail,
      };
    }

    return {
      success: false,
      error: 'SERVER_ERROR',
      message: '시뮬레이션 중 오류가 발생했습니다.',
    };
  }
}
```

---

## 10. 재시도 로직

### Axios Retry 설정

```typescript
import axiosRetry from 'axios-retry';

constructor(private readonly httpService: HttpService) {
  axiosRetry(this.httpService.axiosRef, {
    retries: 3,
    retryDelay: axiosRetry.exponentialDelay,
    retryCondition: (error) => {
      return axiosRetry.isNetworkOrIdempotentRequestError(error) ||
             error.response?.status >= 500;
    },
  });
}
```

---

## 11. 로깅

### 요청/응답 로깅

```typescript
async simulate(input: SimulationInput): Promise<SimulationResult[]> {
  const startTime = Date.now();

  try {
    this.logger.log({
      message: 'GPA simulation request',
      target_gpa: input.G_t,
      total_credits: input.C_tot,
      history_terms: input.history.length,
      remaining_terms: input.terms.length,
    });

    const response = await firstValueFrom(
      this.httpService.post(`${this.simulatorUrl}/simulate`, input),
    );

    const duration = Date.now() - startTime;
    this.logger.log({
      message: 'GPA simulation success',
      duration_ms: duration,
      results_count: response.data.length,
    });

    return response.data;

  } catch (error) {
    const duration = Date.now() - startTime;
    this.logger.error({
      message: 'GPA simulation failed',
      duration_ms: duration,
      error: error.message,
    });
    throw error;
  }
}
```

---

## 12. 테스트

### 단위 테스트 (gpa.service.spec.ts)

```typescript
describe('GpaService', () => {
  let service: GpaService;
  let httpService: HttpService;

  beforeEach(async () => {
    const module = await Test.createTestingModule({
      providers: [
        GpaService,
        {
          provide: HttpService,
          useValue: {
            post: jest.fn(),
            get: jest.fn(),
          },
        },
        {
          provide: ConfigService,
          useValue: {
            get: jest.fn().mockReturnValue('http://localhost:8000'),
          },
        },
      ],
    }).compile();

    service = module.get<GpaService>(GpaService);
    httpService = module.get<HttpService>(HttpService);
  });

  it('should return simulation results', async () => {
    const input = {
      scale_max: 4.5,
      G_t: 4.2,
      C_tot: 130,
      history: [],
      terms: [
        { id: 'S1', type: 'regular', planned_credits: 18, max_credits: 21 },
      ],
    };

    const mockResponse = [
      { term_id: 'S1', credits: 18, required_avg: 4.2 },
    ];

    jest.spyOn(httpService, 'post').mockReturnValue(
      of({ data: mockResponse } as any),
    );

    const result = await service.simulate(input);

    expect(result).toEqual(mockResponse);
  });
});
```

---

## 13. 성능 최적화

### 커넥션 풀링

```typescript
HttpModule.register({
  timeout: 5000,
  maxRedirects: 0,
  httpAgent: new http.Agent({
    keepAlive: true,
    maxSockets: 50,
  }),
  httpsAgent: new https.Agent({
    keepAlive: true,
    maxSockets: 50,
  }),
})
```

### 캐싱 (선택)

```typescript
async simulate(input: SimulationInput): Promise<SimulationResult[]> {
  const cacheKey = this.generateCacheKey(input);

  const cached = await this.cacheManager.get<SimulationResult[]>(cacheKey);
  if (cached) {
    this.logger.log('Cache hit for simulation');
    return cached;
  }

  const results = await this.callSimulator(input);
  await this.cacheManager.set(cacheKey, results, 300000); // 5분

  return results;
}
```

---

## 14. 보안 고려사항

1. **입력 검증**: NestJS DTO validation으로 모든 입력 검증
2. **Rate Limiting**: 1분에 100번까지 제한
3. **네트워크 격리**: Python 모델은 외부 접근 불가, NestJS만 외부 노출
4. **타임아웃 설정**: 5초 타임아웃으로 무한 대기 방지

---

## 15. 트러블슈팅

### 연결 실패
```
Error: connect ECONNREFUSED 127.0.0.1:8000
```
**해결**: Docker 네트워크 확인, GPA_SIMULATOR_URL 환경변수 확인

### 타임아웃
```
Error: timeout of 5000ms exceeded
```
**해결**: 타임아웃 증가, Python 서버 리소스 확인

### 422 에러 빈번 발생
```
UnprocessableEntityException: Target GPA impossible
```
**해결**: 프론트엔드에서 입력 시 유효성 검사 추가

---

## 16. 참고 문서

- FastAPI: https://fastapi.tiangolo.com/
- Axios: https://axios-http.com/
- NestJS HTTP Module: https://docs.nestjs.com/techniques/http-module
- Docker Networking: https://docs.docker.com/network/

---

**Last Updated**: 2025-11-05
**Version**: 1.0.0
