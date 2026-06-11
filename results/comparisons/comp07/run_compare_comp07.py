"""
运行 comp07 的模型对比并将所有相关产物保存在本文件夹内。
如果需要重新生成，可在仓库根目录运行:

python results/comparisons/comp07/run_compare_comp07.py

"""
from pathlib import Path
import sys
# run_compare_comp07.py 位于 results/comparisons/comp07
# 父目录索引 3 指向仓库根目录
sys.path.insert(0, str(Path(__file__).parents[3]))  # 将仓库根加入 sys.path

from schedule_solver import compare_models

if __name__ == '__main__':
    data_dir = Path('data')
    ctt_path = data_dir / 'comp07.ctt'
    out_dir = Path('results')
    compare_models(ctt_path, out_dir, verbose=False)
    print('compare_comp07 已生成于', out_dir / 'comparisons' / 'comp07')
