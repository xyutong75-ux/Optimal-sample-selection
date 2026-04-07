import os
import sys
import json
import time
import random
import math
from datetime import datetime
from itertools import combinations

import tkinter as tk
from tkinter import ttk, messagebox


def get_base_dir() -> str:
    """获取结果保存目录（打包后为 exe 所在目录，开发时为脚本目录）。"""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


BASE_DIR = get_base_dir()
RESULTS_DIR = os.path.join(BASE_DIR, "results")
os.makedirs(RESULTS_DIR, exist_ok=True)


def parse_int(value, name, errors, min_value=None, max_value=None):
    try:
        iv = int(value)
    except (TypeError, ValueError):
        errors.append(f"{name} 必须是整数。")
        return None
    if min_value is not None and iv < min_value:
        errors.append(f"{name} 不能小于 {min_value}。")
    if max_value is not None and iv > max_value:
        errors.append(f"{name} 不能大于 {max_value}。")
    return iv


def parse_samples(raw_text, n, mode):
    if mode != "manual":
        return [f"S{i+1}" for i in range(n)]
    if not raw_text:
        raise ValueError("手动输入模式下，样本列表不能为空。")
    separators = [",", " ", "\n", "\r", "\t", ";", "，", "；"]
    text = raw_text
    for sep in separators:
        text = text.replace(sep, " ")
    items = [item.strip() for item in text.split(" ") if item.strip()]
    if len(items) != n:
        raise ValueError(f"手动样本数量为 {len(items)}，与 n={n} 不一致。")
    return items


def parse_special_indices(raw_text, n, j):
    if not raw_text:
        return list(range(j))
    separators = [",", " ", "\n", "\r", "\t", ";", "，", "；"]
    text = raw_text
    for sep in separators:
        text = text.replace(sep, " ")
    tokens = [t.strip() for t in text.split(" ") if t.strip()]
    if len(tokens) != j:
        raise ValueError(f"重点样本序号数量为 {len(tokens)}，应为 j={j}。")
    indices = []
    for t in tokens:
        try:
            idx = int(t)
        except ValueError:
            raise ValueError("重点样本序号必须是 1~n 的整数。")
        if not (1 <= idx <= n):
            raise ValueError(f"重点样本序号 {idx} 超出范围 1~{n}。")
        pos = idx - 1
        if pos in indices:
            raise ValueError(f"重点样本序号 {idx} 存在重复。")
        indices.append(pos)
    return indices


''' 暴力枚举法
def enumerate_groups(samples, special_indices, m, n, k, j, s):
    total_indices = list(range(n))
    special_set = set(special_indices)
    preferred = []
    others = []
    for comb in combinations(total_indices, k):
        count_special = sum(1 for idx in comb if idx in special_set)
        target = [samples[i] for i in comb]
        if count_special >= s:
            preferred.append(target)
        else:
            others.append(target)
        if len(preferred) >= m and len(preferred) + len(others) >= m:
            break
    result = preferred[:m]
    if len(result) < m:
        needed = m - len(result)
        result.extend(others[:needed])
    return result'''

'''初始贪心算法
def enumerate_groups(samples, special_indices, m, n, k, j, s):
    """
    贪心算法求最小k元组集合
    输入输出格式与原函数完全一致
    """
    import itertools
    from itertools import combinations

    # ===== 你的算法核心 =====
    def can_satisfy(k_tuple, j_tuple, s):
        """检查k元组是否能满足j元组"""
        for s_subset in combinations(j_tuple, s):
            if all(elem in k_tuple for elem in s_subset):
                return True
        return False

    # 生成所有j元组（用数字1..n表示）
    all_j_tuples = list(combinations(range(1, n + 1), j))

    # 生成所有k元组（用数字1..n表示）
    all_k_tuples = list(combinations(range(1, n + 1), k))

    # 贪心选择
    j_covered = [False] * len(all_j_tuples)
    k_used = [False] * len(all_k_tuples)
    selected_k_indices = []  # 记录选中的k元组下标
    covered_count = 0

    while covered_count < len(all_j_tuples) and len(selected_k_indices) < m:
        best_k = -1
        best_new = 0

        # 找能新满足最多j元组的k元组
        for k_idx, k_tuple in enumerate(all_k_tuples):
            if k_used[k_idx]:
                continue

            new_cover = 0
            for j_idx, j_tuple in enumerate(all_j_tuples):
                if not j_covered[j_idx] and can_satisfy(k_tuple, j_tuple, s):
                    new_cover += 1

            if new_cover > best_new:
                best_new = new_cover
                best_k = k_idx

        if best_k == -1 or best_new == 0:
            break

        # 选中这个k元组
        selected_k_indices.append(best_k)
        k_used[best_k] = True

        # 更新被满足的j元组
        for j_idx, j_tuple in enumerate(all_j_tuples):
            if not j_covered[j_idx] and can_satisfy(all_k_tuples[best_k], j_tuple, s):
                j_covered[j_idx] = True
                covered_count += 1

    # ===== 把数字结果转成样本名（与原函数输出格式一致）=====
    result = []
    for k_idx in selected_k_indices[:m]:  # 最多取m个
        # all_k_tuples[k_idx] 是 (1,2,3,4,5,6) 这样的元组
        # 转成样本名：samples[i-1] 因为样本索引从0开始
        group = [samples[i - 1] for i in all_k_tuples[k_idx]]
        result.append(group)

    # 如果没找到任何解，返回空列表
    if not result:
        return []

    # 如果不够m个，用原算法的逻辑补足（可选）
    if len(result) < m:
        print(f"Warning: Only found {len(result)} tuples, need {m}")
        # 可以在这里添加补足逻辑，或者直接返回已有的

    return result[:m]
'''

