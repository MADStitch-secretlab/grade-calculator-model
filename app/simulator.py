"""
GPA Simulator - Core calculation logic
"""
from typing import List, Dict
from app.models import HistoryItem, TermItem, SimulationResult
import logging

logger = logging.getLogger(__name__)


class GPASimulator:
    """GPA 목표 달성을 위한 학기별 필요 평점 계산"""

    def __init__(self, scale_max: float, G_t: float, C_tot: float,
                 history: List[HistoryItem], terms: List[TermItem]):
        self.scale_max = scale_max
        self.G_t = G_t
        self.C_tot = C_tot
        self.history = history
        self.terms = terms

    def simulate(self) -> List[SimulationResult]:
        """
        메인 시뮬레이션 실행
        Returns:
            각 학기별 필요 평점 리스트
        Raises:
            ValueError: 목표 달성 불가능한 경우
        """
        # Step 1: 현재 상태 계산
        C_e, G_c, C_r, g_need = self._calculate_current_state()

        # Step 2: 남은 학점 합계 보정
        self._adjust_remaining_credits(C_r)

        # Step 3: 초기 균등 분배
        term_plans = self._initial_distribution(g_need)

        # Step 4: 현실성 조정 (water-filling)
        term_plans = self._water_filling_adjustment(term_plans, C_r, g_need)

        # Step 5: 라운딩 및 최종 보정
        results = self._round_and_adjust(term_plans, G_c, C_e)

        return results

    def _calculate_current_state(self):
        """Step 1: 현재 상태 계산"""
        logger.info("\n" + "="*80)
        logger.info("🧮 [CALCULATION] 현재 상태 계산 시작")

        if len(self.history) == 0:
            C_e = 0
            G_c = 0
            logger.info("  ℹ️  이수 완료 학기 없음 (C_e=0, G_c=0)")
        else:
            C_e = sum(h.credits for h in self.history)
            logger.info(f"\n  📊 이수 완료 학점 계산:")
            logger.info(f"    - 총 이수 학점 (C_e): {C_e}")

            logger.info(f"\n  📈 현재 GPA 계산 과정:")
            total_grade_points = 0
            for i, h in enumerate(self.history):
                grade_points = h.credits * h.achieved_avg
                total_grade_points += grade_points
                logger.info(f"    [{i+1}] {h.term_id}: {h.credits}학점 × {h.achieved_avg}평점 = {grade_points:.2f} grade points")

            logger.info(f"\n  📐 총 grade points: {total_grade_points:.2f}")
            G_c = total_grade_points / C_e if C_e > 0 else 0
            logger.info(f"  ⭐ 현재 GPA (G_c): {total_grade_points:.2f} ÷ {C_e} = {G_c:.4f}")

        C_r = self.C_tot - C_e
        logger.info(f"\n  📝 남은 학점 (C_r): {self.C_tot} - {C_e} = {C_r}")

        if C_r <= 0:
            raise ValueError("이미 졸업 요구 학점을 충족했습니다")

        # 목표 GPA 달성을 위해 필요한 평균 평점
        g_need = (self.G_t * self.C_tot - G_c * C_e) / C_r
        logger.info(f"\n  🎯 목표 달성에 필요한 평균 평점 계산:")
        logger.info(f"    g_need = ({self.G_t} × {self.C_tot} - {G_c:.4f} × {C_e}) ÷ {C_r}")
        logger.info(f"    g_need = ({self.G_t * self.C_tot:.2f} - {G_c * C_e:.2f}) ÷ {C_r}")
        logger.info(f"    g_need = {g_need:.4f}")

        if g_need < 0:
            raise ValueError("이미 목표 GPA를 초과 달성했습니다")

        # 기본 검증: 목표 평점이 스케일을 초과하는지 확인
        if g_need > self.scale_max:
            # 달성 가능한 최대 GPA 계산 (모든 남은 학기에 만점을 받았을 때)
            max_possible_gpa = (G_c * C_e + self.scale_max * C_r) / self.C_tot

            # 계절학기 추가로 달성 가능한지 계산
            additional_credits_needed = self._calculate_additional_credits_needed(G_c, C_e, C_r)

            if additional_credits_needed > 0 and additional_credits_needed <= 50:  # 최대 50학점까지만 추가
                raise ValueError(
                    f"현재 상태에서 목표 GPA {self.G_t}를 달성하려면 {additional_credits_needed:.0f}학점의 "
                    f"계절학기(모두 만점 {self.scale_max})가 추가로 필요합니다. "
                    f"현재 졸업 학점({self.C_tot}학점)으로는 최대 {max_possible_gpa:.2f}까지만 달성 가능합니다."
                )
            else:
                raise ValueError(
                    f"목표 GPA {self.G_t} 달성이 불가능합니다. "
                    f"현재 상태(이수 학점: {C_e:.0f}, 현재 평점: {G_c:.2f})에서 "
                    f"남은 {C_r:.0f}학점을 모두 만점({self.scale_max})으로 받아도 "
                    f"최대 {max_possible_gpa:.2f}까지만 달성 가능합니다. "
                    f"목표를 {max_possible_gpa:.2f} 이하로 낮추거나, 현재 성적을 다시 확인해주세요."
                )

        return C_e, G_c, C_r, g_need

    def _calculate_additional_credits_needed(self, G_c: float, C_e: float, C_r: float) -> float:
        """
        목표 GPA 달성을 위해 필요한 추가 계절학기 학점 계산

        목표: (G_c * C_e + scale_max * C_r + scale_max * X) / (C_tot + X) = G_t
        여기서 X는 추가 필요 학점

        풀이:
        G_c * C_e + scale_max * C_r + scale_max * X = G_t * (C_tot + X)
        G_c * C_e + scale_max * C_r + scale_max * X = G_t * C_tot + G_t * X
        scale_max * X - G_t * X = G_t * C_tot - G_c * C_e - scale_max * C_r
        X * (scale_max - G_t) = G_t * C_tot - G_c * C_e - scale_max * C_r
        X = (G_t * C_tot - G_c * C_e - scale_max * C_r) / (scale_max - G_t)
        """
        if self.G_t >= self.scale_max:
            return float('inf')  # 불가능

        numerator = self.G_t * self.C_tot - G_c * C_e - self.scale_max * C_r
        denominator = self.scale_max - self.G_t

        if denominator <= 0:
            return float('inf')

        additional_credits = numerator / denominator

        return max(0, additional_credits)

    def _adjust_remaining_credits(self, C_r: float):
        """Step 2: 남은 학점 합계 보정"""
        total_planned = sum(t.planned_credits for t in self.terms)

        if total_planned < C_r:
            # 부족한 경우: 계절학기 추가
            shortage = C_r - total_planned
            self.terms.append(TermItem(
                id=f"Summer{len(self.terms)+1}",
                type="summer",
                planned_credits=shortage,
                max_credits=min(shortage, 9)  # 계절학기는 일반적으로 9학점까지
            ))
        elif total_planned > C_r:
            # 초과한 경우: 뒤에서부터 감소
            excess = total_planned - C_r
            for i in range(len(self.terms) - 1, -1, -1):
                if excess <= 0:
                    break
                reduction = min(excess, self.terms[i].planned_credits)
                self.terms[i].planned_credits -= reduction
                excess -= reduction

    def _initial_distribution(self, g_need: float) -> List[Dict]:
        """Step 3: 초기 균등 분배"""
        term_plans = []
        for term in self.terms:
            if term.planned_credits > 0:  # 학점이 있는 학기만 포함
                term_plans.append({
                    'term_id': term.id,
                    'credits': term.planned_credits,
                    'required_avg': g_need,
                    'max_credits': term.max_credits
                })
        return term_plans

    def _water_filling_adjustment(self, term_plans: List[Dict], C_r: float, g_need: float) -> List[Dict]:
        """
        Step 4: 현실성 조정 (water-filling 알고리즘)

        일부 학기에서 max_credits나 scale_max를 초과하는 경우,
        해당 학기를 최대치로 고정하고 나머지 학기에 재분배
        """
        max_iterations = 20  # 무한 루프 방지

        for _ in range(max_iterations):
            adjusted = False

            for plan in term_plans:
                # 평점이 스케일 최대치를 초과하는 경우
                if plan['required_avg'] > self.scale_max:
                    plan['required_avg'] = self.scale_max
                    plan['is_capped'] = True
                    adjusted = True

                # 학점이 최대 이수 가능 학점을 초과하는 경우
                # (현재 로직에서는 planned_credits가 이미 max_credits 이하이므로 체크만)
                if plan['credits'] > plan['max_credits']:
                    excess_credits = plan['credits'] - plan['max_credits']
                    plan['credits'] = plan['max_credits']
                    adjusted = True

            if adjusted:
                # 재계산: 고정되지 않은 학기들에 재분배
                fixed_plans = [p for p in term_plans if p.get('is_capped', False)]
                flexible_plans = [p for p in term_plans if not p.get('is_capped', False)]

                if len(flexible_plans) == 0:
                    raise ValueError("목표 GPA를 달성할 수 없습니다 (모든 학기가 최대치에 도달)")

                # 고정된 학기들의 총 grade points 계산
                fixed_grade_points = sum(p['credits'] * p['required_avg'] for p in fixed_plans)
                fixed_credits = sum(p['credits'] for p in fixed_plans)

                # 유연한 학기들에 필요한 평균 재계산
                flexible_credits = sum(p['credits'] for p in flexible_plans)
                needed_grade_points = g_need * C_r - fixed_grade_points
                new_avg = needed_grade_points / flexible_credits

                if new_avg > self.scale_max:
                    # 추가 계절학기 자동 생성
                    additional_credits = 6  # 기본 6학점 추가
                    self.terms.append(TermItem(
                        id=f"Summer_Extra{len(self.terms)+1}",
                        type="summer",
                        planned_credits=additional_credits,
                        max_credits=9
                    ))
                    term_plans.append({
                        'term_id': self.terms[-1].id,
                        'credits': additional_credits,
                        'required_avg': self.scale_max,
                        'max_credits': 9
                    })
                    C_r += additional_credits

                    # 전체 재계산
                    new_avg = (g_need * (C_r - additional_credits) - fixed_grade_points) / (flexible_credits + additional_credits)

                for p in flexible_plans:
                    p['required_avg'] = new_avg
            else:
                break

        return term_plans

    def _round_and_adjust(self, term_plans: List[Dict], G_c: float, C_e: float) -> List[SimulationResult]:
        """Step 5: 라운딩 및 최종 보정"""
        results = []

        # 먼저 소수 둘째 자리로 반올림
        for plan in term_plans:
            results.append(SimulationResult(
                term_id=plan['term_id'],
                credits=round(plan['credits'], 2),
                required_avg=round(plan['required_avg'], 2)
            ))

        # 최종 검증: 실제 달성 GPA 계산
        total_new_credits = sum(r.credits for r in results)
        total_new_grade_points = sum(r.credits * r.required_avg for r in results)

        final_gpa = (G_c * C_e + total_new_grade_points) / (C_e + total_new_credits)

        # 목표 GPA와의 차이를 마지막 학기에 보정 (±0.01 이내)
        diff = self.G_t - final_gpa
        if abs(diff) > 0.001 and len(results) > 0:
            # 마지막 학기의 평점을 조정
            last_result = results[-1]
            adjustment = diff * (C_e + total_new_credits) / last_result.credits
            last_result.required_avg = round(last_result.required_avg + adjustment, 2)

            # 조정 후에도 스케일을 초과하지 않도록 체크
            if last_result.required_avg > self.scale_max:
                last_result.required_avg = self.scale_max

        return results
