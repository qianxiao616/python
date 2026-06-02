"""
贪心求解器 - 独立实现

简化的贪心求解器，用于生成排课解决方案和难度标签
"""
import random
from typing import List, Tuple, Optional
from dataclasses import dataclass, field
from src.ctt_parser import Problem, Course


@dataclass
class Lecture:
    """讲座分配"""
    course_id: str
    lecture_index: int
    day: int
    timeslot: int
    room_id: str


@dataclass
class Solution:
    """排课解决方案"""
    problem: Problem
    lectures: List[Lecture] = field(default_factory=list)

    def get_lectures_at(self, day: int, timeslot: int) -> List[Lecture]:
        """获取某个时段的所有讲座"""
        return [lec for lec in self.lectures
                if lec.day == day and lec.timeslot == timeslot]

    def get_lecture_in_room(self, day: int, timeslot: int, room_id: str) -> Optional[Lecture]:
        """获取某个教室在某时段的讲座"""
        for lec in self.lectures:
            if lec.day == day and lec.timeslot == timeslot and lec.room_id == room_id:
                return lec
        return None

    def get_course_lectures(self, course_id: str) -> List[Lecture]:
        """获取某门课程的所有讲座"""
        return [lec for lec in self.lectures if lec.course_id == course_id]


class GreedySolver:
    """贪心求解器"""

    def __init__(self, problem: Problem, time_limit: int = 30, verbose: bool = False):
        self.problem = problem
        self.time_limit = time_limit
        self.verbose = verbose

    def solve(self) -> Solution:
        """
        使用贪心策略求解

        Returns:
            Solution对象
        """
        solution = Solution(self.problem)

        # 创建待排课的讲座列表
        lectures_to_schedule = []
        for course_id, course in self.problem.courses.items():
            for i in range(course.lectures):
                lectures_to_schedule.append((course_id, i))

        # 按约束复杂度排序（更难的课程优先排）
        lectures_to_schedule.sort(
            key=lambda x: len(self.problem.courses[x[0]].unavailable_periods),
            reverse=True
        )

        # 逐个安排讲座
        for course_id, lecture_index in lectures_to_schedule:
            placement = self._find_placement(solution, course_id, lecture_index)
            if placement:
                day, timeslot, room_id = placement
                lecture = Lecture(
                    course_id=course_id,
                    lecture_index=lecture_index,
                    day=day,
                    timeslot=timeslot,
                    room_id=room_id
                )
                solution.lectures.append(lecture)

        return solution

    def _find_placement(self, solution: Solution, course_id: str,
                       lecture_index: int) -> Optional[Tuple[int, int, str]]:
        """
        为讲座寻找合适的位置

        Returns:
            (day, timeslot, room_id) 或 None
        """
        course = self.problem.courses[course_id]
        candidates = []

        # 尝试所有可能的时间和教室
        for day in range(self.problem.days):
            for timeslot in range(self.problem.periods_per_day):
                # 检查是否在不可用时段
                if (day, timeslot) in course.unavailable_periods:
                    continue

                # 检查是否有冲突
                if self._has_conflict(solution, course_id, day, timeslot):
                    continue

                # 尝试所有教室
                for room_id, room in self.problem.rooms.items():
                    # 检查教室是否被占用
                    if solution.get_lecture_in_room(day, timeslot, room_id):
                        continue

                    # 计算这个位置的得分
                    score = self._score_placement(solution, course_id, day, timeslot, room_id)
                    candidates.append((score, day, timeslot, room_id))

        if not candidates:
            return None

        # 选择得分最高的位置
        candidates.sort(reverse=True)
        return candidates[0][1], candidates[0][2], candidates[0][3]

    def _has_conflict(self, solution: Solution, course_id: str,
                     day: int, timeslot: int) -> bool:
        """检查是否有冲突"""
        course = self.problem.courses[course_id]
        lectures_at_time = solution.get_lectures_at(day, timeslot)

        for lec in lectures_at_time:
            other_course = self.problem.courses[lec.course_id]

            # 检查教师冲突
            if other_course.teacher == course.teacher:
                return True

            # 检查课程组冲突
            for curriculum in self.problem.curricula.values():
                if course_id in curriculum.courses and lec.course_id in curriculum.courses:
                    return True

        # 检查同一课程是否已在此时段有讲座
        course_lectures = solution.get_course_lectures(course_id)
        for lec in course_lectures:
            if lec.day == day and lec.timeslot == timeslot:
                return True

        return False

    def _score_placement(self, solution: Solution, course_id: str,
                        day: int, timeslot: int, room_id: str) -> float:
        """评估位置的优劣（分数越高越好）"""
        course = self.problem.courses[course_id]
        room = self.problem.rooms[room_id]
        score = 0.0

        # 教室容量匹配度
        if room.capacity >= course.students:
            score += 100
            # 容量刚好合适更好
            score -= (room.capacity - course.students) * 0.1
        else:
            # 容量不足扣分
            score -= (course.students - room.capacity) * 10

        # 教室稳定性：优先使用已经用过的教室
        course_lectures = solution.get_course_lectures(course_id)
        rooms_used = set(lec.room_id for lec in course_lectures)
        if room_id in rooms_used:
            score += 50

        # 工作天数分布
        days_used = set(lec.day for lec in course_lectures)
        if day not in days_used and len(days_used) < course.min_working_days:
            score += 30

        return score


if __name__ == '__main__':
    from pathlib import Path
    from src.ctt_parser import parse_ctt_file

    test_file = Path(__file__).parent.parent.parent / 'pycourse' / 'data' / 'comp01.ctt'
    if test_file.exists():
        print("Testing greedy solver...")
        problem = parse_ctt_file(str(test_file))
        solver = GreedySolver(problem, time_limit=30)
        solution = solver.solve()
        print(f"Scheduled {len(solution.lectures)} lectures")
