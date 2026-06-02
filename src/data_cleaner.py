"""
数据清洗模块
处理污染数据中的各种问题
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
import re


class DataCleaner:
    """数据清洗器"""

    def __init__(self):
        self.cleaning_report = []
        self.stats = {
            'missing_filled': 0,
            'outliers_corrected': 0,
            'integrity_fixed': 0,
            'format_normalized': 0,
            'duplicates_removed': 0
        }

    def clean_all(self, dfs: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
        """
        清洗所有数据表

        Args:
            dfs: 包含courses, rooms, curricula, constraints的字典

        Returns:
            清洗后的数据字典
        """
        cleaned_dfs = {}

        print(f"\n{'='*60}")
        print(f"开始数据清洗")
        print(f"{'='*60}\n")

        # 清洗课程数据
        cleaned_dfs['courses'] = self._clean_courses(dfs['courses'].copy())

        # 清洗教室数据
        cleaned_dfs['rooms'] = self._clean_rooms(dfs['rooms'].copy())

        # 清洗课程组数据（需要参考课程数据）
        cleaned_dfs['curricula'] = self._clean_curricula(dfs['curricula'].copy(), cleaned_dfs['courses'])

        # 清洗约束数据（需要参考课程数据）
        cleaned_dfs['constraints'] = self._clean_constraints(dfs['constraints'].copy(), cleaned_dfs['courses'])

        return cleaned_dfs

    def _clean_courses(self, df: pd.DataFrame) -> pd.DataFrame:
        """清洗课程数据"""
        print("[COURSES] 清洗课程数据...")
        initial_rows = len(df)

        # 1. 去重
        before_dup = len(df)
        df = df.drop_duplicates(subset=['course_id', 'instance'], keep='first')
        dup_removed = before_dup - len(df)
        if dup_removed > 0:
            self.stats['duplicates_removed'] += dup_removed
            self.cleaning_report.append(f"课程数据: 移除 {dup_removed} 个重复行")

        # 2. 格式规范化
        # 2.1 去除ID中的空格
        df['course_id'] = df['course_id'].astype(str).str.strip()
        df['teacher_id'] = df['teacher_id'].astype(str).str.strip()

        # 2.2 修正数值字段中的格式错误（移除字母）
        for col in ['n_lectures', 'min_working_days', 'n_students']:
            format_issues = df[col].apply(lambda x: isinstance(x, str) and not x.replace('-', '').isdigit())
            format_count = format_issues.sum()
            if format_count > 0:
                self.stats['format_normalized'] += format_count
                self.cleaning_report.append(f"课程数据: 修正 {format_count} 个 {col} 格式错误")
                # 提取数字部分
                df[col] = df[col].apply(lambda x: re.sub(r'[^0-9-]', '', str(x)) if pd.notna(x) else x)

        # 3. 类型转换（先转换为数值，错误的会变成NaN）
        for col in ['n_lectures', 'min_working_days', 'n_students']:
            df[col] = pd.to_numeric(df[col], errors='coerce')

        # 4. 缺失值填充
        missing_before = df.isnull().sum().sum()

        # course_id缺失：生成新ID
        if df['course_id'].isnull().any():
            null_count = df['course_id'].isnull().sum()
            for idx in df[df['course_id'].isnull()].index:
                df.at[idx, 'course_id'] = f"c_generated_{idx}"
            self.cleaning_report.append(f"课程数据: 生成 {null_count} 个缺失的course_id")

        # teacher_id缺失：使用默认值
        if df['teacher_id'].isnull().any():
            null_count = df['teacher_id'].isnull().sum()
            df['teacher_id'].fillna('t_unknown', inplace=True)
            self.cleaning_report.append(f"课程数据: 填充 {null_count} 个缺失的teacher_id为't_unknown'")

        # 数值字段缺失：使用中位数
        for col in ['n_lectures', 'min_working_days', 'n_students']:
            if df[col].isnull().any():
                null_count = df[col].isnull().sum()
                median_val = df[col].median()
                df[col].fillna(median_val, inplace=True)
                self.cleaning_report.append(f"课程数据: 填充 {null_count} 个缺失的{col}为中位数{median_val:.0f}")

        missing_after = df.isnull().sum().sum()
        self.stats['missing_filled'] += (missing_before - missing_after)

        # 5. 异常值修正
        outliers_fixed = 0

        # 负数修正
        for col in ['n_lectures', 'min_working_days', 'n_students']:
            negative_mask = df[col] < 0
            if negative_mask.any():
                count = negative_mask.sum()
                df.loc[negative_mask, col] = df.loc[negative_mask, col].abs()
                self.cleaning_report.append(f"课程数据: 修正 {count} 个{col}负数为绝对值")
                outliers_fixed += count

        # 零值修正（讲座数和工作天数不能为0）
        for col in ['n_lectures', 'min_working_days']:
            zero_mask = df[col] == 0
            if zero_mask.any():
                count = zero_mask.sum()
                df.loc[zero_mask, col] = 1
                self.cleaning_report.append(f"课程数据: 修正 {count} 个{col}零值为1")
                outliers_fixed += count

        # 超大值修正（学生数上限5000）
        huge_mask = df['n_students'] > 5000
        if huge_mask.any():
            count = huge_mask.sum()
            median_students = df['n_students'].median()
            df.loc[huge_mask, 'n_students'] = median_students
            self.cleaning_report.append(f"课程数据: 修正 {count} 个超大学生数为中位数{median_students:.0f}")
            outliers_fixed += count

        # 工作天数超限（不能超过5天）
        exceed_mask = df['min_working_days'] > 5
        if exceed_mask.any():
            count = exceed_mask.sum()
            df.loc[exceed_mask, 'min_working_days'] = 5
            self.cleaning_report.append(f"课程数据: 修正 {count} 个超限工作天数为5")
            outliers_fixed += count

        self.stats['outliers_corrected'] += outliers_fixed

        # 6. 确保数据类型正确
        df['n_lectures'] = df['n_lectures'].astype(int)
        df['min_working_days'] = df['min_working_days'].astype(int)
        df['n_students'] = df['n_students'].astype(int)

        final_rows = len(df)
        print(f"  [OK] 清洗完成: {initial_rows} 行 -> {final_rows} 行\n")
        return df

    def _clean_rooms(self, df: pd.DataFrame) -> pd.DataFrame:
        """清洗教室数据"""
        print("[ROOMS] 清洗教室数据...")
        initial_rows = len(df)

        # 1. 去重
        before_dup = len(df)
        df = df.drop_duplicates(subset=['room_id', 'instance'], keep='first')
        dup_removed = before_dup - len(df)
        if dup_removed > 0:
            self.stats['duplicates_removed'] += dup_removed
            self.cleaning_report.append(f"教室数据: 移除 {dup_removed} 个重复行")

        # 2. 格式规范化（去除空格）
        df['room_id'] = df['room_id'].astype(str).str.strip()

        # 3. 类型转换
        df['capacity'] = pd.to_numeric(df['capacity'], errors='coerce')

        # 4. 缺失值填充
        if df['room_id'].isnull().any():
            null_count = df['room_id'].isnull().sum()
            for idx in df[df['room_id'].isnull()].index:
                df.at[idx, 'room_id'] = f"room_{idx}"
            self.cleaning_report.append(f"教室数据: 生成 {null_count} 个缺失的room_id")
            self.stats['missing_filled'] += null_count

        if df['capacity'].isnull().any():
            null_count = df['capacity'].isnull().sum()
            median_capacity = df['capacity'].median()
            df['capacity'].fillna(median_capacity, inplace=True)
            self.cleaning_report.append(f"教室数据: 填充 {null_count} 个缺失容量为中位数{median_capacity:.0f}")
            self.stats['missing_filled'] += null_count

        # 5. 异常值修正
        outliers_fixed = 0

        # 负数和零值修正
        invalid_mask = df['capacity'] <= 0
        if invalid_mask.any():
            count = invalid_mask.sum()
            median_capacity = df.loc[df['capacity'] > 0, 'capacity'].median()
            df.loc[invalid_mask, 'capacity'] = median_capacity
            self.cleaning_report.append(f"教室数据: 修正 {count} 个无效容量为中位数{median_capacity:.0f}")
            outliers_fixed += count

        # 超大值修正（容量上限1000）
        huge_mask = df['capacity'] > 1000
        if huge_mask.any():
            count = huge_mask.sum()
            median_capacity = df['capacity'].median()
            df.loc[huge_mask, 'capacity'] = median_capacity
            self.cleaning_report.append(f"教室数据: 修正 {count} 个超大容量为中位数{median_capacity:.0f}")
            outliers_fixed += count

        self.stats['outliers_corrected'] += outliers_fixed

        # 6. 确保数据类型
        df['capacity'] = df['capacity'].astype(int)

        final_rows = len(df)
        print(f"  [OK] 清洗完成: {initial_rows} 行 -> {final_rows} 行\n")
        return df

    def _clean_curricula(self, df: pd.DataFrame, courses_df: pd.DataFrame) -> pd.DataFrame:
        """清洗课程组数据"""
        print("[CURRICULA] 清洗课程组数据...")
        initial_rows = len(df)

        # 如果数据为空，直接返回
        if len(df) == 0:
            print(f"  [OK] 清洗完成: {initial_rows} 行 -> {initial_rows} 行 (空数据)\n")
            return df

        # 1. 去重
        before_dup = len(df)
        df = df.drop_duplicates(subset=['curriculum_id', 'course_id', 'instance'], keep='first')
        dup_removed = before_dup - len(df)
        if dup_removed > 0:
            self.stats['duplicates_removed'] += dup_removed
            self.cleaning_report.append(f"课程组数据: 移除 {dup_removed} 个重复行")

        # 2. 格式规范化
        df['curriculum_id'] = df['curriculum_id'].astype(str).str.strip()
        df['course_id'] = df['course_id'].astype(str).str.strip()

        # 3. 缺失值处理（直接删除）
        missing_before = len(df)
        df = df.dropna(subset=['curriculum_id', 'course_id'])
        missing_removed = missing_before - len(df)
        if missing_removed > 0:
            self.cleaning_report.append(f"课程组数据: 删除 {missing_removed} 个含缺失值的行")
            self.stats['missing_filled'] += missing_removed

        # 4. 引用完整性检查
        # 获取有效的课程ID集合（按instance分组）
        valid_courses = set()
        for instance in df['instance'].unique():
            instance_courses = courses_df[courses_df['instance'] == instance]['course_id'].unique()
            valid_courses.update(instance_courses)

        # 标记无效引用
        invalid_mask = ~df['course_id'].isin(valid_courses)
        if invalid_mask.any():
            count = invalid_mask.sum()
            df = df[~invalid_mask]
            self.cleaning_report.append(f"课程组数据: 删除 {count} 个无效的课程引用")
            self.stats['integrity_fixed'] += count

        final_rows = len(df)
        print(f"  [OK] 清洗完成: {initial_rows} 行 -> {final_rows} 行\n")
        return df

    def _clean_constraints(self, df: pd.DataFrame, courses_df: pd.DataFrame) -> pd.DataFrame:
        """清洗约束数据"""
        print("[CONSTRAINTS] 清洗约束数据...")
        initial_rows = len(df)

        # 如果数据为空，直接返回
        if len(df) == 0:
            print(f"  [OK] 清洗完成: {initial_rows} 行 -> {initial_rows} 行 (空数据)\n")
            return df

        # 1. 去重
        before_dup = len(df)
        df = df.drop_duplicates(subset=['course_id', 'day', 'period', 'instance'], keep='first')
        dup_removed = before_dup - len(df)
        if dup_removed > 0:
            self.stats['duplicates_removed'] += dup_removed
            self.cleaning_report.append(f"约束数据: 移除 {dup_removed} 个重复行")

        # 2. 格式规范化
        df['course_id'] = df['course_id'].astype(str).str.strip()

        # 3. 类型转换
        df['day'] = pd.to_numeric(df['day'], errors='coerce')
        df['period'] = pd.to_numeric(df['period'], errors='coerce')

        # 4. 缺失值处理（删除含缺失值的行）
        missing_before = len(df)
        df = df.dropna(subset=['course_id', 'day', 'period'])
        missing_removed = missing_before - len(df)
        if missing_removed > 0:
            self.cleaning_report.append(f"约束数据: 删除 {missing_removed} 个含缺失值的行")
            self.stats['missing_filled'] += missing_removed

        # 5. 异常值修正
        outliers_fixed = 0

        # day范围修正（0-4）
        invalid_day = (df['day'] < 0) | (df['day'] > 4)
        if invalid_day.any():
            count = invalid_day.sum()
            df = df[~invalid_day]
            self.cleaning_report.append(f"约束数据: 删除 {count} 个无效day值的行")
            outliers_fixed += count

        # period范围修正（0-5）
        invalid_period = (df['period'] < 0) | (df['period'] > 5)
        if invalid_period.any():
            count = invalid_period.sum()
            df = df[~invalid_period]
            self.cleaning_report.append(f"约束数据: 删除 {count} 个无效period值的行")
            outliers_fixed += count

        self.stats['outliers_corrected'] += outliers_fixed

        # 6. 引用完整性检查
        valid_courses = set()
        for instance in df['instance'].unique():
            instance_courses = courses_df[courses_df['instance'] == instance]['course_id'].unique()
            valid_courses.update(instance_courses)

        invalid_mask = ~df['course_id'].isin(valid_courses)
        if invalid_mask.any():
            count = invalid_mask.sum()
            df = df[~invalid_mask]
            self.cleaning_report.append(f"约束数据: 删除 {count} 个无效的课程引用")
            self.stats['integrity_fixed'] += count

        # 7. 确保数据类型
        df['day'] = df['day'].astype(int)
        df['period'] = df['period'].astype(int)

        final_rows = len(df)
        print(f"  [OK] 清洗完成: {initial_rows} 行 -> {final_rows} 行\n")
        return df

    def generate_report(self, output_path: str, dirty_dfs: Dict, cleaned_dfs: Dict):
        """生成清洗报告"""
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("="*80 + "\n")
            f.write("数据清洗报告\n")
            f.write("="*80 + "\n\n")

            # 1. 总览
            f.write("一、清洗统计总览\n")
            f.write("-"*80 + "\n")
            f.write(f"缺失值填充/处理: {self.stats['missing_filled']} 处\n")
            f.write(f"异常值修正: {self.stats['outliers_corrected']} 处\n")
            f.write(f"引用完整性修复: {self.stats['integrity_fixed']} 处\n")
            f.write(f"格式规范化: {self.stats['format_normalized']} 处\n")
            f.write(f"重复数据删除: {self.stats['duplicates_removed']} 条\n")
            f.write(f"\n总计处理: {sum(self.stats.values())} 处问题\n\n")

            # 2. 各表数据变化
            f.write("二、各表数据行数变化\n")
            f.write("-"*80 + "\n")
            for table_name in ['courses', 'rooms', 'curricula', 'constraints']:
                dirty_count = len(dirty_dfs[table_name])
                clean_count = len(cleaned_dfs[table_name])
                diff = dirty_count - clean_count
                f.write(f"{table_name.ljust(15)}: {dirty_count} 行 -> {clean_count} 行 "
                       f"(删除 {diff} 行)\n")
            f.write("\n")

            # 3. 详细清洗记录
            f.write("三、详细清洗记录\n")
            f.write("-"*80 + "\n")
            for i, record in enumerate(self.cleaning_report, 1):
                f.write(f"{i}. {record}\n")
            f.write("\n")

            # 4. 数据质量评估
            f.write("四、清洗后数据质量评估\n")
            f.write("-"*80 + "\n")
            for table_name, df in cleaned_dfs.items():
                f.write(f"\n{table_name.upper()}:\n")
                f.write(f"  总行数: {len(df)}\n")
                f.write(f"  缺失值: {df.isnull().sum().sum()}\n")

                if len(df) == 0:
                    f.write(f"  (空数据表)\n")
                    continue

                if table_name == 'courses':
                    f.write(f"  n_lectures范围: [{df['n_lectures'].min()}, {df['n_lectures'].max()}]\n")
                    f.write(f"  n_students范围: [{df['n_students'].min()}, {df['n_students'].max()}]\n")
                    f.write(f"  min_working_days范围: [{df['min_working_days'].min()}, {df['min_working_days'].max()}]\n")
                elif table_name == 'rooms':
                    f.write(f"  capacity范围: [{df['capacity'].min()}, {df['capacity'].max()}]\n")
                elif table_name == 'constraints':
                    f.write(f"  day范围: [{df['day'].min()}, {df['day'].max()}]\n")
                    f.write(f"  period范围: [{df['period'].min()}, {df['period'].max()}]\n")

            f.write("\n" + "="*80 + "\n")
            f.write("清洗完成！数据已符合质量要求。\n")
            f.write("="*80 + "\n")

        print(f"\n[OK] 清洗报告已保存: {output_path}\n")


if __name__ == "__main__":
    print("请通过主程序运行此模块")
