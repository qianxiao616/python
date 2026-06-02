"""
CTT文件转CSV模块
将.ctt文件解析为扁平化的CSV格式
"""

import pandas as pd
import os
from typing import List, Dict, Tuple


class CTTParser:
    """CTT文件解析器"""

    def __init__(self, file_path: str):
        self.file_path = file_path
        self.name = ""
        self.courses = []
        self.rooms = []
        self.curricula = []
        self.constraints = []
        self.metadata = {}

    def parse(self) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """解析CTT文件，返回4个DataFrame"""
        with open(self.file_path, 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f.readlines()]

        current_section = None

        for line in lines:
            if not line or line.startswith('//'):
                continue

            # 元数据
            if ':' in line and not line.startswith('COURSES') and not line.startswith('ROOMS') and not line.startswith('CURRICULA') and not line.startswith('UNAVAILABILITY'):
                if line.startswith('Name:'):
                    self.name = line.split(':', 1)[1].strip()
                    self.metadata['name'] = self.name
                elif line.startswith('Courses:'):
                    self.metadata['n_courses'] = int(line.split(':')[1].strip())
                elif line.startswith('Rooms:'):
                    self.metadata['n_rooms'] = int(line.split(':')[1].strip())
                elif line.startswith('Days:'):
                    self.metadata['days'] = int(line.split(':')[1].strip())
                elif line.startswith('Periods_per_day:'):
                    self.metadata['periods_per_day'] = int(line.split(':')[1].strip())
                elif line.startswith('Curricula:'):
                    self.metadata['n_curricula'] = int(line.split(':')[1].strip())
                elif line.startswith('Constraints:'):
                    self.metadata['n_constraints'] = int(line.split(':')[1].strip())
                continue

            # 切换section
            if line.startswith('COURSES:'):
                current_section = 'COURSES'
                continue
            elif line.startswith('ROOMS:'):
                current_section = 'ROOMS'
                continue
            elif line.startswith('CURRICULA:'):
                current_section = 'CURRICULA'
                continue
            elif line.startswith('UNAVAILABILITY_CONSTRAINTS:'):
                current_section = 'CONSTRAINTS'
                continue

            # 解析数据
            if current_section == 'COURSES':
                parts = line.split()
                if len(parts) >= 5:
                    self.courses.append({
                        'course_id': parts[0],
                        'teacher_id': parts[1],
                        'n_lectures': int(parts[2]),
                        'min_working_days': int(parts[3]),
                        'n_students': int(parts[4]),
                        'instance': self.name
                    })

            elif current_section == 'ROOMS':
                parts = line.split()
                if len(parts) >= 2:
                    self.rooms.append({
                        'room_id': parts[0],
                        'capacity': int(parts[1]),
                        'instance': self.name
                    })

            elif current_section == 'CURRICULA':
                parts = line.split()
                if len(parts) >= 2:
                    curriculum_id = parts[0]
                    n_courses = int(parts[1])
                    course_list = parts[2:2+n_courses]
                    for course in course_list:
                        self.curricula.append({
                            'curriculum_id': curriculum_id,
                            'course_id': course,
                            'instance': self.name
                        })

            elif current_section == 'CONSTRAINTS':
                parts = line.split()
                if len(parts) >= 3:
                    self.constraints.append({
                        'course_id': parts[0],
                        'day': int(parts[1]),
                        'period': int(parts[2]),
                        'instance': self.name
                    })

        # 转换为DataFrame
        df_courses = pd.DataFrame(self.courses)
        df_rooms = pd.DataFrame(self.rooms)
        df_curricula = pd.DataFrame(self.curricula)
        df_constraints = pd.DataFrame(self.constraints)

        return df_courses, df_rooms, df_curricula, df_constraints


def convert_all_ctt_to_csv(ctt_dir: str, output_prefix: str) -> Dict[str, pd.DataFrame]:
    """
    批量转换所有.ctt文件为CSV

    Args:
        ctt_dir: .ctt文件所在目录
        output_prefix: 输出文件前缀（如'clean'或'dirty'）

    Returns:
        包含4个DataFrame的字典
    """
    all_courses = []
    all_rooms = []
    all_curricula = []
    all_constraints = []

    ctt_files = sorted([f for f in os.listdir(ctt_dir) if f.endswith('.ctt')])

    print(f"找到 {len(ctt_files)} 个.ctt文件")

    for ctt_file in ctt_files:
        file_path = os.path.join(ctt_dir, ctt_file)
        parser = CTTParser(file_path)

        try:
            df_courses, df_rooms, df_curricula, df_constraints = parser.parse()

            all_courses.append(df_courses)
            all_rooms.append(df_rooms)
            all_curricula.append(df_curricula)
            all_constraints.append(df_constraints)

            print(f"[OK] 解析完成: {ctt_file}")
        except Exception as e:
            print(f"[FAIL] 解析失败: {ctt_file} - {e}")

    # 合并所有DataFrame
    df_all_courses = pd.concat(all_courses, ignore_index=True)
    df_all_rooms = pd.concat(all_rooms, ignore_index=True)
    df_all_curricula = pd.concat(all_curricula, ignore_index=True)
    df_all_constraints = pd.concat(all_constraints, ignore_index=True)

    print(f"\n总计:")
    print(f"  课程: {len(df_all_courses)} 条")
    print(f"  教室: {len(df_all_rooms)} 条")
    print(f"  课程组: {len(df_all_curricula)} 条")
    print(f"  约束: {len(df_all_constraints)} 条")

    return {
        'courses': df_all_courses,
        'rooms': df_all_rooms,
        'curricula': df_all_curricula,
        'constraints': df_all_constraints
    }


if __name__ == "__main__":
    # 测试解析
    ctt_dir = "../data"
    dfs = convert_all_ctt_to_csv(ctt_dir, "clean")

    # 保存
    for name, df in dfs.items():
        output_path = f"../data_cleaning/clean_{name}.csv"
        df.to_csv(output_path, index=False)
        print(f"保存: {output_path}")
