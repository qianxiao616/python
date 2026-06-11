"""排课求解器入口脚本

用法示例:
    python schedule_solver.py --data-dir data --instance comp01.ctt
    python schedule_solver.py --data-dir data --all
    python schedule_solver.py --data-dir data --output-dir results
"""
import argparse
import csv
import random
from pathlib import Path
from typing import Dict, List, Optional

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False
from src.ctt_parser import parse_ctt_file
from src.constraint_evaluator import ConstraintEvaluator
from src.greedy_solver import GreedySolver, Lecture, Solution


class RandomSolver(GreedySolver):
    """随机模型：随机打散课程顺序，随机选择可行位置"""

    def solve(self) -> Solution:
        solution = Solution(self.problem)
        lectures_to_schedule = [
            (course_id, i)
            for course_id, course in self.problem.courses.items()
            for i in range(course.lectures)
        ]
        random.shuffle(lectures_to_schedule)

        for course_id, lecture_index in lectures_to_schedule:
            placement = self._find_placement(solution, course_id, lecture_index)
            if placement:
                day, timeslot, room_id = placement
                solution.lectures.append(Lecture(
                    course_id=course_id,
                    lecture_index=lecture_index,
                    day=day,
                    timeslot=timeslot,
                    room_id=room_id
                ))
        return solution

    def _find_placement(self, solution: Solution, course_id: str,
                       lecture_index: int) -> Optional[tuple]:
        course = self.problem.courses[course_id]
        candidates = []
        for day in range(self.problem.days):
            for timeslot in range(self.problem.periods_per_day):
                if (day, timeslot) in course.unavailable_periods:
                    continue
                if self._has_conflict(solution, course_id, day, timeslot):
                    continue
                for room_id, room in self.problem.rooms.items():
                    if solution.get_lecture_in_room(day, timeslot, room_id):
                        continue
                    candidates.append((day, timeslot, room_id))
        if not candidates:
            return None
        return random.choice(candidates)


class CapacitySolver(GreedySolver):
    """容量优先模型：优先选择最接近容量的教室"""

    def _score_placement(self, solution: Solution, course_id: str,
                        day: int, timeslot: int, room_id: str) -> float:
        score = super()._score_placement(solution, course_id, day, timeslot, room_id)
        course = self.problem.courses[course_id]
        room = self.problem.rooms[room_id]
        if room.capacity >= course.students:
            score += 80 - (room.capacity - course.students)
        else:
            score -= (course.students - room.capacity) * 20
        return score


class CompactnessSolver(GreedySolver):
    """紧凑性模型：优先安排同一课程组一天内相邻时段"""

    def _score_placement(self, solution: Solution, course_id: str,
                        day: int, timeslot: int, room_id: str) -> float:
        score = super()._score_placement(solution, course_id, day, timeslot, room_id)
        course = self.problem.courses[course_id]
        for curriculum in self.problem.curricula.values():
            if course_id not in curriculum.courses:
                continue
            for lec in solution.get_lectures_at(day, timeslot - 1):
                if lec.course_id in curriculum.courses:
                    score += 40
            for lec in solution.get_lectures_at(day, timeslot + 1):
                if lec.course_id in curriculum.courses:
                    score += 40
        return score


def format_schedule(solution: Solution) -> List[List[str]]:
    rows = []
    for lecture in sorted(solution.lectures, key=lambda lec: (lec.day, lec.timeslot, lec.room_id)):
        rows.append([
            lecture.course_id,
            str(lecture.lecture_index + 1),
            str(lecture.day + 1),
            str(lecture.timeslot + 1),
            lecture.room_id
        ])
    return rows


