from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Set, Tuple
import copy
import json
import os

@dataclass(frozen=True)
class TimeSlot:
    day: int
    period: int

    def label(self) -> str:
        days = ["周一", "周二", "周三", "周四", "周五"]
        return f"{days[self.day]} 第{self.period + 1}节"

    def to_dict(self) -> Dict[str, int]:
        return {"day": self.day, "period": self.period}

@dataclass
class Course:
    id: str
    name: str
    teacher_id: str
    group_ids: List[str]
    size: int
    sessions_per_week: int = 1
    preferred_slots: List[TimeSlot] = field(default_factory=list)
    preferred_room_features: List[str] = field(default_factory=list)

@dataclass
class Teacher:
    id: str
    name: str
    unavailable: Set[TimeSlot] = field(default_factory=set)
    preferred_slots: List[TimeSlot] = field(default_factory=list)

@dataclass
class Room:
    id: str
    name: str
    capacity: int
    features: Set[str] = field(default_factory=set)

@dataclass
class ClassGroup:
    id: str
    name: str
    size: int
    course_ids: List[str] = field(default_factory=list)

@dataclass
class Assignment:
    course_id: str
    room_id: str
    timeslot: TimeSlot

class Timetable:
    def __init__(self):
        self.courses: Dict[str, Course] = {}
        self.teachers: Dict[str, Teacher] = {}
        self.rooms: Dict[str, Room] = {}
        self.groups: Dict[str, ClassGroup] = {}
        self.timeslots: List[TimeSlot] = [TimeSlot(day, period) for day in range(5) for period in range(8)]
        self.assignments: Dict[str, Assignment] = {}

    def add_course(self, course: Course) -> None:
        self.courses[course.id] = course

    def add_teacher(self, teacher: Teacher) -> None:
        self.teachers[teacher.id] = teacher

    def add_room(self, room: Room) -> None:
        self.rooms[room.id] = room

    def add_group(self, group: ClassGroup) -> None:
        self.groups[group.id] = group

    def add_assignment(self, course_id: str, room_id: str, timeslot: TimeSlot) -> None:
        if course_id not in self.courses:
            raise KeyError(f"课程 {course_id} 不存在")
        if room_id not in self.rooms:
            raise KeyError(f"教室 {room_id} 不存在")
        self.assignments[course_id] = Assignment(course_id=course_id, room_id=room_id, timeslot=timeslot)

    def evaluate_constraints(self) -> Dict[str, int]:
        room_usage: Dict[Tuple[str, TimeSlot], List[str]] = {}
        teacher_usage: Dict[Tuple[str, TimeSlot], List[str]] = {}
        group_usage: Dict[Tuple[str, TimeSlot], List[str]] = {}

        hard_room_occupancy = 0
        hard_teacher_conflict = 0
        hard_group_conflict = 0
        hard_capacity = 0
        hard_teacher_unavailable = 0
        soft_preference_penalty = 0
        soft_teacher_preference = 0

        for assignment in self.assignments.values():
            course = self.courses[assignment.course_id]
            room = self.rooms[assignment.room_id]
            teacher = self.teachers[course.teacher_id]

            room_key = (assignment.room_id, assignment.timeslot)
            room_usage.setdefault(room_key, []).append(course.id)
            teacher_key = (course.teacher_id, assignment.timeslot)
            teacher_usage.setdefault(teacher_key, []).append(course.id)
            for group_id in course.group_ids:
                group_key = (group_id, assignment.timeslot)
                group_usage.setdefault(group_key, []).append(course.id)

            if room.capacity < course.size:
                hard_capacity += 1
            if assignment.timeslot in teacher.unavailable:
                hard_teacher_unavailable += 1
            if course.preferred_slots and assignment.timeslot not in course.preferred_slots:
                soft_preference_penalty += 1
            if teacher.preferred_slots and assignment.timeslot not in teacher.preferred_slots:
                soft_teacher_preference += 1

        hard_room_occupancy = sum(max(0, len(courses) - 1) for courses in room_usage.values())
        hard_teacher_conflict = sum(max(0, len(courses) - 1) for courses in teacher_usage.values())
        hard_group_conflict = sum(max(0, len(courses) - 1) for courses in group_usage.values())

        soft_total = soft_preference_penalty + soft_teacher_preference
        hard_total = hard_room_occupancy + hard_teacher_conflict + hard_group_conflict + hard_capacity + hard_teacher_unavailable

        return {
            "hard_room_occupancy": hard_room_occupancy,
            "hard_teacher_conflict": hard_teacher_conflict,
            "hard_group_conflict": hard_group_conflict,
            "hard_capacity": hard_capacity,
            "hard_teacher_unavailable": hard_teacher_unavailable,
            "soft_preference_penalty": soft_preference_penalty,
            "soft_teacher_preference": soft_teacher_preference,
            "hard_total": hard_total,
            "soft_total": soft_total,
            "score": -(hard_total * 100 + soft_total),
        }