'''
def enumerate_groups(samples, special_indices, m, n, k, j, s):
    """
    使用位运算优化的贪心算法
    """
    import itertools
    from itertools import combinations

    # 预计算所有可能的 s-子集的位表示
    def tuple_to_bitmask(tup):
        mask = 0
        for x in tup:
            mask |= 1 << (x - 1)
        return mask

    # 生成所有 j-元组的位掩码
    all_j_tuples = list(combinations(range(1, n + 1), j))
    j_masks = [tuple_to_bitmask(t) for t in all_j_tuples]

    # 生成所有 k-元组的位掩码
    all_k_tuples = list(combinations(range(1, n + 1), k))
    k_masks = [tuple_to_bitmask(t) for t in all_k_tuples]

    # 预计算每个 k-元组能覆盖哪些 j-元组（使用位运算）
    # 对于每个 k-元组，预先计算它能覆盖的所有 j-元组的索引
    k_coverage = []
    for k_mask in k_masks:
        covered = []
        # 检查这个 k-元组是否能覆盖每个 j-元组
        for j_idx, j_mask in enumerate(j_masks):
            # 检查是否存在 s 个重点样本被覆盖
            # 即 j_mask & k_mask 中 1 的个数 >= s
            common = j_mask & k_mask
            if bin(common).count('1') >= s:
                covered.append(j_idx)
        k_coverage.append(set(covered))  # 用set加速查找

    # 贪心选择
    j_covered = [False] * len(j_masks)
    k_used = [False] * len(k_masks)
    selected_k_indices = []
    covered_count = 0

    # 使用优先队列优化选择过程
    import heapq

    while covered_count < len(j_masks) and len(selected_k_indices) < m:
        best_k = -1
        best_new = 0

        # 快速计算每个未使用的k-元组能新覆盖的数量
        for k_idx in range(len(k_masks)):
            if k_used[k_idx]:
                continue

            # 计算新覆盖的数量
            new_cover = 0
            for j_idx in k_coverage[k_idx]:
                if not j_covered[j_idx]:
                    new_cover += 1

            if new_cover > best_new:
                best_new = new_cover
                best_k = k_idx

        if best_k == -1 or best_new == 0:
            break

        # 选中这个k-元组
        selected_k_indices.append(best_k)
        k_used[best_k] = True

        # 更新被覆盖的j-元组
        for j_idx in k_coverage[best_k]:
            if not j_covered[j_idx]:
                j_covered[j_idx] = True
                covered_count += 1

    # 转换为样本名
    result = []
    for k_idx in selected_k_indices[:m]:
        group = [samples[i - 1] for i in all_k_tuples[k_idx]]
        result.append(group)

    return result'''


