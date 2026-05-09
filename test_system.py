# test_system.py - 测试模块
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
import unittest
import tempfile
import os

from scheduler import DataLoader, HybridSolver, Evaluator, OutputGenerator, TimeSlot

class TestCourseScheduler(unittest.TestCase):
    """测试课程安排系统"""
    
    def setUp(self):
        """测试前置设置"""
        self.timetable = DataLoader.create_sample_data()
        self.solver = HybridSolver(self.timetable, seed=42)
    
    def test_data_loading(self):
        """测试数据加载"""
        self.assertGreater(len(self.timetable.courses), 0)
        self.assertGreater(len(self.timetable.teachers), 0)
        self.assertGreater(len(self.timetable.rooms), 0)
    
    def test_constraint_checking(self):
        """测试约束检查"""
        # 创建一个明显违反约束的安排
        test_timetable = DataLoader.create_sample_data()
        
        # 安排两门课在同一时间同一教室
        timeslot = TimeSlot(0, 0)  # 周一第1节课
        room_id = list(test_timetable.rooms.keys())[0]
        
        # 安排第一门课
        course1_id = list(test_timetable.courses.keys())[0]
        test_timetable.add_assignment(course1_id, room_id, timeslot)
        
        # 安排第二门课（应该违反教室占用约束）
        course2_id = list(test_timetable.courses.keys())[1]
        test_timetable.add_assignment(course2_id, room_id, timeslot)
        
        evaluation = test_timetable.evaluate_constraints()
        self.assertGreater(evaluation["hard_room_occupancy"], 0)
    
    def test_solver_feasibility(self):
        """测试求解器可行性"""
        solution = self.solver.solve(time_limit=5)  # 短时间运行测试
        evaluation = Evaluator.evaluate_solution(solution)
        
        # 至少应该能安排一些课程
        self.assertGreater(len(solution.assignments), 0)
    
    def test_output_generation(self):
        """测试输出生成"""
        solution = self.solver.solve(time_limit=2)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # 测试CSV输出
            csv_file = os.path.join(tmpdir, "test.csv")
            OutputGenerator.generate_timetable_csv(solution, csv_file)
            self.assertTrue(os.path.exists(csv_file))
            
            # 测试HTML输出
            html_file = os.path.join(tmpdir, "test.html")
            OutputGenerator.generate_timetable_html(solution, html_file)
            self.assertTrue(os.path.exists(html_file))
            
            # 测试JSON报告
            json_file = os.path.join(tmpdir, "test.json")
            OutputGenerator.generate_constraint_report(solution, json_file)
            self.assertTrue(os.path.exists(json_file))

def run_tests():
    """运行所有测试"""
    unittest.main(argv=[''], verbosity=2, exit=False)

if __name__ == "__main__":
    run_tests()