class Solution:
    def __init__(self, timetable: Timetable):
        self.timetable = timetable
        self.assignments: List[Assignment] = list(timetable.assignments.values())

class DataLoader:
    @staticmethod
    def create_sample_data() -> Timetable:
        timetable = Timetable()

        teachers = [
            Teacher(id="T1", name="张老师", unavailable={TimeSlot(0, 7), TimeSlot(2, 2)}),
            Teacher(id="T2", name="李老师", unavailable={TimeSlot(1, 3), TimeSlot(3, 0)}),
            Teacher(id="T3", name="王老师", unavailable={TimeSlot(4, 5)}),
            Teacher(id="T4", name="赵老师", unavailable={TimeSlot(0, 0), TimeSlot(4, 7)}),
        ]
        for teacher in teachers:
            timetable.add_teacher(teacher)

        rooms = [
            Room(id="R1", name="教室101", capacity=40, features={"投影"}),
            Room(id="R2", name="教室102", capacity=30, features={"黑板"}),
            Room(id="R3", name="教室103", capacity=20, features={"投影", "空调"}),
        ]
        for room in rooms:
            timetable.add_room(room)

        groups = [
            ClassGroup(id="G1", name="高数班", size=35),
            ClassGroup(id="G2", name="英语班", size=28),
            ClassGroup(id="G3", name="编程班", size=22),
        ]
        for group in groups:
            timetable.add_group(group)

        courses = [
            Course(id="C1", name="高等数学", teacher_id="T1", group_ids=["G1"], size=35, preferred_slots=[TimeSlot(0, 1), TimeSlot(2, 1)]),
            Course(id="C2", name="大学英语", teacher_id="T2", group_ids=["G2"], size=28, preferred_slots=[TimeSlot(1, 2), TimeSlot(3, 2)]),
            Course(id="C3", name="程序设计", teacher_id="T3", group_ids=["G3"], size=22, preferred_slots=[TimeSlot(2, 3), TimeSlot(4, 3)]),
            Course(id="C4", name="线性代数", teacher_id="T1", group_ids=["G1"], size=35, preferred_slots=[TimeSlot(0, 2), TimeSlot(2, 2)]),
            Course(id="C5", name="物理", teacher_id="T4", group_ids=["G1", "G2"], size=30, preferred_slots=[TimeSlot(1, 1), TimeSlot(3, 1)]),
            Course(id="C6", name="计算机网络", teacher_id="T3", group_ids=["G3"], size=22, preferred_slots=[TimeSlot(4, 1), TimeSlot(4, 2)]),
        ]
        for course in courses:
            timetable.add_course(course)

        groups[0].course_ids.extend(["C1", "C4", "C5"])
        groups[1].course_ids.extend(["C2", "C5"])
        groups[2].course_ids.extend(["C3", "C6"])

        return timetable