def print_solution(instance_name: str, problem, solution: Solution, evaluation: dict) -> None:
    print('\n' + '=' * 80)
    print(f'实例: {instance_name}')
    print('=' * 80)
    print(f'课程数量: {len(problem.courses)}')
    print(f'教室数量: {len(problem.rooms)}')
    print(f'天数: {problem.days}, 每天时段: {problem.periods_per_day}')
    print(f'已安排讲座: {len(solution.lectures)} / 总需求讲座: {sum(c.lectures for c in problem.courses.values())}')
    print(f"是否满足硬约束: {evaluation['is_feasible']}")
    print(f"硬约束违规数: {evaluation['total_violations']}")
    print(f"软约束总成本: {evaluation['total_cost']}")
    print('硬约束明细:')
    for name, value in evaluation['hard_violations'].items():
        print(f'  - {name}: {value}')
    print('软约束明细:')
    for name, value in evaluation['soft_costs'].items():
        print(f'  - {name}: {value}')
    print('\n排课结果:')
    print(f'  课程   讲次   星期   时段   教室')
    for row in format_schedule(solution):
        print(f'  {row[0]:<8} {row[1]:<4} {row[2]:<4} {row[3]:<4} {row[4]}')


def save_solution_csv(output_path: Path, instance_name: str, solution: Solution) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['instance', 'course_id', 'lecture_index', 'day', 'timeslot', 'room_id'])
        for lecture in sorted(solution.lectures, key=lambda lec: (lec.day, lec.timeslot, lec.room_id)):
            writer.writerow([
                instance_name,
                lecture.course_id,
                lecture.lecture_index + 1,
                lecture.day + 1,
                lecture.timeslot + 1,
                lecture.room_id
            ])


def _build_schedule_grid(problem, solution, day: int):
    room_ids = sorted(problem.rooms.keys())
    periods = problem.periods_per_day
    grid = { (room_id, timeslot): '' for room_id in room_ids for timeslot in range(periods) }
    for lecture in solution.lectures:
        if lecture.day != day:
            continue
        grid[(lecture.room_id, lecture.timeslot)] = f'{lecture.course_id}\n({lecture.lecture_index + 1})'
    return room_ids, grid


def plot_schedule(problem, solution: Solution, output_dir: Path, instance_name: str) -> None:
    schedule_dir = output_dir / 'schedules' / instance_name
    schedule_dir.mkdir(parents=True, exist_ok=True)

    course_ids = sorted(problem.courses.keys())
    color_map = plt.get_cmap('tab20')
    course_colors = {cid: color_map(i % color_map.N) for i, cid in enumerate(course_ids)}
    blank_color = '#ffffff'

    for day in range(problem.days):
        room_ids, grid = _build_schedule_grid(problem, solution, day)
        fig = plt.figure(figsize=(problem.periods_per_day * 1.8 + 5.5, max(6, len(room_ids) * 0.35)))
        gs = fig.add_gridspec(2, 2, width_ratios=[3, 1], height_ratios=[0.15, 0.85], hspace=0.12, wspace=0.22)

        title_ax = fig.add_subplot(gs[0, :])
        title_ax.axis('off')
        title_ax.text(0.5, 0.5, f'第 {day + 1} 天', ha='center', va='center', fontsize=16, fontweight='bold')

        table_ax = fig.add_subplot(gs[1, 0])
        table_ax.axis('off')

        cell_text = []
        cell_colors = []
        for room_id in room_ids:
            row_text = []
            row_colors = []
            for timeslot in range(problem.periods_per_day):
                text = grid[(room_id, timeslot)]
                row_text.append(text)
                if text:
                    course_id = text.splitlines()[0]
                    row_colors.append(course_colors.get(course_id, '#cccccc'))
                else:
                    row_colors.append(blank_color)
            cell_text.append(row_text)
            cell_colors.append(row_colors)

        table = table_ax.table(
            cellText=cell_text,
            rowLabels=room_ids,
            colLabels=[f'时段 {i + 1}' for i in range(problem.periods_per_day)],
            cellColours=cell_colors,
            cellLoc='center',
            loc='center'
        )
        table.auto_set_font_size(False)
        table.set_fontsize(8)
        table.scale(1, 2.2)

        legend_ax = fig.add_subplot(gs[1, 1])
        legend_ax.axis('off')
        legend_ax.set_title('课程图例', fontsize=12, pad=10)

        day_course_ids = sorted({lec.course_id for lec in solution.lectures if lec.day == day})
        legend_rows = max(1, min(len(day_course_ids), 18))
        for idx, cid in enumerate(day_course_ids):
            row = idx % legend_rows
            col = idx // legend_rows
            x = 0.06 + col * 0.35
            y = 0.95 - (row + 1) * (0.85 / legend_rows)
            legend_ax.add_patch(mpatches.Rectangle((x, y), 0.03, 0.03, color=course_colors[cid], transform=legend_ax.transAxes, clip_on=False))
            legend_ax.text(x + 0.04, y + 0.015, cid, transform=legend_ax.transAxes, va='center', fontsize=8)

        legend_ax.set_xlim(0, 1)
        legend_ax.set_ylim(0, 1)

        fig.tight_layout(rect=[0, 0, 1, 0.96])
        save_path = schedule_dir / f'day_{day + 1}.png'
        fig.savefig(save_path, dpi=200, bbox_inches='tight')
        plt.close(fig)
        print(f'已保存第 {day + 1} 天排课图: {save_path}')


