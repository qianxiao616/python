"""
模型训练模块 - Model Trainer

使用多种回归模型预测排课难度，并进行对比实验。
采用留一法交叉验证（LOOCV）适应小样本场景。
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple
from pathlib import Path

from sklearn.model_selection import LeaveOneOut, cross_val_score
from sklearn.linear_model import LinearRegression, Ridge, Lasso
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.svm import SVR
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import warnings
warnings.filterwarnings('ignore')

try:
    from xgboost import XGBRegressor
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False
    print("注意: XGBoost未安装，将跳过XGBoost模型")


class ModelTrainer:
    """模型训练器"""

    def __init__(self, random_state: int = 42):
        """
        初始化训练器

        Args:
            random_state: 随机种子
        """
        self.random_state = random_state
        self.scaler = StandardScaler()
        self.models = {}
        self.results = {}

    def prepare_models(self) -> Dict:
        """
        准备要对比的模型

        Returns:
            模型字典
        """
        models = {
            'Linear Regression': LinearRegression(),
            'Ridge Regression': Ridge(alpha=1.0, random_state=self.random_state),
            'Lasso Regression': Lasso(alpha=1.0, random_state=self.random_state),
            'Random Forest': RandomForestRegressor(
                n_estimators=100,
                max_depth=5,
                min_samples_split=3,
                random_state=self.random_state
            ),
            'Gradient Boosting': GradientBoostingRegressor(
                n_estimators=100,
                max_depth=3,
                learning_rate=0.1,
                random_state=self.random_state
            ),
            'SVR': SVR(kernel='rbf', C=100, gamma='scale'),
        }

        if XGBOOST_AVAILABLE:
            models['XGBoost'] = XGBRegressor(
                n_estimators=100,
                max_depth=3,
                learning_rate=0.1,
                random_state=self.random_state
            )

        self.models = models
        return models

    def train_with_loocv(self, X: pd.DataFrame, y: pd.Series) -> Dict:
        """
        使用留一法交叉验证训练和评估所有模型

        Args:
            X: 特征矩阵
            y: 目标向量

        Returns:
            结果字典
        """
        if len(self.models) == 0:
            self.prepare_models()

        print("\n" + "="*60)
        print("开始模型训练 (留一法交叉验证)")
        print("="*60)

        loo = LeaveOneOut()
        results = {}

        for model_name, model in self.models.items():
            print(f"\n训练模型: {model_name}")

            y_true = []
            y_pred = []

            # 留一法交叉验证
            for train_idx, test_idx in loo.split(X):
                X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
                y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]

                # 标准化特征
                X_train_scaled = self.scaler.fit_transform(X_train)
                X_test_scaled = self.scaler.transform(X_test)

                # 训练和预测
                model.fit(X_train_scaled, y_train)
                pred = model.predict(X_test_scaled)[0]

                y_true.append(y_test.iloc[0])
                y_pred.append(pred)

            # 计算评估指标
            y_true = np.array(y_true)
            y_pred = np.array(y_pred)

            rmse = np.sqrt(mean_squared_error(y_true, y_pred))
            mae = mean_absolute_error(y_true, y_pred)
            r2 = r2_score(y_true, y_pred)

            # 计算MAPE (平均绝对百分比误差)
            mape = np.mean(np.abs((y_true - y_pred) / y_true)) * 100

            results[model_name] = {
                'RMSE': rmse,
                'MAE': mae,
                'R2': r2,
                'MAPE': mape,
                'y_true': y_true,
                'y_pred': y_pred
            }

            print(f"  RMSE: {rmse:.2f}")
            print(f"  MAE:  {mae:.2f}")
            print(f"  R2:   {r2:.3f}")
            print(f"  MAPE: {mape:.2f}%")

        self.results = results
        return results

    def train_final_model(self, X: pd.DataFrame, y: pd.Series, model_name: str = 'Random Forest'):
        """
        在全部数据上训练最终模型

        Args:
            X: 特征矩阵
            y: 目标向量
            model_name: 要训练的模型名称
        """
        if model_name not in self.models:
            raise ValueError(f"模型 {model_name} 不存在")

        print(f"\n在全部数据上训练最终模型: {model_name}")

        # 标准化
        X_scaled = self.scaler.fit_transform(X)

        # 训练
        model = self.models[model_name]
        model.fit(X_scaled, y)

        print(f"[OK] Final model training completed")

        return model

    def get_feature_importance(self, model_name: str, feature_names: List[str]) -> pd.DataFrame:
        """
        获取特征重要性（仅适用于树模型）

        Args:
            model_name: 模型名称
            feature_names: 特征名称列表

        Returns:
            特征重要性DataFrame
        """
        if model_name not in self.models:
            raise ValueError(f"模型 {model_name} 不存在")

        model = self.models[model_name]

        # 检查模型是否有feature_importances_属性
        if hasattr(model, 'feature_importances_'):
            importances = model.feature_importances_
            df = pd.DataFrame({
                'feature': feature_names,
                'importance': importances
            }).sort_values('importance', ascending=False)
            return df
        else:
            print(f"模型 {model_name} 不支持特征重要性")
            return None

    def print_comparison(self):
        """打印模型对比结果"""
        if not self.results:
            print("没有可用的结果")
            return

        print("\n" + "="*60)
        print("模型性能对比")
        print("="*60)

        # 创建对比表
        comparison = []
        for model_name, metrics in self.results.items():
            comparison.append({
                'Model': model_name,
                'RMSE': metrics['RMSE'],
                'MAE': metrics['MAE'],
                'R2': metrics['R2'],
                'MAPE(%)': metrics['MAPE']
            })

        df = pd.DataFrame(comparison)
        df = df.sort_values('RMSE')  # 按RMSE排序

        print("\n", df.to_string(index=False))

        # 找出最佳模型
        best_model = df.iloc[0]['Model']
        print(f"\n最佳模型 (RMSE最低): {best_model}")
        print("="*60)

        return df

    def save_results(self, output_path: str):
        """
        保存结果到CSV

        Args:
            output_path: 输出文件路径
        """
        comparison = []
        for model_name, metrics in self.results.items():
            comparison.append({
                'Model': model_name,
                'RMSE': metrics['RMSE'],
                'MAE': metrics['MAE'],
                'R2': metrics['R2'],
                'MAPE': metrics['MAPE']
            })

        df = pd.DataFrame(comparison)
        df = df.sort_values('RMSE')
        df.to_csv(output_path, index=False)
        print(f"\nResults saved to: {output_path}")


if __name__ == '__main__':
    # 测试代码
    print("模型训练模块加载成功")
    print(f"可用模型数量: {len(ModelTrainer().prepare_models())}")
