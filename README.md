# python
高校课程表调度系统

项目背景

本系统针对高校教务中的经典组合优化问题进行设计与实现，旨在解决课程调度（Course Scheduling）或时间表调度（Timetable Scheduling）问题。该问题涉及在有限的时间资源（时间片）、空间资源（教室）和人力资源（教师）下，安排多门课程的教学活动，同时满足多种约束条件。

本项目融合硬约束（如教室容量、教师时间冲突等）与软约束（如学生、教师的时间偏好），采用混合启发式算法生成可行且高质量的排课方案，为高校教务管理提供实用的决策支持工具。

核心功能

1.  数据建模
    ◦ 构建课程（Course）、教师（Teacher）、教室（Room）、班级（ClassGroup）和时间片（TimeSlot）等核心实体模型

    ◦ 建立各实体间的关联关系（如课程属于教师、课程对应班级、教室配备特定设施等）

2.  约束定义与检测
    ◦ 硬约束：必须满足的约束条件

        ▪ 教室容量（教室可容纳学生数 ≥ 课程班级总人数）

        ▪ 教师时间冲突（同一教师在同一时间只能上一门课）

        ▪ 教室占用冲突（同一教室在同一时间只能安排一门课）

        ▪ 班级时间冲突（同一班级在同一时间只能上一门课）

        ▪ 教师不可用时间（教师在其不可用时间段内不能排课）

    ◦ 软约束：期望满足的偏好条件

        ▪ 课程偏好的时间段

        ▪ 教师偏好的时间段

    ◦ 实现evaluate_constraints函数，量化评估排课方案对各项约束的满足程度

3.  优化求解
    ◦ 实现HybridSolver混合求解器，包含构造初始解和局部搜索优化两个阶段

    ◦ 构造阶段：按课程复杂度（影响班级数、学生数）排序，采用贪心策略为每门课程寻找最优教室和时间

    ◦ 优化阶段：采用爬山法（Hill Climbing）进行局部搜索，尝试调整已安排课程以提升整体满意度

    ◦ 输出排课方案（Solution）及其约束满足度评估结果

4.  输出与可视化
    ◦ 生成CSV格式的课程安排表

    ◦ 生成HTML格式的可视化课表

    ◦ 生成JSON格式的详细约束满足度报告

系统架构

主要数据结构

类名 功能描述 关键属性

TimeSlot 时间片 星期（0-4对应周一至周五），节次（0-7对应第1-8节课）

Course 课程 课程ID、名称、授课教师、对应班级、班级人数、周课时数、偏好时间、所需教室设施等

Teacher 教师 教师ID、姓名、不可用时间、偏好时间等

Room 教室 教室ID、名称、容量、设施等

ClassGroup 班级 班级ID、名称、人数、所上课程等

Assignment 课程安排 课程ID、教室ID、时间片

Timetable 课表模型 包含所有实体及已安排的课程列表

核心算法流程

# 伪代码描述
timetable = 加载课程、教师、教室、班级等数据
solver = HybridSolver(timetable, seed=42)

# 求解过程
1. 按课程复杂度排序（影响班级数、学生数降序）
2. 对每门课程：
   2.1 遍历所有可用教室和时间组合
   2.2 检查是否违反约束（教师不可用、资源冲突等）
   2.3 评估候选安排的成本（硬约束违反数*100 + 软约束违反数）
   2.4 选择成本最低的安排
3. 局部优化（爬山法）：
   3.1 以当前安排为基准
   3.2 对每门课程尝试其他教室和时间组合
   3.3 如果新组合提升评分则采纳
4. 返回最优解


约束评分机制

评分函数evaluate_constraints()返回包含以下指标的字典：

• 硬约束违反数（Hard Constraints Violations）

  • hard_room_occupancy：教室占用冲突

  • hard_teacher_conflict：教师时间冲突

  • hard_group_conflict：班级时间冲突

  • hard_capacity：教室容量不足

  • hard_teacher_unavailable：教师不可用时间冲突

  • hard_total：硬约束违反总数

• 软约束违反数（Soft Constraints Violations）

  • soft_preference_penalty：课程偏好时间违反

  • soft_teacher_preference：教师偏好时间违反

  • soft_total：软约束违反总数

• 综合评分：score = -(hard_total * 100 + soft_total)

  • 分值越高（即负数的绝对值越小）表示排课质量越好

  • 硬约束违反的权重（100倍）显著高于软约束违反

技术栈

• 核心语言：Python 3.8+

• 优化算法：贪心构造 + 爬山法局部搜索

• 约束处理：自定义约束检测与评估框架

• 数据处理：标准数据结构（dataclasses, dict, list等）

• 文件格式：CSV, HTML, JSON

• 测试框架：unittest

• 可扩展集成：

  • 可与python-constraint等约束求解库集成

  • 可与DEAP等进化计算框架集成

  • 可与Pandas等数据分析库集成进行结果分析

快速开始

安装与运行

# 克隆项目
git clone https://github.com/yourusername/timetable-scheduler.git
cd timetable-scheduler

# 运行示例
python scheduler.py

# 运行测试
python test_system.py


基本使用

from scheduler import DataLoader, HybridSolver, OutputGenerator

# 1. 加载数据
timetable = DataLoader.create_sample_data()

# 2. 求解
solver = HybridSolver(timetable, seed=42)
solution = solver.solve(time_limit=5)  # 最多运行5秒