class HybridSolver:
    def __init__(self, timetable: Timetable, seed: int = 0):
        self.base_timetable = copy.deepcopy(timetable)
        self.seed = seed

    def solve(self, time_limit: int = 5) -> Solution:
        timetable = copy.deepcopy(self.base_timetable)
        sorted_courses = sorted(
            timetable.courses.values(),
            key=lambda c: (-len(c.group_ids), c.size),
        )

        for course in sorted_courses:
            best_assignment = None
            best_metric = float('inf')
            for room in timetable.rooms.values():
                if room.capacity < course.size:
                    continue
                for timeslot in timetable.timeslots:
                    if self._is_forbidden(timetable, course, room, timeslot):
                        continue
                    candidate_timetable = copy.deepcopy(timetable)
                    candidate_timetable.add_assignment(course.id, room.id, timeslot)
                    metrics = candidate_timetable.evaluate_constraints()
                    cost = metrics['hard_total'] * 100 + metrics['soft_total']
                    if cost < best_metric:
                        best_metric = cost
                        best_assignment = (room.id, timeslot)
            if best_assignment is not None:
                timetable.add_assignment(course.id, best_assignment[0], best_assignment[1])
            else:
                fallback_room = min(timetable.rooms.values(), key=lambda r: abs(r.capacity - course.size))
                fallback_slot = timetable.timeslots[0]
                timetable.add_assignment(course.id, fallback_room.id, fallback_slot)

        self._local_improve(timetable)
        return Solution(timetable)

    def _is_forbidden(self, timetable: Timetable, course: Course, room: Room, timeslot: TimeSlot) -> bool:
        teacher = timetable.teachers[course.teacher_id]
        if timeslot in teacher.unavailable:
            return True
        for assignment in timetable.assignments.values():
            if assignment.timeslot == timeslot:
                if assignment.room_id == room.id:
                    return True
                assigned_course = timetable.courses[assignment.course_id]
                if assigned_course.teacher_id == course.teacher_id:
                    return True
                if set(assigned_course.group_ids) & set(course.group_ids):
                    return True
        return False

    def _local_improve(self, timetable: Timetable) -> None:
        baseline = timetable.evaluate_constraints()['score']
        for course in timetable.courses.values():
            current = timetable.assignments.get(course.id)
            if current is None:
                continue
            for room in timetable.rooms.values():
                for timeslot in timetable.timeslots:
                    if room.id == current.room_id and timeslot == current.timeslot:
                        continue
                    candidate_timetable = copy.deepcopy(timetable)
                    candidate_timetable.add_assignment(course.id, room.id, timeslot)
                    candidate_score = candidate_timetable.evaluate_constraints()['score']
                    if candidate_score > baseline:
                        timetable.assignments = candidate_timetable.assignments
                        baseline = candidate_score

class Evaluator:
    @staticmethod
    def evaluate_solution(solution: Solution) -> Dict[str, int]:
        if solution is None or solution.timetable is None:
            raise ValueError("无效的解")
        return solution.timetable.evaluate_constraints()

class OutputGenerator:
    @staticmethod
    def generate_timetable_csv(solution: Solution, path: str) -> None:
        lines = ["course_id,course_name,teacher,room,timeslot,groups"]
        timetable = solution.timetable
        for assignment in solution.assignments:
            course = timetable.courses[assignment.course_id]
            teacher = timetable.teachers[course.teacher_id]
            group_names = ";".join(course.group_ids)
            lines.append(
                f"{course.id},{course.name},{teacher.name},{assignment.room_id},{assignment.timeslot.label()},{group_names}"
            )
        directory = os.path.dirname(path)
        if directory:
            os.makedirs(directory, exist_ok=True)
        with open(path, "w", encoding="utf-8") as handle:
            handle.write("\n".join(lines))

    @staticmethod
    def generate_timetable_html(solution: Solution, path: str) -> None:
        rows = [
            "<tr><th>课程ID</th><th>课程名称</th><th>教师</th><th>教室</th><th>时间</th><th>班级</th></tr>"
        ]
        timetable = solution.timetable
        for assignment in solution.assignments:
            course = timetable.courses[assignment.course_id]
            teacher = timetable.teachers[course.teacher_id]
            group_names = ", ".join(course.group_ids)
            rows.append(
                f"<tr><td>{course.id}</td><td>{course.name}</td><td>{teacher.name}</td><td>{assignment.room_id}</td><td>{assignment.timeslot.label()}</td><td>{group_names}</td></tr>"
            )
        html = f"<html><head><meta charset='utf-8'><title>课表</title></head><body><table border='1'>{''.join(rows)}</table></body></html>"
        directory = os.path.dirname(path)
        if directory:
            os.makedirs(directory, exist_ok=True)
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(html)

    @staticmethod
    def generate_constraint_report(solution: Solution, path: str) -> None:
        evaluation = Evaluator.evaluate_solution(solution)
        report = {
            "assignments": [
                {
                    "course_id": assignment.course_id,
                    "room_id": assignment.room_id,
                    "timeslot": assignment.timeslot.to_dict(),
                }
                for assignment in solution.assignments
            ],
            "evaluation": evaluation,
        }
        directory = os.path.dirname(path)
        if directory:
            os.makedirs(directory, exist_ok=True)
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(report, handle, ensure_ascii=False, indent=2)
