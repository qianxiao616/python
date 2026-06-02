"""
AIcourse - 课程排课难度预测系统
主程序

使用方法:
    python main.py --generate-data    # 生成数据集
    python main.py --train           # 训练模型
    python main.py --all             # 完整流程
"""
import argparse
import sys
from pathlib import Path
import pandas as pd
import numpy as np

# 导入自定义模块
from src.feature_extractor import FeatureExtractor
from src.label_generator import LabelGenerator
from src.model_trainer import ModelTrainer
from src.visualizer import Visualizer


def generate_dataset(pycourse_data_dir: str, output_file: str, time_limit: int = 30):
    """
    生成数据集: 提取特征 + 生成标签

    Args:
        pycourse_data_dir: pycourse数据目录
        output_file: 输出CSV文件路径
        time_limit: 求解器时间限制
    """
    print("\n" + "="*60)
    print("步骤1: 生成数据集")
    print("="*60)

    data_dir = Path(pycourse_data_dir)
    if not data_dir.exists():
        print(f"错误: 数据目录不存在: {data_dir}")
        return False

    # 获取所有.ctt文件（排除toy测试文件）
    ctt_files = sorted([
        str(f) for f in data_dir.glob('*.ctt')
        if 'toy' not in f.stem.lower()
    ])

    if not ctt_files:
        print(f"错误: 在 {data_dir} 中没有找到.ctt文件")
        return False

    print(f"\n找到 {len(ctt_files)} 个.ctt文件")

    # 提取特征
    print("\n[1/2] 提取特征...")
    extractor = FeatureExtractor()
    features_list = extractor.extract_batch(ctt_files)

    if not features_list:
        print("错误: 特征提取失败")
        return False

    # 生成标签
    print(f"\n[2/2] 生成难度标签 (时间限制: {time_limit}秒/实例)...")
    generator = LabelGenerator(time_limit=time_limit, verbose=False)
    labels_list = generator.generate_batch(ctt_files)

    if not labels_list:
        print("错误: 标签生成失败")
        return False

    # 打印摘要
    generator.print_summary(labels_list)

    # 合并特征和标签
    print("\n合并数据...")
    features_df = pd.DataFrame(features_list)
    labels_df = pd.DataFrame(labels_list)

    # 按instance_id合并
    dataset = pd.merge(features_df, labels_df, on='instance_id', how='inner')

    # 保存
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    dataset.to_csv(output_path, index=False)

    print(f"\n[OK] Dataset saved: {output_path}")
    print(f"  - Samples: {len(dataset)}")
    print(f"  - Features: {len(extractor.get_feature_names())}")
    print(f"  - Columns: {len(dataset.columns)}")

    return True


