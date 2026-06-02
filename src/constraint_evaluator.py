"""
约束评估器 - 独立实现

评估排课解决方案的硬约束违规和软约束成本
"""
from collections import defaultdict
from typing import Dict
from src.ctt_parser import Problem
from src.greedy_solver import Solution


class ConstraintEvaluator:
    """约束评估器"""

    def __init__(self, problem: Problem):
        self.problem = problem

    def evaluate_all(self, solution: Solution) -> Dict:
        """
        评估所有约束

        Returns:
            包含硬约束违规和软约束成本的字典
        """
        hard = self.evaluate_hard_constraints(solution)
        soft = self.evaluate_soft_constraints(solution)

        total_violations = sum(hard.values())
        total_cost = sum(soft.values())

        return {
            'hard_violations': hard,
            'soft_costs': soft,
            'total_violations': total_violations,
            'total_cost': total_cost,
            'is_feasible': total_violations == 0
        }

    def evaluate_hard_constraints(self, solution: Solution) -> Dict[str, int]:
        """评估硬约束"""
        violations = {
            'lectures': 0,
            'room_occupancy': 0,
            'conflicts': 0,
            'availabilities': 0
        }

        # H1: 所有讲座必须被安排
        for course_id, course in self.problem.courses.items():
            scheduled = solution.get_course_lectures(course_id)
            if len(scheduled) < course.lectures:
                violations['lectures'] += course.lectures - len(scheduled)

        # H2: 教室占用冲突
        room_usage = defaultdict(list)
        for lecture in solution.lectures:
            key = (lecture.day, lecture.timeslot, lecture.room_id)
            room_usage[key].append(lecture)

        for lectures_list in room_usage.values():
            if len(lectures_list) > 1:
                violations['room_occupancy'] += len(lectures_list) - 1

        # H3: 课程冲突（教师和课程组）
        period_courses = defaultdict(list)
        for lecture in solution.lectures:
            period_courses[(lecture.day, lecture.timeslot)].append(lecture.course_id)

        for course_ids in period_courses.values():
            for i in range(len(course_ids)):
                for j in range(i + 1, len(course_ids)):
                    c1, c2 = course_ids[i], course_ids[j]

                    # 检查教师冲突
                    if self.problem.courses[c1].teacher == self.problem.courses[c2].teacher:
                        violations['conflicts'] += 1
                        continue

                    # 检查课程组冲突
                    for curriculum in self.problem.curricula.values():
                        if c1 in curriculum.courses and c2 in curriculum.courses:
                            violations['conflicts'] += 1
                            break

        # H4: 不可用时段
        for lecture in solution.lectures:
            course = self.problem.courses[lecture.course_id]
            if (lecture.day, lecture.timeslot) in course.unavailable_periods:
                violations['availabilities'] += 1

        return violations

    def evaluate_soft_constraints(self, solution: Solution) -> Dict[str, int]:
        """评估软约束"""
        costs = {
            'room_capacity': 0,
            'min_working_days': 0,
            'curriculum_compactness': 0,
            'room_stability': 0
        }

        # S1: 教室容量超载（1分/人）
        for lecture in solution.lectures:
            course = self.problem.courses[lecture.course_id]
            room = self.problem.rooms[lecture.room_id]
            if course.students > room.capacity:
                costs['room_capacity'] += course.students - room.capacity

        # S2: 最少工作天数不足（5分/天）
        for course_id, course in self.problem.courses.items():
            lectures = solution.get_course_lectures(course_id)
            days_used = set(lec.day for lec in lectures)
            if len(days_used) < course.min_working_days:
                costs['min_working_days'] += 5 * (course.min_working_days - len(days_used))

        # S3: 课程组紧凑性（2分/孤立讲座）
        for curriculum in self.problem.curricula.values():
            for day in range(self.problem.days):
                # 获取该课程组在该天的所有讲座
                day_lectures = []
                for course_id in curriculum.courses:
                    lectures = solution.get_course_lectures(course_id)
                    day_lectures.extend([lec for lec in lectures if lec.day == day])

                if not day_lectures:
                    continue

                # 检查每个讲座是否孤立
                timeslots = sorted(set(lec.timeslot for lec in day_lectures))
                for timeslot in timeslots:
                    # 检查相邻时段是否有讲座
                    if (timeslot - 1) not in timeslots and (timeslot + 1) not in timeslots:
                        costs['curriculum_compactness'] += 2

        # S4: 教室稳定性（1分/额外教室）
        for course_id in self.problem.courses.keys():
            lectures = solution.get_course_lectures(course_id)
            rooms_used = set(lec.room_id for lec in lectures)
            if len(rooms_used) > 1:
                costs['room_stability'] += len(rooms_used) - 1

        return costs


if __name__ == '__main__':
    from pathlib import Path
    from src.ctt_parser import parse_ctt_file
    from src.greedy_solver import GreedySolver

    test_file = Path(__file__).parent.parent.parent / 'pycourse' / 'data' / 'comp01.ctt'
    if test_file.exists():
        print("Testing constraint evaluator...")
        problem = parse_ctt_file(str(test_file))
        solver = GreedySolver(problem)
        solution = solver.solve()

        evaluator = ConstraintEvaluator(problem)
        result = evaluator.evaluate_all(solution)

        print(f"Total violations: {result['total_violations']}")
        print(f"Total cost: {result['total_cost']}")
        print(f"Is feasible: {result['is_feasible']}")
