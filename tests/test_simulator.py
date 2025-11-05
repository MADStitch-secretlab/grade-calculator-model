"""
GPA Simulator 단위 테스트
"""
import pytest
from app.models import HistoryItem, TermItem
from app.simulator import GPASimulator


class TestGPASimulator:
    """GPASimulator 클래스 테스트"""

    def test_basic_simulation(self):
        """기본 시뮬레이션 테스트"""
        # 입력 데이터 (PRD 예시)
        history = [
            HistoryItem(term_id="S1", credits=18, achieved_avg=3.8),
            HistoryItem(term_id="S2", credits=18, achieved_avg=3.9)
        ]
        terms = [
            TermItem(id="S3", type="regular", planned_credits=18, max_credits=21),
            TermItem(id="S4", type="regular", planned_credits=18, max_credits=21),
            TermItem(id="S5", type="regular", planned_credits=18, max_credits=21),
            TermItem(id="S6", type="regular", planned_credits=18, max_credits=21),
            TermItem(id="S7", type="regular", planned_credits=18, max_credits=21),
            TermItem(id="S8", type="regular", planned_credits=18, max_credits=21)
        ]

        simulator = GPASimulator(
            scale_max=4.5,
            G_t=4.2,
            C_tot=130,
            history=history,
            terms=terms
        )

        results = simulator.simulate()

        # 검증
        assert len(results) >= 6  # 최소 6학기
        assert all(r.credits > 0 for r in results)
        assert all(0 <= r.required_avg <= 4.5 for r in results)

        # 총 GPA 계산 검증 (±0.01 오차 허용)
        total_credits = sum(h.credits for h in history) + sum(r.credits for r in results)
        total_grade_points = (
            sum(h.credits * h.achieved_avg for h in history) +
            sum(r.credits * r.required_avg for r in results)
        )
        final_gpa = total_grade_points / total_credits
        assert abs(final_gpa - 4.2) < 0.02  # ±0.02 오차 허용

    def test_no_history(self):
        """이수 이력이 없는 경우"""
        terms = [
            TermItem(id="S1", type="regular", planned_credits=18, max_credits=21),
            TermItem(id="S2", type="regular", planned_credits=18, max_credits=21),
            TermItem(id="S3", type="regular", planned_credits=18, max_credits=21),
            TermItem(id="S4", type="regular", planned_credits=18, max_credits=21)
        ]

        simulator = GPASimulator(
            scale_max=4.5,
            G_t=4.0,
            C_tot=72,
            history=[],
            terms=terms
        )

        results = simulator.simulate()

        # 모든 학기가 동일한 평점이어야 함
        assert len(results) == 4
        assert all(abs(r.required_avg - 4.0) < 0.05 for r in results)

    def test_impossible_target(self):
        """달성 불가능한 목표 GPA"""
        history = [
            HistoryItem(term_id="S1", credits=18, achieved_avg=2.0),
            HistoryItem(term_id="S2", credits=18, achieved_avg=2.0)
        ]
        terms = [
            TermItem(id="S3", type="regular", planned_credits=18, max_credits=21)
        ]

        simulator = GPASimulator(
            scale_max=4.5,
            G_t=4.5,
            C_tot=54,
            history=history,
            terms=terms
        )

        with pytest.raises(ValueError) as exc_info:
            simulator.simulate()

        # 에러 메시지에 달성 가능한 최대 GPA 정보가 포함되어 있는지 확인
        error_message = str(exc_info.value)
        assert "최대" in error_message or "계절학기" in error_message

    def test_already_achieved(self):
        """이미 목표를 달성한 경우"""
        history = [
            HistoryItem(term_id="S1", credits=60, achieved_avg=4.3)
        ]
        terms = [
            TermItem(id="S2", type="regular", planned_credits=10, max_credits=21)
        ]

        simulator = GPASimulator(
            scale_max=4.5,
            G_t=4.2,
            C_tot=70,
            history=history,
            terms=terms
        )

        # 이미 목표를 초과 달성했으므로 에러 또는 매우 낮은 평점 요구
        try:
            results = simulator.simulate()
            # 낮은 평점으로도 충분해야 함
            assert all(r.required_avg < 4.2 for r in results)
        except ValueError:
            # "이미 목표 GPA를 초과 달성" 에러가 발생할 수도 있음
            pass

    def test_scale_limit(self):
        """스케일 제한 검증"""
        history = [
            HistoryItem(term_id="S1", credits=18, achieved_avg=4.0)
        ]
        terms = [
            TermItem(id="S2", type="regular", planned_credits=18, max_credits=21),
            TermItem(id="S3", type="regular", planned_credits=18, max_credits=21)
        ]

        simulator = GPASimulator(
            scale_max=4.5,
            G_t=4.3,
            C_tot=54,
            history=history,
            terms=terms
        )

        results = simulator.simulate()

        # 모든 필요 평점이 스케일 이내여야 함
        assert all(r.required_avg <= 4.5 for r in results)

        # g_need = (4.3 * 54 - 4.0 * 18) / 36 = (232.2 - 72) / 36 = 4.45
        # 4.45는 4.5 이내이므로 가능함

    def test_credit_adjustment(self):
        """학점 부족 시 자동 조정"""
        history = [
            HistoryItem(term_id="S1", credits=18, achieved_avg=3.8)
        ]
        terms = [
            TermItem(id="S2", type="regular", planned_credits=10, max_credits=21)
            # 100 학점이 필요한데 28학점만 있음 -> 자동으로 계절학기 추가
        ]

        simulator = GPASimulator(
            scale_max=4.5,
            G_t=4.0,
            C_tot=100,
            history=history,
            terms=terms
        )

        results = simulator.simulate()

        # 추가 학기가 생성되어야 함
        total_result_credits = sum(r.credits for r in results)
        assert total_result_credits >= 82  # 100 - 18 = 82학점 필요


class TestAPIIntegration:
    """FastAPI 엔드포인트 통합 테스트"""

    @pytest.fixture
    def client(self):
        """테스트 클라이언트 생성"""
        from fastapi.testclient import TestClient
        from app.main import app
        return TestClient(app)

    def test_health_check(self, client):
        """헬스체크 테스트"""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

    def test_simulate_endpoint(self, client):
        """시뮬레이션 엔드포인트 테스트"""
        payload = {
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
        }

        response = client.post("/simulate", json=payload)
        assert response.status_code == 200

        results = response.json()
        assert len(results) >= 6
        assert all("term_id" in r for r in results)
        assert all("credits" in r for r in results)
        assert all("required_avg" in r for r in results)

    def test_invalid_input(self, client):
        """잘못된 입력 테스트"""
        payload = {
            "scale_max": 4.5,
            "G_t": 5.0,  # 스케일 초과
            "C_tot": 130,
            "history": [],
            "terms": [
                {"id": "S1", "type": "regular", "planned_credits": 18, "max_credits": 21}
            ]
        }

        response = client.post("/simulate", json=payload)
        assert response.status_code == 400

    def test_impossible_target_api(self, client):
        """달성 불가능한 목표 API 테스트"""
        payload = {
            "scale_max": 4.5,
            "G_t": 4.5,
            "C_tot": 54,
            "history": [
                {"term_id": "S1", "credits": 18, "achieved_avg": 2.0},
                {"term_id": "S2", "credits": 18, "achieved_avg": 2.0}
            ],
            "terms": [
                {"id": "S3", "type": "regular", "planned_credits": 18, "max_credits": 21}
            ]
        }

        response = client.post("/simulate", json=payload)
        assert response.status_code == 422