def enumerate_groups(samples, special_indices, m, n, k, j, s, t=1):
    """
    贪心 + 模拟退火优化，适用于所有规模
    """

    # 预计算所有可能的 s-子集的位表示（实际未用位运算，但保留函数名）
    def tuple_to_bitmask(tup):
        mask = 0
        for x in tup:
            mask |= 1 << (x - 1)
        return mask

    # 生成所有 j-元组的位掩码
    all_j_tuples = list(combinations(range(1, n + 1), j))
    j_masks = [tuple_to_bitmask(t) for t in all_j_tuples]

    # 生成所有 k-元组的位掩码
    all_k_tuples = list(combinations(range(1, n + 1), k))
    k_masks = [tuple_to_bitmask(t) for t in all_k_tuples]

    # 预计算每个 k-元组能覆盖哪些 j-元组（存储索引）
    k_coverage = []
    for k_mask in k_masks:
        covered = []
        for j_idx, j_mask in enumerate(j_masks):
            common = j_mask & k_mask
            if bin(common).count('1') >= s:
                covered.append(j_idx)
        k_coverage.append(set(covered))

    # ========== 贪心选择初始解 ==========
    j_satisfied_count = [0] * len(j_masks)
    k_used = [False] * len(k_masks)
    selected_k_indices_greedy = []

    all_satisfied = False
    while not all_satisfied and len(selected_k_indices_greedy) < m:
        best_k = -1
        best_score = -1

        for k_idx in range(len(k_masks)):
            if k_used[k_idx]:
                continue

            contribution = 0
            for j_idx in k_coverage[k_idx]:
                if j_satisfied_count[j_idx] < t:
                    contribution += 1

            if contribution > best_score:
                best_score = contribution
                best_k = k_idx

        if best_k == -1 or best_score == 0:
            break

        selected_k_indices_greedy.append(best_k)
        k_used[best_k] = True

        for j_idx in k_coverage[best_k]:
            j_satisfied_count[j_idx] += 1

        all_satisfied = all(count >= t for count in j_satisfied_count)

    if not all_satisfied:
        return []  # 无可行解

    # ========== 模拟退火优化 ==========
    # 将当前解转换为布尔数组（便于操作）
    k_count = len(k_masks)
    current = [False] * k_count
    for idx in selected_k_indices_greedy:
        current[idx] = True

    # 计算每个j元组当前被覆盖的次数
    current_counts = j_satisfied_count[:]

    # 辅助函数：判断当前解是否满足所有j元组覆盖次数 >= t
    def is_valid(counts):
        return all(c >= t for c in counts)

    # 辅助函数：从解数组更新计数
    def update_counts_from_solution(solution):
        counts = [0] * len(j_masks)
        for k_idx, chosen in enumerate(solution):
            if chosen:
                for j_idx in k_coverage[k_idx]:
                    counts[j_idx] += 1
        return counts

    # 能量函数：优先保证覆盖，其次最小化选中数
    # 能量 = 大常数 * 未满足的j元组数 + 选中的k元组数
    BIG = 10000

    def energy(solution):
        counts = update_counts_from_solution(solution)
        unsatisfied = sum(1 for c in counts if c < t)
        selected = sum(solution)
        return BIG * unsatisfied + selected

    # 当前能量
    current_energy = energy(current)
    best_solution = current[:]
    best_energy = current_energy

    # 退火参数
    T = 1000.0  # 初始温度
    T_min = 1e-8  # 终止温度
    cooling_rate = 0.995  # 冷却率
    max_iter = 20000  # 最大迭代次数

    # 预计算所有未选中的索引（加快随机选择）
    all_indices = list(range(k_count))

    for iteration in range(max_iter):
        if T < T_min:
            break

        # 生成新解：随机选择一种操作（添加、移除、交换）
        op = random.randint(0, 2)
        new_solution = current[:]

        if op == 0:  # 添加一个未选中的k元组
            # 找到所有未选中的索引
            candidates = [i for i in all_indices if not new_solution[i]]
            if candidates:
                add_idx = random.choice(candidates)
                new_solution[add_idx] = True
        elif op == 1:  # 移除一个选中的k元组
            # 找到所有选中的索引
            candidates = [i for i in all_indices if new_solution[i]]
            if candidates:
                remove_idx = random.choice(candidates)
                new_solution[remove_idx] = False
        else:  # 交换：移除一个并添加另一个
            # 找到选中的和未选中的
            selected = [i for i in all_indices if new_solution[i]]
            unselected = [i for i in all_indices if not new_solution[i]]
            if selected and unselected:
                remove_idx = random.choice(selected)
                add_idx = random.choice(unselected)
                new_solution[remove_idx] = False
                new_solution[add_idx] = True

        # 计算新能量
        new_energy = energy(new_solution)

        # 决定是否接受新解
        if new_energy < current_energy:
            accept = True
        else:
            # Metropolis 准则
            delta = new_energy - current_energy
            prob = math.exp(-delta / T)
            accept = random.random() < prob

        if accept:
            current = new_solution[:]
            current_energy = new_energy
            if current_energy < best_energy:
                best_solution = current[:]
                best_energy = current_energy

        # 降温
        T *= cooling_rate

        # 定期进行局部优化：尝试移除冗余的k元组（仅当解有效时）
        if iteration % 1000 == 0 and is_valid(update_counts_from_solution(best_solution)):
            # 从后往前检查
            changed = True
            while changed:
                changed = False
                # 获取当前最优解的计数
                counts = update_counts_from_solution(best_solution)
                # 尝试移除每个选中的
                for i in all_indices:
                    if best_solution[i]:
                        temp = best_solution[:]
                        temp[i] = False
                        temp_counts = update_counts_from_solution(temp)
                        if all(c >= t for c in temp_counts):
                            best_solution = temp[:]
                            best_energy = BIG * 0 + sum(best_solution)
                            changed = True
                            break  # 从头开始重新检查
                # 如果没有移除任何，退出循环

    # 最终，从 best_solution 中提取选中的k元组索引
    final_indices = [i for i in all_indices if best_solution[i]]

    # 如果解不满足覆盖（理论上不应发生），回退到贪心解
    counts_final = update_counts_from_solution(best_solution)
    if not all(c >= t for c in counts_final):
        final_indices = selected_k_indices_greedy

    # 转换为样本名
    result = []
    for k_idx in final_indices[:m]:
        group = [samples[i - 1] for i in all_k_tuples[k_idx]]
        result.append(group)

    return result