def solve_instance(ctt_path: Path, output_dir: Path, verbose: bool = False) -> None:
    problem = parse_ctt_file(str(ctt_path))
    solver = GreedySolver(problem, time_limit=30, verbose=verbose)
    solution = solver.solve()
    evaluator = ConstraintEvaluator(problem)
    evaluation = evaluator.evaluate_all(solution)

    instance_name = ctt_path.stem
    print_solution(instance_name, problem, solution, evaluation)

    csv_path = output_dir / 'schedules' / instance_name / f'schedule_{instance_name}.csv'
    save_solution_csv(csv_path, instance_name, solution)
    print(f'已保存排课结果: {csv_path}')

    plot_schedule(problem, solution, output_dir, instance_name)


def compute_satisfaction(evaluation: Dict[str, object], best_cost: float, worst_cost: float) -> float:
    effective_cost = evaluation['total_cost'] + evaluation['total_violations'] * 1000
    if worst_cost <= best_cost:
        return 100.0
    score = 100.0 * (worst_cost - effective_cost) / (worst_cost - best_cost)
    return max(0.0, score)


def plot_comparison(results: List[Dict], output_dir: Path, instance_name: str) -> None:
    comparison_dir = output_dir / 'comparisons' / instance_name
    comparison_dir.mkdir(parents=True, exist_ok=True)

    model_names = [r['name'] for r in results]
    soft_costs = [r['evaluation']['total_cost'] for r in results]
    violations = [r['evaluation']['total_violations'] for r in results]
    satisfaction = [r['satisfaction'] for r in results]

    fig, ax1 = plt.subplots(figsize=(10, 6))
    bars = ax1.bar(model_names, soft_costs, color=['#4472c4', '#ed7d31', '#a5a5a5'], alpha=0.85)
    ax1.set_ylabel('软约束总成本', fontsize=12)
    ax1.set_title(f'模型对比 - {instance_name} 排课满意度及成本', fontsize=14, fontweight='bold')

    for bar, cost in zip(bars, soft_costs):
        ax1.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 2, f'{cost}', ha='center', va='bottom', fontsize=10)

    ax2 = ax1.twinx()
    ax2.plot(model_names, satisfaction, color='#70ad47', marker='o', linewidth=2, label='满意度')
    ax2.set_ylabel('满意度分数', fontsize=12)
    for x, y in zip(model_names, satisfaction):
        ax2.text(x, y + 1.5, f'{y:.1f}', ha='center', va='bottom', fontsize=10, color='#70ad47')

    ax1.grid(alpha=0.3)
    fig.tight_layout()
    save_path = comparison_dir / f'compare_{instance_name}.png'
    plt.savefig(save_path, dpi=200, bbox_inches='tight')
    plt.close()
    print(f'已保存模型对比图: {save_path}')


