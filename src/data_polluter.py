"""
数据污染模块
对干净的CSV数据注入各种类型的脏数据
"""

import pandas as pd
import numpy as np
import random
from typing import Dict, List
import copy


class DataPolluter:
    """数据污染器"""

    def __init__(self, pollution_rate: float = 0.18):
        """
        Args:
            pollution_rate: 总体污染比例（默认18%）
        """
        self.pollution_rate = pollution_rate
        self.pollution_log = []

    def pollute_all(self, dfs: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
        """
        污染所有数据表

        Args:
            dfs: 包含courses, rooms, curricula, constraints的字典

        Returns:
            污染后的数据字典
        """
        polluted_dfs = {}

        print(f"\n{'='*60}")
        print(f"开始数据污染 (总体污染率: {self.pollution_rate*100:.1f}%)")
        print(f"{'='*60}\n")

        # 污染课程数据
        polluted_dfs['courses'] = self._pollute_courses(dfs['courses'].copy())

        # 污染教室数据
        polluted_dfs['rooms'] = self._pollute_rooms(dfs['rooms'].copy())

        # 污染课程组数据
        polluted_dfs['curricula'] = self._pollute_curricula(dfs['curricula'].copy(), dfs['courses'])

        # 污染约束数据
        polluted_dfs['constraints'] = self._pollute_constraints(dfs['constraints'].copy(), dfs['courses'])

        return polluted_dfs

    def _pollute_courses(self, df: pd.DataFrame) -> pd.DataFrame:
        """污染课程数据"""
        print("[COURSES] 污染课程数据...")
        n_rows = len(df)
        n_pollute = int(n_rows * self.pollution_rate)

        polluted_count = 0

        # 1. 缺失值污染 (5%)
        missing_indices = random.sample(range(n_rows), int(n_rows * 0.05))
        for idx in missing_indices:
            col = random.choice(['course_id', 'teacher_id', 'n_lectures', 'min_working_days', 'n_students'])
            original_value = df.at[idx, col]
            df.at[idx, col] = np.nan
            self.pollution_log.append(f"课程[{idx}] {col}: {original_value} -> NaN (缺失值)")
            polluted_count += 1

        # 2. 异常值污染 (8%)
        outlier_indices = random.sample(range(n_rows), int(n_rows * 0.08))
        for idx in outlier_indices:
            pollution_type = random.choice(['negative', 'huge', 'zero', 'exceed_days'])

            if pollution_type == 'negative':
                col = random.choice(['n_lectures', 'n_students'])
                original_value = df.at[idx, col]
                df.at[idx, col] = -abs(df.at[idx, col])
                self.pollution_log.append(f"课程[{idx}] {col}: {original_value} -> {df.at[idx, col]} (负数)")

            elif pollution_type == 'huge':
                original_value = df.at[idx, 'n_students']
                df.at[idx, 'n_students'] = random.randint(10000, 50000)
                self.pollution_log.append(f"课程[{idx}] n_students: {original_value} -> {df.at[idx, 'n_students']} (超大值)")

            elif pollution_type == 'zero':
                col = random.choice(['n_lectures', 'min_working_days'])
                original_value = df.at[idx, col]
                df.at[idx, col] = 0
                self.pollution_log.append(f"课程[{idx}] {col}: {original_value} -> 0 (零值)")

            elif pollution_type == 'exceed_days':
                original_value = df.at[idx, 'min_working_days']
                df.at[idx, 'min_working_days'] = 10  # 超过5天
                self.pollution_log.append(f"课程[{idx}] min_working_days: {original_value} -> 10 (超限)")

            polluted_count += 1

        # 3. 格式错误 (3%)
        format_indices = random.sample(range(n_rows), int(n_rows * 0.03))
        for idx in format_indices:
            original_value = df.at[idx, 'n_lectures']
            df.at[idx, 'n_lectures'] = f"{df.at[idx, 'n_lectures']}abc"  # 数字中混入字母
            self.pollution_log.append(f"课程[{idx}] n_lectures: {original_value} -> {df.at[idx, 'n_lectures']} (格式错误)")
            polluted_count += 1

        # 4. 重复数据 (2%)
        n_dup = min(int(n_rows * 0.02), min(50, n_rows))
        if n_dup > 0:
            dup_indices = random.sample(range(min(50, n_rows)), n_dup)
            for idx in dup_indices:
                df = pd.concat([df, df.iloc[[idx]]], ignore_index=True)
                self.pollution_log.append(f"课程[{idx}] 创建重复行")
                polluted_count += 1

        print(f"  [OK] 污染 {polluted_count} 处\n")
        return df

    def _pollute_rooms(self, df: pd.DataFrame) -> pd.DataFrame:
        """污染教室数据"""
        print("[ROOMS] 污染教室数据...")
        n_rows = len(df)
        polluted_count = 0

        # 1. 缺失值 (5%)
        missing_indices = random.sample(range(n_rows), int(n_rows * 0.05))
        for idx in missing_indices:
            col = random.choice(['room_id', 'capacity'])
            original_value = df.at[idx, col]
            df.at[idx, col] = np.nan
            self.pollution_log.append(f"教室[{idx}] {col}: {original_value} -> NaN")
            polluted_count += 1

        # 2. 异常值 (8%)
        outlier_indices = random.sample(range(n_rows), int(n_rows * 0.08))
        for idx in outlier_indices:
            pollution_type = random.choice(['negative', 'huge', 'zero'])
            original_value = df.at[idx, 'capacity']

            if pollution_type == 'negative':
                df.at[idx, 'capacity'] = -abs(df.at[idx, 'capacity'])
            elif pollution_type == 'huge':
                df.at[idx, 'capacity'] = random.randint(10000, 50000)
            elif pollution_type == 'zero':
                df.at[idx, 'capacity'] = 0

            self.pollution_log.append(f"教室[{idx}] capacity: {original_value} -> {df.at[idx, 'capacity']} ({pollution_type})")
            polluted_count += 1

        # 3. 重复数据 (3%)
        n_dup = min(int(n_rows * 0.03), min(20, n_rows))
        if n_dup > 0:
            dup_indices = random.sample(range(min(20, n_rows)), n_dup)
            for idx in dup_indices:
                df = pd.concat([df, df.iloc[[idx]]], ignore_index=True)
                self.pollution_log.append(f"教室[{idx}] 创建重复行")
                polluted_count += 1

        # 4. 格式错误（多余空格）
        format_indices = random.sample(range(n_rows), int(n_rows * 0.02))
        for idx in format_indices:
            original_value = df.at[idx, 'room_id']
            df.at[idx, 'room_id'] = f"  {df.at[idx, 'room_id']}  "  # 前后加空格
            self.pollution_log.append(f"教室[{idx}] room_id: '{original_value}' -> '{df.at[idx, 'room_id']}' (多余空格)")
            polluted_count += 1

        print(f"  [OK] 污染 {polluted_count} 处\n")
        return df

    def _pollute_curricula(self, df: pd.DataFrame, courses_df: pd.DataFrame) -> pd.DataFrame:
        """污染课程组数据"""
        print("[CURRICULA] 污染课程组数据...")
        n_rows = len(df)
        polluted_count = 0

        # 1. 缺失值 (5%)
        missing_indices = random.sample(range(n_rows), int(n_rows * 0.05))
        for idx in missing_indices:
            col = random.choice(['curriculum_id', 'course_id'])
            original_value = df.at[idx, col]
            df.at[idx, col] = np.nan
            self.pollution_log.append(f"课程组[{idx}] {col}: {original_value} -> NaN")
            polluted_count += 1

        # 2. 引用完整性破坏 (10%) - 引用不存在的课程
        integrity_indices = random.sample(range(n_rows), int(n_rows * 0.10))
        for idx in integrity_indices:
            original_value = df.at[idx, 'course_id']
            df.at[idx, 'course_id'] = f"c9999"  # 不存在的课程ID
            self.pollution_log.append(f"课程组[{idx}] course_id: {original_value} -> c9999 (引用完整性破坏)")
            polluted_count += 1

        # 3. 重复数据 (3%)
        n_dup = min(int(n_rows * 0.03), min(50, n_rows))
        if n_dup > 0:
            dup_indices = random.sample(range(min(50, n_rows)), n_dup)
            for idx in dup_indices:
                df = pd.concat([df, df.iloc[[idx]]], ignore_index=True)
                self.pollution_log.append(f"课程组[{idx}] 创建重复行")
                polluted_count += 1

        print(f"  [OK] 污染 {polluted_count} 处\n")
        return df

    def _pollute_constraints(self, df: pd.DataFrame, courses_df: pd.DataFrame) -> pd.DataFrame:
        """污染约束数据"""
        print("[CONSTRAINTS] 污染约束数据...")
        n_rows = len(df)
        polluted_count = 0

        # 1. 缺失值 (5%)
        missing_indices = random.sample(range(n_rows), int(n_rows * 0.05))
        for idx in missing_indices:
            col = random.choice(['course_id', 'day', 'period'])
            original_value = df.at[idx, col]
            df.at[idx, col] = np.nan
            self.pollution_log.append(f"约束[{idx}] {col}: {original_value} -> NaN")
            polluted_count += 1

        # 2. 异常值 (8%)
        outlier_indices = random.sample(range(n_rows), int(n_rows * 0.08))
        for idx in outlier_indices:
            pollution_type = random.choice(['negative_day', 'exceed_day', 'negative_period', 'exceed_period'])

            if pollution_type == 'negative_day':
                original_value = df.at[idx, 'day']
                df.at[idx, 'day'] = -1
                self.pollution_log.append(f"约束[{idx}] day: {original_value} -> -1 (负数)")
            elif pollution_type == 'exceed_day':
                original_value = df.at[idx, 'day']
                df.at[idx, 'day'] = 10  # 超过5天
                self.pollution_log.append(f"约束[{idx}] day: {original_value} -> 10 (超限)")
            elif pollution_type == 'negative_period':
                original_value = df.at[idx, 'period']
                df.at[idx, 'period'] = -1
                self.pollution_log.append(f"约束[{idx}] period: {original_value} -> -1 (负数)")
            elif pollution_type == 'exceed_period':
                original_value = df.at[idx, 'period']
                df.at[idx, 'period'] = 10  # 超过6个时段
                self.pollution_log.append(f"约束[{idx}] period: {original_value} -> 10 (超限)")

            polluted_count += 1

        # 3. 引用完整性破坏 (8%)
        integrity_indices = random.sample(range(n_rows), int(n_rows * 0.08))
        for idx in integrity_indices:
            original_value = df.at[idx, 'course_id']
            df.at[idx, 'course_id'] = f"c8888"  # 不存在的课程ID
            self.pollution_log.append(f"约束[{idx}] course_id: {original_value} -> c8888 (引用完整性破坏)")
            polluted_count += 1

        # 4. 重复数据 (2%)
        n_dup = min(int(n_rows * 0.02), min(50, n_rows))
        if n_dup > 0:
            dup_indices = random.sample(range(min(50, n_rows)), n_dup)
            for idx in dup_indices:
                df = pd.concat([df, df.iloc[[idx]]], ignore_index=True)
                self.pollution_log.append(f"约束[{idx}] 创建重复行")
                polluted_count += 1

        print(f"  [OK] 污染 {polluted_count} 处\n")
        return df

    def save_pollution_log(self, output_path: str):
        """保存污染日志"""
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("数据污染日志\n")
            f.write("="*80 + "\n\n")
            f.write(f"总计污染: {len(self.pollution_log)} 处\n\n")
            f.write("详细记录:\n")
            f.write("-"*80 + "\n")
            for i, log in enumerate(self.pollution_log, 1):
                f.write(f"{i}. {log}\n")

        print(f"[OK] 污染日志已保存: {output_path}")


if __name__ == "__main__":
    print("请通过主程序运行此模块")