def train_models(dataset_file: str, results_dir: str):
    """
    训练和评估模型

    Args:
        dataset_file: 数据集文件路径
        results_dir: 结果输出目录
    """
    print("\n" + "="*60)
    print("步骤2: 训练模型")
    print("="*60)

    # 读取数据
    dataset_path = Path(dataset_file)
    if not dataset_path.exists():
        print(f"错误: 数据集文件不存在: {dataset_path}")
        return False

    df = pd.read_csv(dataset_path)
    print(f"\n加载数据集: {len(df)} 个样本")

    # 准备特征和标签
    extractor = FeatureExtractor()
    feature_cols = extractor.get_feature_names()

    # 检查所有特征列是否存在
    missing_cols = [col for col in feature_cols if col not in df.columns]
    if missing_cols:
        print(f"警告: 缺少特征列: {missing_cols}")
        feature_cols = [col for col in feature_cols if col in df.columns]

    X = df[feature_cols]
    y = df['difficulty']

    print(f"特征数: {len(feature_cols)}")
    print(f"目标变量: difficulty (软成本)")

    # 数据统计
    print(f"\n目标变量统计:")
    print(f"  最小值: {y.min():.0f}")
    print(f"  最大值: {y.max():.0f}")
    print(f"  平均值: {y.mean():.2f}")
    print(f"  标准差: {y.std():.2f}")

    # 训练模型
    trainer = ModelTrainer(random_state=42)
    trainer.prepare_models()
    results = trainer.train_with_loocv(X, y)

    # 打印对比结果
    comparison_df = trainer.print_comparison()

    # 保存结果
    results_path = Path(results_dir)
    results_path.mkdir(parents=True, exist_ok=True)
    trainer.save_results(results_path / 'model_comparison.csv')

    # 训练最终模型（使用全部数据）
    best_model_name = comparison_df.iloc[0]['Model']
    trainer.train_final_model(X, y, model_name=best_model_name)

    # 获取特征重要性（针对随机森林）
    if 'Random Forest' in trainer.models:
        print("\nGetting feature importance...")
        importance_df = trainer.get_feature_importance('Random Forest', feature_cols)
        if importance_df is not None:
            importance_df.to_csv(results_path / 'feature_importance.csv', index=False)
            print(f"[OK] Feature importance saved")

    # 可视化
    print("\nGenerating visualization plots...")
    visualizer = Visualizer(results_path / 'figures')

    # 模型对比图
    visualizer.plot_model_comparison(results)

    # 预测vs实际图
    visualizer.plot_predictions(results)

    # 难度分布图
    visualizer.plot_difficulty_distribution(df)

    # 残差分析图
    visualizer.plot_residuals(results, best_model_name)

    # 特征重要性图
    if importance_df is not None:
        visualizer.plot_feature_importance(importance_df)

    # 相关性矩阵
    visualizer.plot_correlation_matrix(df, feature_cols[:10])  # 只显示前10个特征

    print("\n" + "="*60)
    print("Training completed!")
    print("="*60)
    print(f"\nResults saved in: {results_path}")

    return True


def main():
    """主程序"""
    parser = argparse.ArgumentParser(
        description='AIcourse - 课程排课难度预测系统',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python main.py --generate-data          # 生成数据集
  python main.py --train                  # 训练模型
  python main.py --all                    # 运行完整流程
  python main.py --all --time-limit 60    # 使用更长的求解时间
        """
    )

    parser.add_argument('--generate-data', action='store_true',
                       help='生成数据集（特征提取+标签生成）')
    parser.add_argument('--train', action='store_true',
                       help='训练模型')
    parser.add_argument('--all', action='store_true',
                       help='运行完整流程（生成数据+训练）')
    parser.add_argument('--time-limit', type=int, default=30,
                       help='求解器时间限制（秒，默认30）')
    parser.add_argument('--pycourse-dir', type=str,
                       default='../pycourse/data',
                       help='pycourse数据目录路径')
    parser.add_argument('--output', type=str,
                       default='data/features.csv',
                       help='数据集输出文件路径')
    parser.add_argument('--results-dir', type=str,
                       default='results',
                       help='结果输出目录')

    args = parser.parse_args()

    # 转换为绝对路径
    script_dir = Path(__file__).parent
    pycourse_dir = (script_dir / args.pycourse_dir).resolve()
    output_file = (script_dir / args.output).resolve()
    results_dir = (script_dir / args.results_dir).resolve()

    print("\n" + "="*60)
    print("AIcourse - 课程排课难度预测系统")
    print("="*60)
    print(f"\nPycourse数据目录: {pycourse_dir}")
    print(f"数据集输出: {output_file}")
    print(f"结果目录: {results_dir}")

    # 执行操作
    if args.all:
        # 完整流程
        print("\n执行完整流程...")
        if not generate_dataset(str(pycourse_dir), str(output_file), args.time_limit):
            sys.exit(1)
        if not train_models(str(output_file), str(results_dir)):
            sys.exit(1)

    elif args.generate_data:
        # 只生成数据
        if not generate_dataset(str(pycourse_dir), str(output_file), args.time_limit):
            sys.exit(1)

    elif args.train:
        # 只训练模型
        if not train_models(str(output_file), str(results_dir)):
            sys.exit(1)

    else:
        # 没有指定操作
        parser.print_help()
        print("\n请指定操作: --generate-data, --train, 或 --all")
        sys.exit(1)

    print("\n" + "="*60)
    print("程序执行完成！")
    print("="*60)


if __name__ == '__main__':
    main()
