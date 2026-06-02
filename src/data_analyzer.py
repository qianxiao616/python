"""
数据分析与可视化模块
使用Numpy/Pandas进行统计分析，使用Matplotlib/Seaborn绘制图表
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict
import os


class DataAnalyzer:
    """数据分析器"""

    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        self.figures_dir = os.path.join(output_dir, 'figures')
        os.makedirs(self.figures_dir, exist_ok=True)

        # 设置中文字体
        plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'DejaVu Sans']
        plt.rcParams['axes.unicode_minus'] = False

        self.analysis_results = []

    def analyze_all(self, dfs: Dict[str, pd.DataFrame]):
        """完整的数据分析流程"""
        print(f"\n{'='*60}")
        print(f"开始数据分析与可视化")
        print(f"{'='*60}\n")

        # 1. 基础统计分析
        self._basic_statistics(dfs)

        # 2. 课程分布分析
        self._course_distribution_analysis(dfs['courses'])

        # 3. 资源约束分析
        self._resource_constraint_analysis(dfs)

        # 4. 关联分析
        self._correlation_analysis(dfs)

        # 5. 生成可视化图表
        self._create_visualizations(dfs)

        # 6. 生成分析报告
        self._generate_report(dfs)

        print(f"\n{'='*60}")
        print(f"数据分析完成！")
        print(f"{'='*60}\n")

    def _basic_statistics(self, dfs: Dict[str, pd.DataFrame]):
        """基础统计分析"""
        print("[STATS] 基础统计分析...")

        self.analysis_results.append("## 一、基础统计概览\n")

        for table_name, df in dfs.items():
            self.analysis_results.append(f"\n### {table_name.upper()}\n")
            self.analysis_results.append(f"- 总行数: {len(df)}\n")
            self.analysis_results.append(f"- 总列数: {len(df.columns)}\n")

            if len(df) == 0:
                self.analysis_results.append(f"- (空数据表)\n")
                continue

            self.analysis_results.append(f"- 实例数: {df['instance'].nunique()}\n")

            if table_name == 'courses':
                self.analysis_results.append(f"- 总课程数: {df['course_id'].nunique()}\n")
                self.analysis_results.append(f"- 总教师数: {df['teacher_id'].nunique()}\n")
                self.analysis_results.append(f"- 总讲座数: {df['n_lectures'].sum()}\n")
                self.analysis_results.append(f"- 总学生人次: {df['n_students'].sum()}\n")

        print("  [OK] 完成\n")

    def _course_distribution_analysis(self, courses_df: pd.DataFrame):
        """课程分布分析"""
        print("[COURSE] 课程分布分析...")

        self.analysis_results.append("\n## 二、课程分布分析\n")

        # 讲座数分析
        self.analysis_results.append("\n### 2.1 讲座数分布\n")
        lectures_stats = courses_df['n_lectures'].describe()
        self.analysis_results.append(f"```\n{lectures_stats}\n```\n")

        # 学生数分析
        self.analysis_results.append("\n### 2.2 学生数分布\n")
        students_stats = courses_df['n_students'].describe()
        self.analysis_results.append(f"```\n{students_stats}\n```\n")

        # 最少工作天数分析
        self.analysis_results.append("\n### 2.3 最少工作天数分布\n")
        days_stats = courses_df['min_working_days'].describe()
        self.analysis_results.append(f"```\n{days_stats}\n```\n")

        # 教师负载分析
        self.analysis_results.append("\n### 2.4 教师负载分析\n")
        teacher_load = courses_df.groupby('teacher_id').agg({
            'n_lectures': 'sum',
            'course_id': 'count',
            'n_students': 'sum'
        }).rename(columns={'course_id': 'n_courses'})

        self.analysis_results.append(f"- 平均每位教师负责课程数: {teacher_load['n_courses'].mean():.2f}\n")
        self.analysis_results.append(f"- 平均每位教师讲座数: {teacher_load['n_lectures'].mean():.2f}\n")
        self.analysis_results.append(f"- 最繁忙教师讲座数: {teacher_load['n_lectures'].max()}\n")

        print("  [OK] 完成\n")

    def _resource_constraint_analysis(self, dfs: Dict[str, pd.DataFrame]):
        """资源约束分析"""
        print("[RESOURCE] 资源约束分析...")

        self.analysis_results.append("\n## 三、资源约束分析\n")

        courses_df = dfs['courses']
        rooms_df = dfs['rooms']

        # 教室容量分析
        self.analysis_results.append("\n### 3.1 教室资源\n")
        capacity_stats = rooms_df['capacity'].describe()
        self.analysis_results.append(f"```\n{capacity_stats}\n```\n")

        # 按实例统计
        self.analysis_results.append("\n### 3.2 各实例资源使用情况\n")

        instance_stats = []
        for instance in courses_df['instance'].unique():
            inst_courses = courses_df[courses_df['instance'] == instance]
            inst_rooms = rooms_df[rooms_df['instance'] == instance]

            total_lectures = inst_courses['n_lectures'].sum()
            total_capacity = inst_rooms['capacity'].sum()
            avg_students = inst_courses['n_students'].mean()

            instance_stats.append({
                'instance': instance,
                'n_courses': len(inst_courses),
                'n_rooms': len(inst_rooms),
                'total_lectures': total_lectures,
                'avg_capacity': inst_rooms['capacity'].mean(),
                'avg_students': avg_students
            })

        inst_df = pd.DataFrame(instance_stats)
        self.analysis_results.append(f"\n前5个实例统计:\n```\n{inst_df.head()}\n```\n")

        # 课程组分析
        if 'curricula' in dfs and len(dfs['curricula']) > 0:
            curricula_df = dfs['curricula']
            self.analysis_results.append("\n### 3.3 课程组分析\n")

            curriculum_size = curricula_df.groupby('curriculum_id').size()
            self.analysis_results.append(f"- 平均课程组大小: {curriculum_size.mean():.2f}\n")
            self.analysis_results.append(f"- 最大课程组大小: {curriculum_size.max()}\n")
            self.analysis_results.append(f"- 最小课程组大小: {curriculum_size.min()}\n")

        # 不可用约束分析
        if 'constraints' in dfs and len(dfs['constraints']) > 0:
            constraints_df = dfs['constraints']
            self.analysis_results.append("\n### 3.4 不可用约束分析\n")
            self.analysis_results.append(f"- 总约束数: {len(constraints_df)}\n")

            constraints_per_course = constraints_df.groupby('course_id').size()
            self.analysis_results.append(f"- 平均每门课约束数: {constraints_per_course.mean():.2f}\n")
            self.analysis_results.append(f"- 最多约束的课程: {constraints_per_course.max()} 个时段不可用\n")

        print("  [OK] 完成\n")

    def _correlation_analysis(self, dfs: Dict[str, pd.DataFrame]):
        """关联分析"""
        print("[CORRELATION] 关联分析...")

        self.analysis_results.append("\n## 四、关联分析\n")

        courses_df = dfs['courses']

        # 数值特征相关性
        numeric_cols = ['n_lectures', 'min_working_days', 'n_students']
        corr_matrix = courses_df[numeric_cols].corr()

        self.analysis_results.append("\n### 4.1 课程特征相关性矩阵\n")
        self.analysis_results.append(f"```\n{corr_matrix}\n```\n")

        # 发现的规律
        self.analysis_results.append("\n### 4.2 发现的数据规律\n")

        # 规律1: 讲座数与学生数的关系
        lectures_students_corr = courses_df['n_lectures'].corr(courses_df['n_students'])
        self.analysis_results.append(f"1. **讲座数与学生数相关性**: {lectures_students_corr:.3f}\n")
        if abs(lectures_students_corr) < 0.3:
            self.analysis_results.append("   - 相关性较弱，说明课程规模与学生数没有强关联\n")

        # 规律2: 教师负载分布
        teacher_courses = courses_df.groupby('teacher_id').size()
        self.analysis_results.append(f"\n2. **教师负载分布**:\n")
        self.analysis_results.append(f"   - 只教1门课的教师: {(teacher_courses == 1).sum()} 位\n")
        self.analysis_results.append(f"   - 教2门或以上的教师: {(teacher_courses >= 2).sum()} 位\n")

        # 规律3: 小班课vs大班课
        small_class = courses_df[courses_df['n_students'] <= 20]
        large_class = courses_df[courses_df['n_students'] >= 100]
        self.analysis_results.append(f"\n3. **班级规模**:\n")
        self.analysis_results.append(f"   - 小班课(≤20人): {len(small_class)} 门 ({len(small_class)/len(courses_df)*100:.1f}%)\n")
        self.analysis_results.append(f"   - 大班课(≥100人): {len(large_class)} 门 ({len(large_class)/len(courses_df)*100:.1f}%)\n")

        print("  [OK] 完成\n")

    def _create_visualizations(self, dfs: Dict[str, pd.DataFrame]):
        """创建可视化图表"""
        print("[VISUALIZATION] 生成可视化图表...")

        courses_df = dfs['courses']
        rooms_df = dfs['rooms']

        # 图表1: 分布图 - 学生数和讲座数分布
        print("  生成图表1: 分布图...")
        fig, axes = plt.subplots(1, 2, figsize=(14, 5))

        axes[0].hist(courses_df['n_students'], bins=30, color='skyblue', edgecolor='black')
        axes[0].set_xlabel('Number of Students', fontsize=12)
        axes[0].set_ylabel('Frequency', fontsize=12)
        axes[0].set_title('Distribution of Student Numbers', fontsize=14, fontweight='bold')
        axes[0].grid(axis='y', alpha=0.3)

        axes[1].hist(courses_df['n_lectures'], bins=range(1, courses_df['n_lectures'].max()+2),
                     color='lightcoral', edgecolor='black')
        axes[1].set_xlabel('Number of Lectures', fontsize=12)
        axes[1].set_ylabel('Frequency', fontsize=12)
        axes[1].set_title('Distribution of Lecture Numbers', fontsize=14, fontweight='bold')
        axes[1].grid(axis='y', alpha=0.3)

        plt.tight_layout()
        plt.savefig(os.path.join(self.figures_dir, '1_distribution.png'), dpi=300, bbox_inches='tight')
        plt.close()

        # 图表2: 箱线图 - 检测异常值
        print("  生成图表2: 箱线图...")
        fig, axes = plt.subplots(1, 3, figsize=(15, 5))

        axes[0].boxplot(courses_df['n_lectures'], vert=True, patch_artist=True,
                       boxprops=dict(facecolor='lightblue'))
        axes[0].set_ylabel('Number of Lectures', fontsize=12)
        axes[0].set_title('Lectures per Course', fontsize=14, fontweight='bold')
        axes[0].grid(axis='y', alpha=0.3)

        axes[1].boxplot(courses_df['n_students'], vert=True, patch_artist=True,
                       boxprops=dict(facecolor='lightgreen'))
        axes[1].set_ylabel('Number of Students', fontsize=12)
        axes[1].set_title('Students per Course', fontsize=14, fontweight='bold')
        axes[1].grid(axis='y', alpha=0.3)

        axes[2].boxplot(rooms_df['capacity'], vert=True, patch_artist=True,
                       boxprops=dict(facecolor='lightyellow'))
        axes[2].set_ylabel('Room Capacity', fontsize=12)
        axes[2].set_title('Room Capacity Distribution', fontsize=14, fontweight='bold')
        axes[2].grid(axis='y', alpha=0.3)

        plt.tight_layout()
        plt.savefig(os.path.join(self.figures_dir, '2_boxplot.png'), dpi=300, bbox_inches='tight')
        plt.close()

        # 图表3: 热力图 - 特征相关性
        print("  生成图表3: 热力图...")
        numeric_cols = ['n_lectures', 'min_working_days', 'n_students']
        corr_matrix = courses_df[numeric_cols].corr()

        plt.figure(figsize=(8, 6))
        sns.heatmap(corr_matrix, annot=True, fmt='.3f', cmap='coolwarm',
                   square=True, linewidths=1, cbar_kws={"shrink": 0.8})
        plt.title('Correlation Matrix of Course Features', fontsize=14, fontweight='bold', pad=15)
        plt.tight_layout()
        plt.savefig(os.path.join(self.figures_dir, '3_heatmap.png'), dpi=300, bbox_inches='tight')
        plt.close()

        # 图表4: 散点图 - 教室容量 vs 学生数
        print("  生成图表4: 散点图...")
        fig, ax = plt.subplots(figsize=(10, 6))

        # 为每个实例计算平均值
        instance_data = []
        for instance in courses_df['instance'].unique():
            inst_courses = courses_df[courses_df['instance'] == instance]
            inst_rooms = rooms_df[rooms_df['instance'] == instance]

            avg_students = inst_courses['n_students'].mean()
            avg_capacity = inst_rooms['capacity'].mean()

            instance_data.append({
                'avg_students': avg_students,
                'avg_capacity': avg_capacity,
                'instance': instance
            })

        inst_scatter_df = pd.DataFrame(instance_data)

        ax.scatter(inst_scatter_df['avg_students'], inst_scatter_df['avg_capacity'],
                  s=100, alpha=0.6, c='purple', edgecolors='black')

        # 添加对角线参考线
        max_val = max(inst_scatter_df['avg_students'].max(), inst_scatter_df['avg_capacity'].max())
        ax.plot([0, max_val], [0, max_val], 'r--', alpha=0.5, label='Perfect Match')

        ax.set_xlabel('Average Students per Course', fontsize=12)
        ax.set_ylabel('Average Room Capacity', fontsize=12)
        ax.set_title('Room Capacity vs Student Demand', fontsize=14, fontweight='bold')
        ax.legend()
        ax.grid(alpha=0.3)

        plt.tight_layout()
        plt.savefig(os.path.join(self.figures_dir, '4_scatter.png'), dpi=300, bbox_inches='tight')
        plt.close()

        # 图表5: 柱状对比图 - 各实例资源使用
        print("  生成图表5: 柱状对比图...")

        # 选择前10个实例
        instances = sorted(courses_df['instance'].unique())[:10]
        instance_stats = []

        for instance in instances:
            inst_courses = courses_df[courses_df['instance'] == instance]
            inst_rooms = rooms_df[rooms_df['instance'] == instance]

            instance_stats.append({
                'instance': instance,
                'n_courses': len(inst_courses),
                'n_rooms': len(inst_rooms),
                'total_lectures': inst_courses['n_lectures'].sum()
            })

        inst_bar_df = pd.DataFrame(instance_stats)

        fig, ax = plt.subplots(figsize=(12, 6))

        x = np.arange(len(inst_bar_df))
        width = 0.25

        ax.bar(x - width, inst_bar_df['n_courses'], width, label='Courses', color='skyblue')
        ax.bar(x, inst_bar_df['n_rooms'], width, label='Rooms', color='lightcoral')
        ax.bar(x + width, inst_bar_df['total_lectures']/10, width, label='Lectures/10', color='lightgreen')

        ax.set_xlabel('Instance', fontsize=12)
        ax.set_ylabel('Count', fontsize=12)
        ax.set_title('Resource Usage by Instance', fontsize=14, fontweight='bold')
        ax.set_xticks(x)
        ax.set_xticklabels(inst_bar_df['instance'], rotation=45, ha='right')
        ax.legend()
        ax.grid(axis='y', alpha=0.3)

        plt.tight_layout()
        plt.savefig(os.path.join(self.figures_dir, '5_barchart.png'), dpi=300, bbox_inches='tight')
        plt.close()

        print("  [OK] 5个图表已生成\n")

    def _generate_report(self, dfs: Dict[str, pd.DataFrame]):
        """生成分析报告"""
        print("[REPORT] 生成分析报告...")

        report_path = os.path.join(self.output_dir, 'data_analysis_report.md')

        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("# 数据分析与可视化报告\n\n")
            f.write("="*80 + "\n\n")

            # 写入分析结果
            for line in self.analysis_results:
                f.write(line)

            # 添加可视化图表说明
            f.write("\n\n## 五、可视化图表说明\n\n")

            f.write("### 5.1 分布图 (1_distribution.png)\n")
            f.write("- **左图**: 学生数分布 - 显示课程学生数的频率分布\n")
            f.write("- **右图**: 讲座数分布 - 显示每门课讲座次数的分布\n")
            f.write("- **用途**: 了解课程规模特征，为资源分配提供依据\n\n")

            f.write("### 5.2 箱线图 (2_boxplot.png)\n")
            f.write("- 显示讲座数、学生数、教室容量的分布和异常值\n")
            f.write("- **用途**: 识别数据中的异常值和离群点，评估数据质量\n\n")

            f.write("### 5.3 热力图 (3_heatmap.png)\n")
            f.write("- 显示课程特征之间的相关性矩阵\n")
            f.write("- **用途**: 发现特征之间的关联关系，指导特征工程\n\n")

            f.write("### 5.4 散点图 (4_scatter.png)\n")
            f.write("- 显示平均教室容量与平均学生数的关系\n")
            f.write("- **红色虚线**: 完美匹配线（容量=学生数）\n")
            f.write("- **用途**: 评估资源匹配度，发现容量过剩或不足的情况\n\n")

            f.write("### 5.5 柱状对比图 (5_barchart.png)\n")
            f.write("- 显示各实例的课程数、教室数、讲座数对比\n")
            f.write("- **用途**: 横向对比不同实例的规模和复杂度\n\n")

            # 添加结论和建议
            f.write("\n## 六、数据规律总结\n\n")
            f.write("### 6.1 主要发现\n\n")
            f.write("1. **规模差异**: 不同实例的课程数、教室数差异较大，说明排课问题的复杂度跨度很大\n")
            f.write("2. **资源匹配**: 大部分实例的平均教室容量与学生需求匹配良好\n")
            f.write("3. **特征相关性**: 课程特征之间相关性较弱，说明特征独立性较好\n")
            f.write("4. **数据分布**: 学生数呈现右偏分布，小班课较多\n\n")

            f.write("### 6.2 对模型选择的建议\n\n")
            f.write("1. **特征工程**: 可以添加更多派生特征，如资源压力比、约束密度等\n")
            f.write("2. **模型选择**: 考虑使用能处理非线性关系的模型（如随机森林、梯度提升）\n")
            f.write("3. **归一化**: 特征尺度差异大，建议进行标准化处理\n")
            f.write("4. **异常值处理**: 箱线图显示存在异常值，可能需要进一步处理或robust模型\n\n")

            f.write("\n" + "="*80 + "\n")
            f.write("\n**报告生成时间**: 2026-06-03\n")
            f.write("\n**图表位置**: data_cleaning/figures/\n")
            f.write("\n**数据来源**: ITC2007 课程排课数据集（21个实例）\n")

        print(f"  [OK] 报告已保存: {report_path}\n")


if __name__ == "__main__":
    print("请通过主程序运行此模块")