def save_result(params, samples, special_indices, groups):
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    filename = f"result_{timestamp}.json"
    path = os.path.join(RESULTS_DIR, filename)
    data = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "params": params,
        "samples": samples,
        "special_indices": special_indices,
        "groups": groups,
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return filename


class SampleSelectionApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("最优样本选择系统")
        self.root.geometry("920x620")
        self.root.minsize(820, 560)

        try:
            self.root.iconbitmap(default="")  # 可根据需要添加图标
        except Exception:
            pass

        self._build_ui()

    def _build_ui(self):
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        title_label = ttk.Label(
            main_frame,
            text="最优样本选择系统",
            font=("Microsoft YaHei", 16, "bold"),
        )
        title_label.pack(anchor=tk.CENTER, pady=(0, 4))

        sub_label = ttk.Label(
            main_frame,
            text="使用枚举法生成满足约束条件的样本组合，结果自动保存到程序同级目录的 results 文件夹。",
            font=("Microsoft YaHei", 9),
            foreground="#555555",
        )
        sub_label.pack(anchor=tk.CENTER, pady=(0, 8))

        content = ttk.Notebook(main_frame)
        self.content = content
        self.page_main = ttk.Frame(content)
        self.page_history = ttk.Frame(content)
        content.add(self.page_main, text="运算")
        content.add(self.page_history, text="历史记录")
        content.pack(fill=tk.BOTH, expand=True, pady=(6, 0))

        self._build_main_page(self.page_main)
        self._build_history_page(self.page_history)

    def _build_main_page(self, parent):
        top_frame = ttk.Frame(parent)
        top_frame.pack(fill=tk.X, pady=(4, 4))

        self.var_m = tk.StringVar()
        self.var_n = tk.StringVar()
        self.var_k = tk.StringVar()
        self.var_j = tk.StringVar()
        self.var_s = tk.StringVar()
        self.var_t = tk.StringVar(value="1") # 新增 t 参数，默认值为 1
        self.var_sample_mode = tk.StringVar(value="random")
        self.var_special_indices = tk.StringVar()

        def add_labeled_entry(row, col, text, var, width=10, hint=None):
            frame = ttk.Frame(top_frame)
            frame.grid(row=row, column=col, sticky="w", padx=4, pady=3)
            label = ttk.Label(frame, text=text)
            label.pack(anchor="w")
            entry = ttk.Entry(frame, textvariable=var, width=width)
            entry.pack(anchor="w")
            if hint:
                hint_label = ttk.Label(
                    frame,
                    text=hint,
                    font=("Microsoft YaHei", 8),
                    foreground="#888888",
                )
                hint_label.pack(anchor="w", pady=(1, 0))
            return entry

        top_frame.columnconfigure(0, weight=1)
        top_frame.columnconfigure(1, weight=1)
        top_frame.columnconfigure(2, weight=1)

        add_labeled_entry(
            0,
            0,
            "输出组合数量 m (建议 45–54)",
            self.var_m,
            hint="用于限制最终显示/保存的组合数量。",
        )
        add_labeled_entry(
            0,
            1,
            "样本总数 n (7–25)",
            self.var_n,
        )
        add_labeled_entry(
            0,
            2,
            "每组样本数 k (4–7)",
            self.var_k,
        )
        add_labeled_entry(
            1,
            0,
            "重点样本数 j (s ≤ j ≤ k)",
            self.var_j,
            hint="在 n 个样本中，事先指定的“重点样本”数量。",
        )
        add_labeled_entry(
            1,
            1,
            "至少包含的重点样本数 s (3–7)",
            self.var_s,
            hint="每个 k 样本组合中，至少要包含的重点样本个数。",
        )
        # 新增 t 参数输入框
        add_labeled_entry(
            1,
            2,  # 放在第一行第三列
            "每个j元组至少被t个不同的k元组覆盖",
            self.var_t,
            hint="默认t=1",
        )
        mode_frame = ttk.LabelFrame(parent, text="样本设置")
        mode_frame.pack(fill=tk.X, padx=2, pady=(6, 4))

        radio_frame = ttk.Frame(mode_frame)
        radio_frame.pack(fill=tk.X, padx=4, pady=(4, 2))
        ttk.Radiobutton(
            radio_frame,
            text="随机自动生成 n 个样本（S1, S2, ...）",
            variable=self.var_sample_mode,
            value="random",
        ).pack(side=tk.LEFT, padx=(0, 14))
        ttk.Radiobutton(
            radio_frame,
            text="手动输入 n 个样本",
            variable=self.var_sample_mode,
            value="manual",
        ).pack(side=tk.LEFT)

        manual_frame = ttk.Frame(mode_frame)
        manual_frame.pack(fill=tk.BOTH, expand=True, padx=4, pady=(2, 4))

        label_samples = ttk.Label(
            manual_frame,
            text="手动样本列表（仅在“手动输入”模式下有效，多种分隔符均可）：",
        )
        label_samples.pack(anchor="w")
        self.txt_samples = tk.Text(manual_frame, height=5, wrap=tk.WORD)
        self.txt_samples.pack(fill=tk.BOTH, expand=True, pady=(2, 2))
        hint_samples = ttk.Label(
            manual_frame,
            text="示例：A1, A2, A3, ... （逗号、空格、换行、中文逗号等均可分隔）",
            font=("Microsoft YaHei", 8),
            foreground="#888888",
        )
        hint_samples.pack(anchor="w")

        idx_frame = ttk.Frame(mode_frame)
        idx_frame.pack(fill=tk.X, padx=4, pady=(4, 4))
        ttk.Label(
            idx_frame,
            text="重点样本序号（1~n，j 个，以逗号或空格分隔）：",
        ).pack(anchor="w")
        entry_idx = ttk.Entry(idx_frame, textvariable=self.var_special_indices)
        entry_idx.pack(fill=tk.X, pady=(2, 0))
        ttk.Label(
            idx_frame,
            text="留空时：默认前 j 个样本为重点样本；填写时：总数必须为 j，且每个序号在 1~n 之间。",
            font=("Microsoft YaHei", 8),
            foreground="#888888",
        ).pack(anchor="w", pady=(1, 0))

        btn_frame = ttk.Frame(parent)
        btn_frame.pack(fill=tk.X, pady=(6, 4))

        btn_clear = ttk.Button(btn_frame, text="清空输入", command=self.clear_inputs)
        btn_clear.pack(side=tk.RIGHT, padx=(0, 6))

        btn_run = ttk.Button(btn_frame, text="运行枚举算法并保存结果", command=self.run_algorithm)
        btn_run.pack(side=tk.RIGHT, padx=(0, 10))

        btn_refresh_history = ttk.Button(
            btn_frame,
            text="刷新历史记录",
            command=self.refresh_history,
        )
        btn_refresh_history.pack(side=tk.LEFT, padx=(4, 0))

        result_frame = ttk.LabelFrame(parent, text="本次运算结果")
        result_frame.pack(fill=tk.BOTH, expand=True, padx=2, pady=(4, 2))

        # 枚举结果个数：醒目单独一行
        count_frame = ttk.Frame(result_frame)
        count_frame.pack(fill=tk.X, padx=4, pady=(6, 4))
        ttk.Label(count_frame, text="枚举结果个数：", font=("Microsoft YaHei", 12, "bold")).pack(side=tk.LEFT)
        self.lbl_result_count = tk.Label(
            count_frame,
            text="—",
            font=("Microsoft YaHei", 14, "bold"),
            fg="#1a73e8",
        )
        self.lbl_result_count.pack(side=tk.LEFT, padx=(0, 4))
        ttk.Label(count_frame, text="组", font=("Microsoft YaHei", 12, "bold")).pack(side=tk.LEFT)
        self.lbl_result_footer = ttk.Label(
            result_frame,
            text="",
            font=("Microsoft YaHei", 9),
            foreground="#666666",
        )
        self.lbl_result_footer.pack(anchor="w", padx=4, pady=(0, 2))

        self.var_result_summary = tk.StringVar(value="尚未计算，点击「运行枚举算法并保存结果」后此处显示。")
        lbl_summary = ttk.Label(
            result_frame,
            textvariable=self.var_result_summary,
            foreground="#555555",
            font=("Microsoft YaHei", 9),
        )
        lbl_summary.pack(anchor="w", padx=4, pady=(0, 2))

        # 全部枚举结果列表标题
        self.lbl_list_title = ttk.Label(
            result_frame,
            text="全部枚举结果列表（每组 k 个样本，可滚动查看全部）：",
            font=("Microsoft YaHei", 10, "bold"),
        )
        self.lbl_list_title.pack(anchor="w", padx=4, pady=(6, 2))

        list_frame = ttk.Frame(result_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=4, pady=(0, 4))

        self.lst_results = tk.Listbox(
            list_frame,
            height=28,
            font=("Consolas", 10),
        )
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.lst_results.yview)
        self.lst_results.configure(yscrollcommand=scrollbar.set)
        self.lst_results.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.result_frame = result_frame

    def _build_history_page(self, parent):
        top_frame = ttk.Frame(parent)
        top_frame.pack(fill=tk.X, pady=(4, 4))

        btn_refresh = ttk.Button(top_frame, text="刷新历史记录", command=self.refresh_history)
        btn_refresh.pack(side=tk.LEFT, padx=(4, 4))

        btn_clear = ttk.Button(
            top_frame,
            text="清空全部记录",
            command=self.clear_all_history,
        )
        btn_clear.pack(side=tk.LEFT)

        lbl_tip = ttk.Label(
            top_frame,
            text=f"结果文件保存在：{RESULTS_DIR}",
            font=("Microsoft YaHei", 8),
            foreground="#777777",
        )
        lbl_tip.pack(side=tk.RIGHT, padx=(4, 4))

        columns = ("time", "params", "n", "count", "filename")
        self.tree_history = ttk.Treeview(
            parent,
            columns=columns,
            show="headings",
            selectmode="browse",
        )
        self.tree_history.heading("time", text="时间")
        self.tree_history.heading("params", text="参数 (m, n, k, j, s)")
        self.tree_history.heading("n", text="样本数 n")
        self.tree_history.heading("count", text="结果组合数")
        self.tree_history.heading("filename", text="文件名")

        self.tree_history.column("time", width=140, anchor="w")
        self.tree_history.column("params", width=200, anchor="w")
        self.tree_history.column("n", width=70, anchor="center")
        self.tree_history.column("count", width=90, anchor="center")
        self.tree_history.column("filename", width=200, anchor="w")

        vsb = ttk.Scrollbar(parent, orient="vertical", command=self.tree_history.yview)
        self.tree_history.configure(yscrollcommand=vsb.set)

        self.tree_history.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(4, 0), pady=(0, 4))
        vsb.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 4), pady=(0, 4))

        btn_frame = ttk.Frame(parent)
        btn_frame.pack(fill=tk.X, pady=(0, 4))

        btn_view = ttk.Button(btn_frame, text="查看选中记录详情", command=self.view_selected_history)
        btn_view.pack(side=tk.LEFT, padx=(4, 4))

        btn_delete = ttk.Button(btn_frame, text="删除选中记录", command=self.delete_selected_history)
        btn_delete.pack(side=tk.LEFT)

        self.refresh_history()

    def clear_inputs(self):
        self.var_m.set("")
        self.var_n.set("")
        self.var_k.set("")
        self.var_j.set("")
        self.var_s.set("")
        self.var_t.set("1")  # 新增：清空时恢复默认值 1
        self.var_sample_mode.set("random")
        self.var_special_indices.set("")
        self.txt_samples.delete("1.0", tk.END)
        self.lst_results.delete(0, tk.END)
        self.lbl_result_count.config(text="—")
        self.lbl_result_footer.config(text="")
        self.lbl_list_title.config(text="全部枚举结果列表（每组 k 个样本，可滚动查看全部）：")
        self.var_result_summary.set("输入已清空。")

    def run_algorithm(self):
        t0 = time.perf_counter()
        errors = []
        m = parse_int(self.var_m.get(), "m", errors)
        n = parse_int(self.var_n.get(), "n", errors, min_value=7, max_value=25)
        k = parse_int(self.var_k.get(), "k", errors, min_value=4, max_value=7)
        j = parse_int(self.var_j.get(), "j", errors)
        s = parse_int(self.var_s.get(), "s", errors)
        t = parse_int(self.var_t.get(), "t", errors, min_value=1)  # 新增 t 参数解析

        if m is not None and (m < 1 or m > 10000):
            errors.append("m 建议在 1~10000 之间（通常 45~54）。")
        if j is not None and s is not None and j < s:
            errors.append("必须满足 j ≥ s。")
        if k is not None and j is not None and j > k:
            errors.append("必须满足 j ≤ k。")
        if n is not None and k is not None and k > n:
            errors.append("必须满足 k ≤ n。")
            # 新增 t 参数验证
        if t is not None and t < 1:
            errors.append("必须满足 t >= 1。")
        if errors:
            messagebox.showerror("参数错误", "\n".join(errors))
            return

        sample_mode = self.var_sample_mode.get()
        samples_text = self.txt_samples.get("1.0", tk.END)
        special_indices_text = self.var_special_indices.get()

        try:
            samples = parse_samples(samples_text, n, sample_mode)
            special_indices = parse_special_indices(special_indices_text, n, j)
        except ValueError as e:
            messagebox.showerror("输入错误", str(e))
            return

        groups = enumerate_groups(samples, special_indices, m, n, k, j, s,t)
        self.lst_results.delete(0, tk.END)
        for idx, g in enumerate(groups, start=1):
            self.lst_results.insert(tk.END, f"#{idx}: " + ", ".join(g))

        params = {"m": m, "n": n, "k": k, "j": j, "s": s, "t": t}
        filename = save_result(params, samples, special_indices, groups)

        # 立刻呈现：枚举结果个数 + 全部结果列表
        n_group = len(groups)
        elapsed_s = time.perf_counter() - t0
        elapsed_ms = int(round(elapsed_s * 1000))
        self.lbl_result_count.config(text=str(n_group))
        self.var_result_summary.set(f"已保存为文件：{filename}（计算耗时：{elapsed_ms} ms）")
        self.lbl_list_title.config(
            text=f"全部 {n_group} 组枚举结果如下（可滚动查看）："
        )
        self.lbl_result_footer.config(
            text=f"已呈现全部 {n_group} 组枚举结果。计算耗时：{elapsed_ms} ms"
        )
        # 确保结果区域可见：选中「运算」页并滚动列表到顶部
        self.content.select(0)
        self.lst_results.see(0)
        self.result_frame.lift()

        # 生成本次运行的“编码”，形如 m-n-k-j-s-运行次数-结果个数（对应讲义中的格式）
        run_index = getattr(self, "run_counter", 0) + 1
        self.run_counter = run_index
        db_code = f"{m}-{n}-{k}-{j}-{s}-{t}-{run_index}-{n_group}"

        # 弹出结果预览窗口（类似讲义中的 DB resources 屏幕）
        self.show_result_popup(db_code, groups, elapsed_ms)

        self.refresh_history()

    def show_result_popup(self, code: str, groups, elapsed_ms: int):
        """显示一个弹窗窗口，按讲义中 Data Base Resources 的格式预览本次结果。"""
        win = tk.Toplevel(self.root)
        win.title(f"结果预览 - {code}")
        win.geometry("720x520")

        header = ttk.Label(
            win,
            text=f"Data Base Record: {code}    (Time: {elapsed_ms} ms)",
            font=("Microsoft YaHei", 11, "bold"),
        )
        header.pack(anchor="w", padx=10, pady=(10, 4))

        hint = ttk.Label(
            win,
            text="下面为本次计算得到的全部枚举结果（每行一组，可滚动查看）：",
            font=("Microsoft YaHei", 9),
            foreground="#555555",
        )
        hint.pack(anchor="w", padx=10, pady=(0, 4))

        list_frame = ttk.Frame(win)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 6))

        lst = tk.Listbox(
            list_frame,
            font=("Consolas", 10),
        )
        vsb = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=lst.yview)
        lst.configure(yscrollcommand=vsb.set)
        lst.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)

        for idx, g in enumerate(groups, start=1):
            lst.insert(tk.END, f"#{idx}: " + ", ".join(g))

        btn_frame = ttk.Frame(win)
        btn_frame.pack(fill=tk.X, padx=10, pady=(4, 10))

        def on_back():
            win.destroy()

        def on_print():
            # 简单实现：将结果导出为同名 .txt 文件，便于打印
            path = os.path.join(RESULTS_DIR, f"{code}.txt")
            try:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(f"{code}\n")
                    for idx, g in enumerate(groups, start=1):
                        f.write(f"#{idx}: " + ", ".join(g) + "\n")
                messagebox.showinfo("导出成功", f"已将结果导出为文本文件：\n{path}\n可用文本编辑器或 Word 打开后打印。")
            except Exception as e:
                messagebox.showerror("导出失败", f"无法写入文件：{e}")

        btn_back = ttk.Button(btn_frame, text="BACK", command=on_back)
        btn_back.pack(side=tk.RIGHT, padx=(4, 0))

        btn_print = ttk.Button(btn_frame, text="Print", command=on_print)
        btn_print.pack(side=tk.RIGHT, padx=(4, 0))

    def refresh_history(self):
        for item in self.tree_history.get_children():
            self.tree_history.delete(item)

        if not os.path.isdir(RESULTS_DIR):
            return

        items = []
        for name in sorted(os.listdir(RESULTS_DIR)):
            if not name.lower().endswith(".json"):
                continue
            path = os.path.join(RESULTS_DIR, name)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                params = data.get("params", {})
                items.append(
                    (
                        name,
                        data.get("timestamp", ""),
                        params.get("m", ""),
                        params.get("n", ""),
                        params.get("k", ""),
                        params.get("j", ""),
                        params.get("s", ""),
                        len(data.get("groups", [])),
                    )
                )
            except Exception:
                continue

        items.sort(key=lambda x: x[0], reverse=True)
        for rec in items:
            name, ts, m, n, k, j, s, count = rec
            params_str = f"({m}, {n}, {k}, {j}, {s})"
            self.tree_history.insert(
                "",
                tk.END,
                iid=name,
                values=(ts, params_str, n, count, name),
            )

    def get_selected_history_filename(self):
        selection = self.tree_history.selection()
        if not selection:
            messagebox.showwarning("提示", "请先在历史记录中选中一条记录。")
            return None
        return selection[0]

    def view_selected_history(self):
        filename = self.get_selected_history_filename()
        if not filename:
            return
        path = os.path.join(RESULTS_DIR, filename)
        if not os.path.isfile(path):
            messagebox.showerror("错误", "指定的结果文件不存在。")
            self.refresh_history()
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            messagebox.showerror("错误", "结果文件读取失败。")
            return

        params = data.get("params", {})
        groups = data.get("groups", [])
        special_indices = data.get("special_indices", [])
        display_indices = ", ".join(str(i + 1) for i in special_indices) or "(默认前 j 个)"

        win = tk.Toplevel(self.root)
        win.title(f"查看结果 - {filename}")
        win.geometry("720x520")

        info = ttk.Label(
            win,
            text=(
                f"文件名：{filename}\n"
                f"时间：{data.get('timestamp', '')}\n"
                f"参数：m={params.get('m')}, n={params.get('n')}, "
                f"k={params.get('k')}, j={params.get('j')}, s={params.get('s')}\n"
                f"重点样本索引：{display_indices}\n"
                f"结果组合数：{len(groups)} 组"
            ),
            justify=tk.LEFT,
        )
        info.pack(anchor="w", padx=8, pady=(8, 4))

        frame_list = ttk.Frame(win)
        frame_list.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 8))

        lst = tk.Listbox(frame_list)
        vsb = ttk.Scrollbar(frame_list, orient=tk.VERTICAL, command=lst.yview)
        lst.configure(yscrollcommand=vsb.set)
        lst.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)

        for idx, g in enumerate(groups, start=1):
            lst.insert(tk.END, f"#{idx}: " + ", ".join(g))

    def delete_selected_history(self):
        filename = self.get_selected_history_filename()
        if not filename:
            return
        if not messagebox.askyesno("确认删除", f"确定要删除记录文件：\n{filename} 吗？"):
            return
        path = os.path.join(RESULTS_DIR, filename)
        try:
            if os.path.isfile(path):
                os.remove(path)
            self.refresh_history()
            messagebox.showinfo("完成", "记录已删除。")
        except Exception as e:
            messagebox.showerror("错误", f"删除失败：{e}")

    def clear_all_history(self):
        if not messagebox.askyesno(
            "确认清空",
            "确定要删除所有历史记录吗？此操作不可恢复。",
        ):
            return
        removed = 0
        if os.path.isdir(RESULTS_DIR):
            for name in os.listdir(RESULTS_DIR):
                if not name.lower().endswith(".json"):
                    continue
                path = os.path.join(RESULTS_DIR, name)
                try:
                    os.remove(path)
                    removed += 1
                except Exception:
                    continue
        self.refresh_history()
        messagebox.showinfo("完成", f"已删除 {removed} 个历史记录文件。")


def main():
    root = tk.Tk()
    app = SampleSelectionApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()

