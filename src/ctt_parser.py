"""
CTT文件解析器 - 独立实现

解析ITC2007 Curriculum-Based Course Timetabling的.ctt格式文件
"""
from dataclasses import dataclass, field
from typing import Dict, List, Set, Tuple
from pathlib import Path


@dataclass
class Course:
    """课程"""
    id: str
    teacher: str
    lectures: int
    min_working_days: int
    students: int
    unavailable_periods: Set[Tuple[int, int]] = field(default_factory=set)


@dataclass
class Room:
    """教室"""
    id: str
    capacity: int


@dataclass
class Curriculum:
    """课程组"""
    id: str
    courses: List[str]


@dataclass
class Problem:
    """排课问题实例"""
    name: str
    days: int
    periods_per_day: int
    courses: Dict[str, Course]
    rooms: Dict[str, Room]
    curricula: Dict[str, Curriculum]

    @property
    def total_periods(self) -> int:
        return self.days * self.periods_per_day


def parse_ctt_file(file_path: str) -> Problem:
    """
    解析.ctt文件

    Args:
        file_path: .ctt文件路径

    Returns:
        Problem对象
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = [line.strip() for line in f.readlines()]

    # 解析头部信息
    name = lines[0].split(': ')[1]
    num_courses = int(lines[1].split(': ')[1])
    num_rooms = int(lines[2].split(': ')[1])
    days = int(lines[3].split(': ')[1])
    periods_per_day = int(lines[4].split(': ')[1])
    num_curricula = int(lines[5].split(': ')[1])
    num_constraints = int(lines[6].split(': ')[1])

    idx = 7
    # 跳过空行
    while idx < len(lines) and not lines[idx]:
        idx += 1

    # 解析课程
    courses = {}
    assert lines[idx] == "COURSES:"
    idx += 1

    for _ in range(num_courses):
        parts = lines[idx].split()
        course_id = parts[0]
        teacher = parts[1]
        lectures = int(parts[2])
        min_working_days = int(parts[3])
        students = int(parts[4])

        courses[course_id] = Course(
            id=course_id,
            teacher=teacher,
            lectures=lectures,
            min_working_days=min_working_days,
            students=students,
            unavailable_periods=set()
        )
        idx += 1

    # 跳过空行
    while idx < len(lines) and not lines[idx]:
        idx += 1

    # 解析教室
    rooms = {}
    assert lines[idx] == "ROOMS:"
    idx += 1

    for _ in range(num_rooms):
        parts = lines[idx].split()
        room_id = parts[0]
        capacity = int(parts[1])
        rooms[room_id] = Room(id=room_id, capacity=capacity)
        idx += 1

    # 跳过空行
    while idx < len(lines) and not lines[idx]:
        idx += 1

    # 解析课程组
    curricula = {}
    assert lines[idx] == "CURRICULA:"
    idx += 1

    for _ in range(num_curricula):
        parts = lines[idx].split()
        curriculum_id = parts[0]
        num_courses_in_curriculum = int(parts[1])
        course_ids = parts[2:2+num_courses_in_curriculum]

        curricula[curriculum_id] = Curriculum(
            id=curriculum_id,
            courses=course_ids
        )
        idx += 1

    # 跳过空行
    while idx < len(lines) and not lines[idx]:
        idx += 1

    # 解析不可用约束
    assert lines[idx] == "UNAVAILABILITY_CONSTRAINTS:"
    idx += 1

    for _ in range(num_constraints):
        parts = lines[idx].split()
        course_id = parts[0]
        day = int(parts[1])
        timeslot = int(parts[2])

        if course_id in courses:
            courses[course_id].unavailable_periods.add((day, timeslot))
        idx += 1

    return Problem(
        name=name,
        days=days,
        periods_per_day=periods_per_day,
        courses=courses,
        rooms=rooms,
        curricula=curricula
    )


if __name__ == '__main__':
    # 测试
    test_file = Path(__file__).parent.parent.parent / 'pycourse' / 'data' / 'comp01.ctt'
    if test_file.exists():
        problem = parse_ctt_file(str(test_file))
        print(f"Problem: {problem.name}")
        print(f"Courses: {len(problem.courses)}")
        print(f"Rooms: {len(problem.rooms)}")
        print(f"Days: {problem.days}")
        print(f"Periods per day: {problem.periods_per_day}")
