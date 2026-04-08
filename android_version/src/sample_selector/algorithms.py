# src/sample_selector/algorithms.py

import random
import math
import time
from itertools import combinations

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
    T = 1000.0          # 初始温度
    T_min = 1e-8        # 终止温度
    cooling_rate = 0.995  # 冷却率
    max_iter = 20000     # 最大迭代次数

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


def parse_samples(raw_text, n, mode):
    """解析样本输入"""
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
    """解析重点样本索引"""
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