def compare_models(ctt_path: Path, output_dir: Path, verbose: bool = False) -> None:
    problem = parse_ctt_file(str(ctt_path))
    model_classes = [
        ('Greedy模型', GreedySolver),
        ('随机模型', RandomSolver),
        ('紧凑性模型', CompactnessSolver)
    ]
    results = []
    effective_costs = []

    for name, solver_cls in model_classes:
        solver = solver_cls(problem, time_limit=30, verbose=verbose)
        solution = solver.solve()
        evaluator = ConstraintEvaluator(problem)
        evaluation = evaluator.evaluate_all(solution)
        effective_cost = evaluation['total_cost'] + evaluation['total_violations'] * 1000
        effective_costs.append(effective_cost)
        results.append({
            'name': name,
            'solution': solution,
            'evaluation': evaluation,
            'effective_cost': effective_cost
        })

    best_cost = min(effective_costs)
    worst_cost = max(effective_costs)
    for entry in results:
        entry['satisfaction'] = compute_satisfaction(entry['evaluation'], best_cost, worst_cost)

    for entry in results:
        evaluation = entry['evaluation']
        print('\n' + '=' * 60)
        print(f'模型: {entry["name"]}')
        print('=' * 60)
        print(f"总软成本: {evaluation['total_cost']}")
        print(f"硬约束违规数: {evaluation['total_violations']}")
        print(f"满意度分数: {entry['satisfaction']:.1f}")
        print('软约束明细:')
        for label, value in evaluation['soft_costs'].items():
            print(f'  - {label}: {value}')

    plot_comparison(results, output_dir, ctt_path.stem)
    summary_dir = output_dir / 'comparisons' / ctt_path.stem
    summary_path = summary_dir / f'compare_{ctt_path.stem}.csv'
    summary_dir.mkdir(parents=True, exist_ok=True)
    with open(summary_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['model', 'soft_cost', 'hard_violations', 'satisfaction', 'room_capacity', 'min_working_days', 'curriculum_compactness', 'room_stability'])
        for entry in results:
            ev = entry['evaluation']
            writer.writerow([
                entry['name'],
                ev['total_cost'],
                ev['total_violations'],
                f"{entry['satisfaction']:.1f}",
                ev['soft_costs']['room_capacity'],
                ev['soft_costs']['min_working_days'],
                ev['soft_costs']['curriculum_compactness'],
                ev['soft_costs']['room_stability']
            ])
    print(f'已保存模型对比结果: {summary_path}')

    instance_name = ctt_path.stem
    print('\n' + '=' * 60)
    print(f'生成 {instance_name} 的可视化排课结果（Greedy 模型）')
    print('=' * 60)
    best_solution = results[0]['solution']
    evaluation = results[0]['evaluation']
    print_solution(instance_name, problem, best_solution, evaluation)

    csv_path = output_dir / 'schedules' / instance_name / f'schedule_{instance_name}.csv'
    save_solution_csv(csv_path, instance_name, best_solution)
    print(f'已保存排课结果: {csv_path}')

    plot_schedule(problem, best_solution, output_dir, instance_name)


def main() -> None:
    parser = argparse.ArgumentParser(description='排课任务求解器')
    parser.add_argument('--data-dir', type=str, default='data', help='CTT 文件所在目录')
    parser.add_argument('--instance', type=str, help='要求解的单个 .ctt 文件名称，例如 comp01.ctt')
    parser.add_argument('--all', action='store_true', help='求解目录中所有 .ctt 实例')
    parser.add_argument('--compare', action='store_true', help='对比三个常见模型的排课满意度（默认使用 comp07.ctt）')
    parser.add_argument('--output-dir', type=str, default='results', help='保存排课结果的目录')
    parser.add_argument('--verbose', action='store_true', help='输出详细求解信息')
    args = parser.parse_args()

    data_dir = Path(args.data_dir)
    if not data_dir.exists() or not data_dir.is_dir():
        raise SystemExit(f'错误: 未找到数据目录 {data_dir}')

    output_dir = Path(args.output_dir)
    if args.all:
        ctt_files = sorted(data_dir.glob('*.ctt'))
        if not ctt_files:
            raise SystemExit(f'错误: 在 {data_dir} 没有找到 .ctt 文件')
        for ctt_path in ctt_files:
            solve_instance(ctt_path, output_dir, verbose=args.verbose)
    elif args.compare:
        if not args.instance:
            args.instance = 'comp07.ctt'
        ctt_path = data_dir / args.instance
        if not ctt_path.exists():
            raise SystemExit(f'错误: 未找到实例文件 {ctt_path}')
        compare_models(ctt_path, output_dir, verbose=args.verbose)
    elif args.instance:
        ctt_path = data_dir / args.instance
        if not ctt_path.exists():
            raise SystemExit(f'错误: 未找到实例文件 {ctt_path}')
        solve_instance(ctt_path, output_dir, verbose=args.verbose)
    else:
        raise SystemExit('请指定 --instance、--compare 或 --all')


if __name__ == '__main__':
    main()