# 3. 输出结果
OutputGenerator.generate_timetable_csv(solution, "output/timetable.csv")
OutputGenerator.generate_timetable_html(solution, "output/timetable.html")
OutputGenerator.generate_constraint_report(solution, "output/report.json")


自定义数据

from scheduler import Timetable, Course, Teacher, Room, ClassGroup, TimeSlot

# 创建空课表
timetable = Timetable()

# 添加教师
teacher = Teacher(id="T001", name="王老师", 
                  unavailable={TimeSlot(0, 0), TimeSlot(2, 2)})  # 周一第1节，周三第3节不可用
timetable.add_teacher(teacher)

# 添加教室
room = Room(id="R101", name="教学楼101", capacity=50, features={"投影", "空调"})
timetable.add_room(room)

# 添加班级
group = ClassGroup(id="G2023CS01", name="2023级计算机1班", size=45)
timetable.add_group(group)

# 添加课程
course = Course(
    id="CS101", 
    name="计算机导论", 
    teacher_id="T001", 
    group_ids=["G2023CS01"], 
    size=45,
    sessions_per_week=2,
    preferred_slots=[TimeSlot(1, 1), TimeSlot(3, 1)],  # 偏好周二第2节，周四第2节
    preferred_room_features=["投影"]
)
timetable.add_course(course)

# 求解（同上）


测试

项目包含完整的单元测试，确保核心功能正确性：
# 运行所有测试
python -m pytest test_system.py -v

# 或直接运行测试模块
python test_system.py


测试覆盖：
• 数据加载与模型构建

• 约束冲突检测

• 求解器可行性

• 多种格式输出生成

项目结构


timetable-scheduler/
├── scheduler.py          # 核心调度算法与数据模型
├── test_system.py       # 单元测试
├── requirements.txt     # 依赖包列表
├── README.md           # 项目说明（本文件）
├── examples/           # 使用示例
│   ├── basic_usage.py
│   └── custom_data.py
└── output/             # 输出目录（自动生成）
    ├── timetable.csv
    ├── timetable.html
    └── report.json


扩展与定制

1. 添加新约束类型

# 在Timetable.evaluate_constraints()方法中添加
def evaluate_constraints(self):
    # ... 现有评估逻辑 ...
    
    # 添加新硬约束：特殊教室要求
    hard_special_room = 0
    for assignment in self.assignments.values():
        course = self.courses[assignment.course_id]
        room = self.rooms[assignment.room_id]
        
        # 检查课程要求的特殊设施
        for feature in course.preferred_room_features:
            if feature not in room.features:
                hard_special_room += 1
                
    # 更新返回结果
    return {
        # ... 现有指标 ...
        "hard_special_room": hard_special_room,
        "hard_total": hard_total + hard_special_room,
        "score": -(hard_total * 100 + soft_total + hard_special_room * 50)
    }


2. 集成外部优化库

# 示例：与python-constraint集成
from constraint import Problem, AllDifferentConstraint

def solve_with_csp(timetable):
    problem = Problem()
    
    # 为每门课程添加变量（可能的教室+时间组合）
    for course in timetable.courses.values():
        domain = []
        for room in timetable.rooms.values():
            for timeslot in timetable.timeslots:
                if room.capacity >= course.size:
                    domain.append((room.id, timeslot))
        problem.addVariable(course.id, domain)
    
    # 添加约束
    for course in timetable.courses.values():
        # 教师不可用时间约束
        teacher = timetable.teachers[course.teacher_id]
        # ... 添加约束逻辑
    
    return problem.getSolution()


3. 多目标优化

# 扩展评分函数以支持多目标优化
def evaluate_multi_objective(self):
    metrics = self.evaluate_constraints()
    
    # 新增目标：教室利用率均衡
    room_usage = {}
    for assignment in self.assignments.values():
        room_usage[assignment.room_id] = room_usage.get(assignment.room_id, 0) + 1
    
    usage_std = np.std(list(room_usage.values())) if room_usage else 0
    metrics["room_balance"] = usage_std
    
    return metrics


性能与优化

• 时间复杂度：O(C×R×T)其中C为课程数，R为教室数，T为时间片数

• 空间复杂度：O(C+R+T)主要存储各实体及安排信息

• 优化方向：

  • 使用启发式规则预过滤候选安排

  • 实现并行化评估

  • 集成元启发式算法（遗传算法、模拟退火等）

应用场景

1. 高校教务管理：自动化生成学期课表
2. 培训机构：安排课程与教室资源
3. 会议室调度：企业会议室资源分配
4. 考试安排：考场与监考教师调度
5. 研究平台：组合优化算法实验与比较

未来改进方向

1. 算法增强
   • 集成遗传算法、模拟退火等元启发式算法

   • 实现多目标优化（Pareto前沿）

   • 添加自适应参数调整机制

2. 功能扩展
   • 支持连续多节课程安排

   • 添加课程间前后置关系约束

   • 支持教师工作量均衡约束

   • 添加可视化冲突检测界面

3. 工程优化
   • 添加RESTful API接口

   • 提供Web管理界面

   • 支持数据库持久化存储

   • 实现增量式排课更新

许可证

本项目采用MIT许可证。详见LICENSE文件。

贡献指南

欢迎提交Issue和Pull Request！贡献内容包括但不限于：
• 新的优化算法实现

• 额外约束类型支持

• 性能优化

• 文档改进

• 测试用例补充
本项目为高校课程调度问题的参考实现，旨在平衡算法效率与解的质量，适用于中小规模排课场景。对于大规模复杂场景，建议结合更先进的优化算法和并行计算技术。