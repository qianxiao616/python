# AIcourse - 课程排课难度预测系统

基于机器学习的 ITC2007 课程排课问题难度预测系统。

## 项目简介

本项目将课程排课问题转化为一个回归任务：不直接求解排课，而是预测排课问题的"难度"。具体做法是从 ITC2007 标准数据集（`.ctt` 文件）中提取问题特征，使用自主实现的贪心求解器求解每个实例，并将求解得到的软约束成本作为难度标签，进而训练多种回归模型预测新实例的排课难度。

项目包含两条完整的流水线：

1. **数据污染与清洗流水线**（`data_cleaning_main.py`）——演示从原始数据到清洗、分析、可视化的完整数据处理流程。
2. **难度预测流水线**（`main.py`）——特征提取、标签生成、模型训练与评估。

## 核心流程

```
.ctt 文件
   ├─[数据流水线]→ CSV 转换 → 数据污染 → 数据清洗 → 分析与可视化
   └─[预测流水线]→ 特征提取 → 贪心求解 → 软成本标签 → 模型训练 → 难度预测
```

## 项目结构

```
AIcourse/
├── src/                          # 源代码
│   ├── ctt_parser.py             # CTT 文件解析器（独立实现）
│   ├── greedy_solver.py          # 贪心排课求解器（独立实现）
│   ├── constraint_evaluator.py   # 硬/软约束评估器
│   ├── feature_extractor.py      # 特征提取（20 个特征）
│   ├── label_generator.py        # 标签生成（基于求解器软成本）
│   ├── model_trainer.py          # 模型训练与 LOOCV 评估
│   ├── visualizer.py             # 预测结果可视化
│   ├── ctt_to_csv.py             # .ctt → CSV 转换
│   ├── data_polluter.py          # 数据污染（注入缺失/异常/重复/格式错误）
│   ├── data_cleaner.py           # 数据清洗
│   └── data_analyzer.py          # 数据分析与可视化
│
├── data/                         # 数据目录
│   ├── comp01.ctt ~ comp21.ctt   # 21 个 ITC2007 排课实例
│   └── features.csv              # 提取的特征 + 标签数据集
│
├── data_cleaning/                # 数据处理流水线产物
│   ├── clean_*.csv               # 由 .ctt 转换得到的干净 CSV
│   ├── dirty/                    # 污染后的数据
│   ├── cleaned/                  # 清洗后的数据
│   ├── figures/                  # 数据分析图表（5 张）
│   ├── pollution_log.txt         # 污染日志
│   ├── cleaning_report.txt       # 清洗报告
│   └── data_analysis_report.md   # 数据分析报告
│
├── results/                      # 预测流水线结果
│   ├── model_comparison.csv      # 模型性能对比表
│   ├── feature_importance.csv    # 特征重要性排序
│   └── figures/                  # 可视化图表（6 张）
│
├── models/                       # 保存的模型
├── main.py                       # 预测流水线入口
├── data_cleaning_main.py         # 数据处理流水线入口
├── requirements.txt              # 依赖列表
└── README.md                     # 本文件
```

## 特征说明

本项目从每个排课实例提取 **20 个数值特征**，分为四类：

### 1. 规模类特征 (5 个)
- `n_courses`：课程数量
- `total_lectures`：讲座总次数
- `n_rooms`：教室数量
- `n_curricula`：课程组数量
- `n_unavailability_constraints`：不可用约束总数

### 2. 约束紧密度特征 (6 个)
- `avg_curriculum_size`：平均课程组大小
- `max_curriculum_size`：最大课程组大小
- `constraint_density`：课程组冲突密度
- `teacher_conflict_density`：教师冲突密度
- `avg_unavailable_per_course`：平均每门课不可用时段数
- `courses_in_curricula_ratio`：被课程组覆盖的课程比例

### 3. 资源匹配特征 (6 个)
- `room_capacity_mean`：教室平均容量
- `room_capacity_std`：教室容量标准差
- `student_count_mean`：课程平均学生数
- `student_count_std`：学生数标准差
- `avg_students_per_room_capacity`：学生与教室容量比
- `room_utilization_pressure`：时段利用压力

### 4. 时间分布特征 (3 个)
- `avg_min_working_days`：课程平均最少工作天数
- `lectures_per_timeslot_ratio`：讲座与时段比
- `time_slack`：时间松弛度

## 标签生成

难度标签由贪心求解器自动生成，而非人工标注：

1. 用贪心求解器求解每个 `.ctt` 实例
2. 用约束评估器计算软约束成本（教室容量、最少工作天数、课程组紧凑性、教室稳定性）的加权和
3. 将软成本作为连续的难度标签（`difficulty`），同时记录可行性、硬约束违规数、求解时间等元信息

## 模型与评估

训练并对比以下回归模型：

1. **线性回归** (Linear Regression) — 基线
2. **岭回归** (Ridge) — L2 正则化
3. **Lasso 回归** (Lasso) — L1 正则化
4. **随机森林** (Random Forest)
5. **梯度提升** (Gradient Boosting)
6. **支持向量回归** (SVR)

> XGBoost 为可选模型，未安装时自动跳过。

**评估方法**：留一法交叉验证 (LOOCV)，适合 21 个样本的小数据集。
**评估指标**：RMSE、MAE、R²、MAPE。

## 实验结果

| 排名 | 模型 | RMSE | MAE | R² | MAPE(%) |
|------|------|------|-----|-----|---------|
| 1 | Lasso Regression | 121.66 | 81.38 | 0.883 | 21.90 |
| 2 | Ridge Regression | 159.78 | 105.41 | 0.798 | 29.89 |
| 3 | Gradient Boosting | 211.03 | 127.15 | 0.648 | 28.22 |
| 4 | Random Forest | 277.06 | 163.57 | 0.393 | 37.98 |
| 5 | SVR | 371.67 | 194.43 | -0.093 | 44.95 |
| 6 | Linear Regression | 1210.20 | 680.58 | -10.587 | 182.77 |

**最佳模型**：Lasso Regression（R² = 0.883，RMSE = 121.66）。结果表明，在小样本场景下正则化对防止过拟合至关重要，Lasso 的特征选择能力使其在 20 维特征下表现最优。

## 使用方法

### 1. 安装依赖

```bash
cd AIcourse
pip install -r requirements.txt
```

### 2. 数据处理流水线（污染 → 清洗 → 分析）

```bash
python data_cleaning_main.py
```

产物输出到 `data_cleaning/`，包括干净/污染/清洗后的 CSV、污染日志、清洗报告、分析报告及 5 张图表。

### 3. 难度预测流水线

```bash
# 生成数据集（特征提取 + 标签生成）
python main.py --generate-data

# 训练并评估模型
python main.py --train

# 完整流程（生成数据 + 训练）
python main.py --all

# 使用更长的求解时间以提高标签质量
python main.py --all --time-limit 60
```

预测结果输出到 `results/`，包括模型对比表、特征重要性表及 6 张可视化图表。

## 依赖项

- Python 3.7+
- pandas >= 1.3.0
- numpy >= 1.21.0
- scikit-learn >= 1.0.0
- matplotlib >= 3.4.0
- seaborn >= 0.11.0
- scipy >= 1.7.0
- xgboost >= 1.5.0 (可选)

## 参考

- ITC2007 Curriculum-Based Course Timetabling (Track 3)
