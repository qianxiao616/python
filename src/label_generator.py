"""
标签生成模块 - Label Generator

使用贪心求解器求解每个.ctt实例，计算软成本作为难度标签。
"""
from pathlib import Path
from typing import Dict, List
import time

from src.ctt_parser import parse_ctt_file
from src.greedy_solver import GreedySolver
from src.constraint_evaluator import ConstraintEvaluator


class LabelGenerator:
    """难度标签生成器"""

    def __init__(self, time_limit: int = 30, verbose: bool = False):
        self.time_limit = time_limit
        self.verbose = verbose

    def generate_label(self, ctt_file_path: str) -> Dict[str, any]:
        """为单个实例生成标签"""
        instance_id = Path(ctt_file_path).stem

        try:
            # 解析问题
            problem = parse_ctt_file(ctt_file_path)

            # 使用贪心求解器求解
            solver = GreedySolver(problem, time_limit=self.time_limit, verbose=self.verbose)

            start_time = time.time()
            solution = solver.solve()
            solve_time = time.time() - start_time

            # 评估解决方案
            evaluator = ConstraintEvaluator(problem)
            result = evaluator.evaluate_all(solution)

            # 提取标签和元信息
            label_info = {
                'instance_id': instance_id,
                'difficulty': result['total_cost'],
                'total_violations': result['total_violations'],
                'is_feasible': result['is_feasible'],
                'solve_time': solve_time,

                # 详细的软约束成本
                'room_capacity_cost': result['soft_costs']['room_capacity'],
                'min_working_days_cost': result['soft_costs']['min_working_days'],
                'curriculum_compactness_cost': result['soft_costs']['curriculum_compactness'],
                'room_stability_cost': result['soft_costs']['room_stability'],

                # 详细的硬约束违规
                'lectures_violations': result['hard_violations']['lectures'],
                'room_occupancy_violations': result['hard_violations']['room_occupancy'],
                'conflicts_violations': result['hard_violations']['conflicts'],
                'availabilities_violations': result['hard_violations']['availabilities'],
            }

            return label_info

        except Exception as e:
            print(f"[ERROR] Failed for {instance_id}: {e}")
            import traceback
            traceback.print_exc()
            return None

    def generate_batch(self, ctt_files: List[str]) -> List[Dict[str, any]]:
        """批量生成标签"""
        results = []

        for i, ctt_file in enumerate(ctt_files, 1):
            instance_id = Path(ctt_file).stem
            print(f"\n[{i}/{len(ctt_files)}] Processing: {instance_id}")

            label_info = self.generate_label(ctt_file)

            if label_info:
                results.append(label_info)
                print(f"[OK] {instance_id}: difficulty={label_info['difficulty']}, "
                      f"feasible={label_info['is_feasible']}, "
                      f"violations={label_info['total_violations']}, "
                      f"time={label_info['solve_time']:.2f}s")
            else:
                print(f"[ERROR] {instance_id}: Failed")

        return results

    def print_summary(self, labels: List[Dict[str, any]]):
        """打印标签统计摘要"""
        if not labels:
            print("No label data available")
            return

        print("\n" + "="*60)
        print("Label Generation Summary")
        print("="*60)

        difficulties = [l['difficulty'] for l in labels]
        feasible_count = sum(1 for l in labels if l['is_feasible'])

        print(f"\nTotal instances: {len(labels)}")
        print(f"Feasible solutions: {feasible_count} ({feasible_count/len(labels)*100:.1f}%)")
        print(f"Infeasible solutions: {len(labels) - feasible_count}")

        print(f"\nDifficulty statistics (soft cost):")
        print(f"  Min: {min(difficulties):.0f}")
        print(f"  Max: {max(difficulties):.0f}")
        print(f"  Mean: {sum(difficulties)/len(difficulties):.2f}")
        print(f"  Median: {sorted(difficulties)[len(difficulties)//2]:.0f}")

        solve_times = [l['solve_time'] for l in labels]
        print(f"\nSolve time statistics:")
        print(f"  Min: {min(solve_times):.2f}s")
        print(f"  Max: {max(solve_times):.2f}s")
        print(f"  Mean: {sum(solve_times)/len(solve_times):.2f}s")

        print(f"\nSoft constraint costs (mean):")
        room_cap = sum(l['room_capacity_cost'] for l in labels) / len(labels)
        min_days = sum(l['min_working_days_cost'] for l in labels) / len(labels)
        compact = sum(l['curriculum_compactness_cost'] for l in labels) / len(labels)
        stability = sum(l['room_stability_cost'] for l in labels) / len(labels)

        print(f"  Room capacity: {room_cap:.2f}")
        print(f"  Min working days: {min_days:.2f}")
        print(f"  Curriculum compactness: {compact:.2f}")
        print(f"  Room stability: {stability:.2f}")

        print("="*60)
