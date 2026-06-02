"""
特征提取模块 - Feature Extractor

从ITC2007 .ctt文件中提取数值特征，用于机器学习建模。
提取20个特征，涵盖规模、约束紧密度、资源匹配和时间分布四大类。
"""
from pathlib import Path
from typing import Dict, List
import numpy as np

from src.ctt_parser import parse_ctt_file, Problem


class FeatureExtractor:
    """特征提取器"""

    def __init__(self):
        self.feature_names = [
            # 规模类特征 (5个)
            'n_courses',
            'total_lectures',
            'n_rooms',
            'n_curricula',
            'n_unavailability_constraints',

            # 约束紧密度特征 (6个)
            'avg_curriculum_size',
            'max_curriculum_size',
            'constraint_density',
            'teacher_conflict_density',
            'avg_unavailable_per_course',
            'courses_in_curricula_ratio',

            # 资源匹配特征 (6个)
            'room_capacity_mean',
            'room_capacity_std',
            'student_count_mean',
            'student_count_std',
            'avg_students_per_room_capacity',
            'room_utilization_pressure',

            # 时间分布特征 (3个)
            'avg_min_working_days',
            'lectures_per_timeslot_ratio',
            'time_slack',
        ]

    def extract_from_file(self, ctt_file_path: str) -> Dict[str, float]:
        """从.ctt文件提取特征"""
        problem = parse_ctt_file(ctt_file_path)
        return self.extract_from_problem(problem)

    def extract_from_problem(self, problem: Problem) -> Dict[str, float]:
        """从Problem对象提取特征"""
        features = {}

        # ===== 1. 规模类特征 =====
        features['n_courses'] = len(problem.courses)
        features['total_lectures'] = sum(c.lectures for c in problem.courses.values())
        features['n_rooms'] = len(problem.rooms)
        features['n_curricula'] = len(problem.curricula)
        features['n_unavailability_constraints'] = sum(
            len(c.unavailable_periods) for c in problem.courses.values()
        )

        # ===== 2. 约束紧密度特征 =====
        curriculum_sizes = [len(cur.courses) for cur in problem.curricula.values()]
        features['avg_curriculum_size'] = np.mean(curriculum_sizes) if curriculum_sizes else 0
        features['max_curriculum_size'] = max(curriculum_sizes) if curriculum_sizes else 0

        total_curriculum_pairs = sum(len(cur.courses) * (len(cur.courses) - 1) / 2
                                     for cur in problem.curricula.values())
        max_possible_pairs = features['n_courses'] * (features['n_courses'] - 1) / 2
        features['constraint_density'] = (
            total_curriculum_pairs / max_possible_pairs if max_possible_pairs > 0 else 0
        )

        teacher_courses = {}
        for course_id, course in problem.courses.items():
            if course.teacher not in teacher_courses:
                teacher_courses[course.teacher] = []
            teacher_courses[course.teacher].append(course_id)

        teacher_conflict_pairs = sum(len(courses) * (len(courses) - 1) / 2
                                     for courses in teacher_courses.values())
        features['teacher_conflict_density'] = (
            teacher_conflict_pairs / max_possible_pairs if max_possible_pairs > 0 else 0
        )

        unavailable_counts = [len(c.unavailable_periods) for c in problem.courses.values()]
        features['avg_unavailable_per_course'] = (
            np.mean(unavailable_counts) if unavailable_counts else 0
        )

        courses_in_curricula = set()
        for curriculum in problem.curricula.values():
            courses_in_curricula.update(curriculum.courses)
        features['courses_in_curricula_ratio'] = (
            len(courses_in_curricula) / features['n_courses'] if features['n_courses'] > 0 else 0
        )

        # ===== 3. 资源匹配特征 =====
        room_capacities = [r.capacity for r in problem.rooms.values()]
        features['room_capacity_mean'] = np.mean(room_capacities) if room_capacities else 0
        features['room_capacity_std'] = np.std(room_capacities) if room_capacities else 0

        student_counts = [c.students for c in problem.courses.values()]
        features['student_count_mean'] = np.mean(student_counts) if student_counts else 0
        features['student_count_std'] = np.std(student_counts) if student_counts else 0

        features['avg_students_per_room_capacity'] = (
            features['student_count_mean'] / features['room_capacity_mean']
            if features['room_capacity_mean'] > 0 else 0
        )

        total_timeslots = problem.days * problem.periods_per_day
        total_slots = total_timeslots * features['n_rooms']
        features['room_utilization_pressure'] = (
            features['total_lectures'] / total_slots if total_slots > 0 else 0
        )

        # ===== 4. 时间分布特征 =====
        min_working_days = [c.min_working_days for c in problem.courses.values()]
        features['avg_min_working_days'] = (
            np.mean(min_working_days) if min_working_days else 0
        )

        features['lectures_per_timeslot_ratio'] = (
            features['total_lectures'] / total_timeslots if total_timeslots > 0 else 0
        )

        features['time_slack'] = total_slots - features['total_lectures']

        return features

    def extract_batch(self, ctt_files: List[str]) -> List[Dict[str, any]]:
        """批量提取特征"""
        results = []

        for ctt_file in ctt_files:
            try:
                instance_id = Path(ctt_file).stem
                features = self.extract_from_file(ctt_file)
                features['instance_id'] = instance_id
                results.append(features)
                print(f"[OK] Extract features: {instance_id}")
            except Exception as e:
                print(f"[ERROR] Failed: {ctt_file} - {e}")

        return results

    def get_feature_names(self) -> List[str]:
        """返回特征名称列表"""
        return self.feature_names.copy()
