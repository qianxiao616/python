"""
数据污染与清洗主程序
完成任务一和任务二的完整流程
"""

import sys
import os

# 添加src到路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from ctt_to_csv import convert_all_ctt_to_csv
from data_polluter import DataPolluter
from data_cleaner import DataCleaner
from data_analyzer import DataAnalyzer


def main():
    """主流程"""
    print("\n" + "="*80)
    print("课程排课数据污染与清洗项目")
    print("="*80 + "\n")

    # 路径配置
    ctt_dir = "data"
    output_dir = "data_cleaning"

    # ========================================
    # 步骤1: 将.ctt文件转换为干净的CSV
    # ========================================
    print("\n【步骤1】转换.ctt文件为CSV...")
    print("-"*80)

    clean_dfs = convert_all_ctt_to_csv(ctt_dir, "clean")

    # 保存干净的CSV（作为参考）
    for name, df in clean_dfs.items():
        output_path = os.path.join(output_dir, f"clean_{name}.csv")
        df.to_csv(output_path, index=False)
        print(f"[OK] 保存干净数据: {output_path}")

    # ========================================
    # 步骤2: 数据污染
    # ========================================
    print("\n【步骤2】数据污染...")
    print("-"*80)

    polluter = DataPolluter(pollution_rate=0.18)
    dirty_dfs = polluter.pollute_all(clean_dfs)

    # 保存污染后的CSV
    for name, df in dirty_dfs.items():
        output_path = os.path.join(output_dir, "dirty", f"dirty_{name}.csv")
        df.to_csv(output_path, index=False)
        print(f"[OK] 保存污染数据: {output_path}")

    # 保存污染日志
    polluter.save_pollution_log(os.path.join(output_dir, "pollution_log.txt"))

    # ========================================
    # 步骤3: 数据清洗
    # ========================================
    print("\n【步骤3】数据清洗...")
    print("-"*80)

    cleaner = DataCleaner()
    cleaned_dfs = cleaner.clean_all(dirty_dfs)

    # 保存清洗后的CSV
    for name, df in cleaned_dfs.items():
        output_path = os.path.join(output_dir, "cleaned", f"cleaned_{name}.csv")
        df.to_csv(output_path, index=False)
        print(f"[OK] 保存清洗数据: {output_path}")

    # 生成清洗报告
    cleaner.generate_report(
        os.path.join(output_dir, "cleaning_report.txt"),
        dirty_dfs,
        cleaned_dfs
    )

    # ========================================
    # 步骤4: 数据分析与可视化
    # ========================================
    print("\n【步骤4】数据分析与可视化...")
    print("-"*80)

    analyzer = DataAnalyzer(output_dir)
    analyzer.analyze_all(cleaned_dfs)

    # ========================================
    # 完成
    # ========================================
    print("\n" + "="*80)
    print("[SUCCESS] 所有任务完成！")
    print("="*80)

    print("\n[FILES] 输出文件:")
    print(f"  干净数据: {output_dir}/clean_*.csv")
    print(f"  污染数据: {output_dir}/dirty/dirty_*.csv")
    print(f"  污染日志: {output_dir}/pollution_log.txt")
    print(f"  清洗数据: {output_dir}/cleaned/cleaned_*.csv")
    print(f"  清洗报告: {output_dir}/cleaning_report.txt")
    print(f"  分析报告: {output_dir}/data_analysis_report.md")
    print(f"  可视化图表: {output_dir}/figures/ (5张图)")

    print("\n[DONE] 任务一完成: 数据污染与清洗")
    print("[DONE] 任务二完成: 数据分析与可视化")
    print("\n")


if __name__ == "__main__":
    main()
