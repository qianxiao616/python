"""
可视化模块 - Visualizer

生成各种图表用于结果展示和分析。
"""
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']  # 用于显示中文
plt.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号

# 设置样式
sns.set_style("whitegrid")
sns.set_palette("husl")


class Visualizer:
    """可视化器"""

    def __init__(self, output_dir: str):
        """
        初始化可视化器

        Args:
            output_dir: 输出目录
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def plot_model_comparison(self, results: Dict, save_name: str = 'model_comparison.png'):
        """
        绘制模型性能对比图

        Args:
            results: 模型结果字典
            save_name: 保存文件名
        """
        # 准备数据
        models = list(results.keys())
        rmse_values = [results[m]['RMSE'] for m in models]
        mae_values = [results[m]['MAE'] for m in models]
        r2_values = [results[m]['R2'] for m in models]

        # 创建子图
        fig, axes = plt.subplots(1, 3, figsize=(15, 4))

        # RMSE对比
        axes[0].bar(models, rmse_values, color='skyblue')
        axes[0].set_title('RMSE Comparison', fontsize=14, fontweight='bold')
        axes[0].set_ylabel('RMSE')
        axes[0].tick_params(axis='x', rotation=45)
        for i, v in enumerate(rmse_values):
            axes[0].text(i, v, f'{v:.1f}', ha='center', va='bottom')

        # MAE对比
        axes[1].bar(models, mae_values, color='lightcoral')
        axes[1].set_title('MAE Comparison', fontsize=14, fontweight='bold')
        axes[1].set_ylabel('MAE')
        axes[1].tick_params(axis='x', rotation=45)
        for i, v in enumerate(mae_values):
            axes[1].text(i, v, f'{v:.1f}', ha='center', va='bottom')

        # R2对比
        axes[2].bar(models, r2_values, color='lightgreen')
        axes[2].set_title('R2 Comparison', fontsize=14, fontweight='bold')
        axes[2].set_ylabel('R2 Score')
        axes[2].tick_params(axis='x', rotation=45)
        axes[2].axhline(y=0, color='gray', linestyle='--', linewidth=0.8)
        for i, v in enumerate(r2_values):
            axes[2].text(i, v, f'{v:.3f}', ha='center', va='bottom')

        plt.tight_layout()
        save_path = self.output_dir / save_name
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"[OK] Model comparison plot saved: {save_path}")
        plt.close()

    def plot_predictions(self, results: Dict, save_name: str = 'predictions.png'):
        """
        绘制预测vs实际值散点图（所有模型）

        Args:
            results: 模型结果字典
            save_name: 保存文件名
        """
        n_models = len(results)
        n_cols = 3
        n_rows = (n_models + n_cols - 1) // n_cols

        fig, axes = plt.subplots(n_rows, n_cols, figsize=(15, 5*n_rows))
        axes = axes.flatten() if n_models > 1 else [axes]

        for idx, (model_name, result) in enumerate(results.items()):
            y_true = result['y_true']
            y_pred = result['y_pred']
            r2 = result['R2']
            rmse = result['RMSE']

            ax = axes[idx]

            # 散点图
            ax.scatter(y_true, y_pred, alpha=0.6, s=60, edgecolors='black', linewidth=0.5)

            # 对角线（完美预测线）
            min_val = min(y_true.min(), y_pred.min())
            max_val = max(y_true.max(), y_pred.max())
            ax.plot([min_val, max_val], [min_val, max_val], 'r--', linewidth=2, label='Perfect Prediction')

            ax.set_xlabel('Actual Difficulty', fontsize=11)
            ax.set_ylabel('Predicted Difficulty', fontsize=11)
            ax.set_title(f'{model_name}\nR2={r2:.3f}, RMSE={rmse:.1f}', fontsize=12, fontweight='bold')
            ax.legend()
            ax.grid(True, alpha=0.3)

        # 隐藏多余的子图
        for idx in range(n_models, len(axes)):
            axes[idx].axis('off')

        plt.tight_layout()
        save_path = self.output_dir / save_name
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"[OK] Predictions plot saved: {save_path}")
        plt.close()

    def plot_feature_importance(self, importance_df: pd.DataFrame,
                                 save_name: str = 'feature_importance.png',
                                 top_n: int = 15):
        """
        绘制特征重要性图

        Args:
            importance_df: 特征重要性DataFrame
            save_name: 保存文件名
            top_n: 显示前N个特征
        """
        if importance_df is None or len(importance_df) == 0:
            print("没有特征重要性数据")
            return

        # 取前N个
        df_plot = importance_df.head(top_n)

        plt.figure(figsize=(10, 8))
        plt.barh(df_plot['feature'], df_plot['importance'], color='steelblue')
        plt.xlabel('Importance', fontsize=12)
        plt.ylabel('Feature', fontsize=12)
        plt.title('Feature Importance (Random Forest)', fontsize=14, fontweight='bold')
        plt.gca().invert_yaxis()  # 最重要的在上面

        # 添加数值标签
        for i, v in enumerate(df_plot['importance']):
            plt.text(v, i, f' {v:.4f}', va='center')

        plt.tight_layout()
        save_path = self.output_dir / save_name
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"[OK] Feature importance plot saved: {save_path}")
        plt.close()

    def plot_difficulty_distribution(self, df: pd.DataFrame,
                                     save_name: str = 'difficulty_distribution.png'):
        """
        绘制难度分布图

        Args:
            df: 包含difficulty列的DataFrame
            save_name: 保存文件名
        """
        fig, axes = plt.subplots(1, 2, figsize=(12, 4))

        # 直方图
        axes[0].hist(df['difficulty'], bins=15, color='skyblue', edgecolor='black', alpha=0.7)
        axes[0].set_xlabel('Difficulty (Soft Cost)', fontsize=11)
        axes[0].set_ylabel('Frequency', fontsize=11)
        axes[0].set_title('Difficulty Distribution', fontsize=13, fontweight='bold')
        axes[0].grid(True, alpha=0.3)

        # 箱线图
        axes[1].boxplot(df['difficulty'], vert=True, patch_artist=True,
                       boxprops=dict(facecolor='lightcoral', alpha=0.7))
        axes[1].set_ylabel('Difficulty (Soft Cost)', fontsize=11)
        axes[1].set_title('Difficulty Box Plot', fontsize=13, fontweight='bold')
        axes[1].grid(True, alpha=0.3)

        plt.tight_layout()
        save_path = self.output_dir / save_name
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"[OK] Difficulty distribution plot saved: {save_path}")
        plt.close()

    def plot_residuals(self, results: Dict, best_model_name: str,
                       save_name: str = 'residuals.png'):
        """
        绘制残差分析图

        Args:
            results: 模型结果字典
            best_model_name: 最佳模型名称
            save_name: 保存文件名
        """
        if best_model_name not in results:
            print(f"模型 {best_model_name} 不存在")
            return

        result = results[best_model_name]
        y_true = result['y_true']
        y_pred = result['y_pred']
        residuals = y_true - y_pred

        fig, axes = plt.subplots(1, 2, figsize=(12, 4))

        # 残差散点图
        axes[0].scatter(y_pred, residuals, alpha=0.6, s=60, edgecolors='black', linewidth=0.5)
        axes[0].axhline(y=0, color='red', linestyle='--', linewidth=2)
        axes[0].set_xlabel('Predicted Difficulty', fontsize=11)
        axes[0].set_ylabel('Residuals', fontsize=11)
        axes[0].set_title(f'Residual Plot - {best_model_name}', fontsize=13, fontweight='bold')
        axes[0].grid(True, alpha=0.3)

        # 残差直方图
        axes[1].hist(residuals, bins=10, color='lightgreen', edgecolor='black', alpha=0.7)
        axes[1].set_xlabel('Residuals', fontsize=11)
        axes[1].set_ylabel('Frequency', fontsize=11)
        axes[1].set_title('Residuals Distribution', fontsize=13, fontweight='bold')
        axes[1].axvline(x=0, color='red', linestyle='--', linewidth=2)
        axes[1].grid(True, alpha=0.3)

        plt.tight_layout()
        save_path = self.output_dir / save_name
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"[OK] Residuals plot saved: {save_path}")
        plt.close()

    def plot_correlation_matrix(self, df: pd.DataFrame, feature_cols: List[str],
                                save_name: str = 'correlation_matrix.png'):
        """
        绘制特征相关性矩阵

        Args:
            df: 数据DataFrame
            feature_cols: 特征列名列表
            save_name: 保存文件名
        """
        # 计算相关性矩阵
        corr = df[feature_cols + ['difficulty']].corr()

        plt.figure(figsize=(12, 10))
        sns.heatmap(corr, annot=False, cmap='coolwarm', center=0,
                   square=True, linewidths=0.5, cbar_kws={"shrink": 0.8})
        plt.title('Feature Correlation Matrix', fontsize=14, fontweight='bold')
        plt.tight_layout()

        save_path = self.output_dir / save_name
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"[OK] Correlation matrix saved: {save_path}")
        plt.close()


if __name__ == '__main__':
    print("可视化模块加载成功")
