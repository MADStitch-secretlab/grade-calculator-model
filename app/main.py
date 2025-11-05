"""
GPA Simulator FastAPI Application
"""
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import logging

from app.models import SimulationInput, SimulationResult, ErrorResponse
from app.simulator import GPASimulator

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# FastAPI 앱 생성
app = FastAPI(
    title="GPA Simulator API",
    description="목표 GPA 달성을 위한 학기별 필요 평점 계산 API",
    version="1.0.0"
)

# CORS 설정 (NestJS 백엔드와의 통신을 위해)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 프로덕션에서는 특정 origin만 허용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """헬스체크 엔드포인트"""
    return {
        "service": "GPA Simulator",
        "status": "running",
        "version": "1.0.0"
    }


@app.get("/health")
async def health_check():
    """헬스체크 엔드포인트"""
    return {"status": "healthy"}


@app.post(
    "/simulate",
    response_model=List[SimulationResult],
    responses={
        200: {
            "description": "시뮬레이션 성공",
            "model": List[SimulationResult]
        },
        400: {
            "description": "입력 데이터 검증 실패",
            "model": ErrorResponse
        },
        422: {
            "description": "목표 GPA 달성 불가능",
            "model": ErrorResponse
        },
        500: {
            "description": "내부 서버 오류",
            "model": ErrorResponse
        }
    }
)
async def simulate_gpa(data: SimulationInput) -> List[SimulationResult]:
    """
    GPA 시뮬레이션 실행

    Args:
        data: 시뮬레이션 입력 데이터
            - scale_max: 평점 최대값 (예: 4.5)
            - G_t: 목표 GPA
            - C_tot: 졸업 요구 총 학점
            - history: 이수 완료 학기 목록
            - terms: 남은 학기 목록

    Returns:
        각 학기별 필요 평점 리스트

    Raises:
        HTTPException: 입력 검증 실패 또는 계산 불가능한 경우
    """
    # 입력 데이터 로깅
    logger.info("="*80)
    logger.info("📥 [REQUEST] 백엔드로 들어온 데이터:")
    logger.info(f"  - 목표 GPA (G_t): {data.G_t}")
    logger.info(f"  - 졸업 총 학점 (C_tot): {data.C_tot}")
    logger.info(f"  - 평점 최대값 (scale_max): {data.scale_max}")
    logger.info(f"  - 완료된 학기 수: {len(data.history)}")
    logger.info(f"  - 남은 학기 수: {len(data.terms)}")

    # History 상세 로깅
    logger.info("\n📚 [HISTORY] 완료된 학기 상세:")
    for i, h in enumerate(data.history):
        logger.info(f"  [{i+1}] {h.term_id}: {h.credits}학점, 평균 {h.achieved_avg}")

    # Terms 상세 로깅
    logger.info("\n📝 [TERMS] 남은 학기 상세:")
    for i, t in enumerate(data.terms):
        logger.info(f"  [{i+1}] {t.id} ({t.type}): 계획 {t.planned_credits}학점, 최대 {t.max_credits}학점")
    logger.info("="*80)

    # 입력 검증
    if data.G_t > data.scale_max:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"목표 GPA ({data.G_t})가 최대 평점 ({data.scale_max})을 초과합니다"
        )

    if data.G_t <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="목표 GPA는 0보다 커야 합니다"
        )

    try:
        # 시뮬레이터 생성 및 실행
        simulator = GPASimulator(
            scale_max=data.scale_max,
            G_t=data.G_t,
            C_tot=data.C_tot,
            history=data.history,
            terms=data.terms
        )

        results = simulator.simulate()

        # 결과 로깅
        logger.info("\n" + "="*80)
        logger.info("✅ [RESULT] 시뮬레이션 완료")
        logger.info(f"  총 {len(results)}개 학기 계획:")
        for i, r in enumerate(results):
            logger.info(f"  [{i+1}] {r.term_id}: {r.credits}학점, 필요 평균 {r.required_avg}점")
        logger.info("="*80 + "\n")

        return results

    except ValueError as e:
        # 목표 달성 불가능한 경우
        logger.warning(f"Simulation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )

    except Exception as e:
        # 예상치 못한 오류
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"내부 서버 오류: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
