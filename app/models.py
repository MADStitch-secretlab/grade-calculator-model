"""
Pydantic models for GPA Simulator API
"""
from typing import List
from pydantic import BaseModel, Field


class HistoryItem(BaseModel):
    """이수 완료한 학기 정보"""
    term_id: str = Field(..., description="학기 ID (e.g., S1, S2)")
    credits: float = Field(..., gt=0, description="이수 학점")
    achieved_avg: float = Field(..., ge=0, description="해당 학기 평균 평점")


class TermItem(BaseModel):
    """남은 학기 정보"""
    id: str = Field(..., description="학기 ID")
    type: str = Field(..., description="학기 유형 (regular, summer)")
    planned_credits: float = Field(..., gt=0, description="계획 학점")
    max_credits: float = Field(default=21, gt=0, description="최대 이수 가능 학점")


class SimulationInput(BaseModel):
    """시뮬레이션 입력 데이터"""
    scale_max: float = Field(..., gt=0, description="평점 최대값 (예: 4.5)")
    G_t: float = Field(..., gt=0, description="목표 GPA")
    C_tot: float = Field(..., gt=0, description="졸업 요구 총 학점")
    history: List[HistoryItem] = Field(..., min_length=0, description="이수 완료 학기 목록")
    terms: List[TermItem] = Field(..., min_length=1, description="남은 학기 목록")


class SimulationResult(BaseModel):
    """각 학기별 필요 평점 결과"""
    term_id: str = Field(..., description="학기 ID")
    credits: float = Field(..., description="할당된 학점")
    required_avg: float = Field(..., description="필요한 평균 평점")


class ErrorResponse(BaseModel):
    """에러 응답"""
    detail: str = Field(..., description="에러 메시지")
