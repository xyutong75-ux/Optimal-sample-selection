import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox


def get_base_dir() -> str:
    """获取程序所在目录（打包为 exe 后为 exe 所在目录）。"""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


BASE_DIR = get_base_dir()
RESULTS_DIR = os.path.join(BASE_DIR, "results")
os.makedirs(RESULTS_DIR, exist_ok=True)


class SampleSelectionAppStub:
    """
    最优样本选择系统 - UI 框架（无算法版本）

    说明：
    - 本文件只包含界面与交互逻辑，不包含任何“枚举 / 计算”算法。
    - 运行 exe 后，界面可以正常操作，但点击“运行枚举算法”按钮不会真正计算结果。
    - 你可以在 run_algorithm() 中指定的位置，接入你自己的算法。
    """

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("最优样本选择系统（算法占位版本）")
        self.root.geometry("920x620")
        self.root.minsize(820, 560)

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
            text="【算法占位版本】本 exe 仅包含界面，点击计算不会真正运算结果。",
            font=("Microsoft YaHei", 9),
            foreground="#aa0000",
        )
        sub_label.pack(anchor=tk.CENTER, pady=(0, 8))

        content = ttk.Notebook(main_frame)
        self.page_main = ttk.Frame(content)
        self.page_history = ttk.Frame(content)
        content.add(self.page_main, text="运算")
        content.add(self.page_history, text="历史记录（占位）")
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
            "输出组合数量 m (45–54)",
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

        mode_frame = ttk.LabelFrame(parent, text="样本设置")
        mode_frame.pack(fill=tk.X, padx=2, pady=(6, 4))

        radio_frame = ttk.Frame(mode_frame)
        radio_frame.pack(fill=tk.X, padx=4, pady=(4, 2))
        ttk.Radiobutton(
            radio_frame,
            text="随机自动生成 n 个样本（1,2,3,...）",
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

        ttk.Label(
            manual_frame,
            text="手动样本列表（仅在“手动输入”模式下有效，多种分隔符均可）：",
        ).pack(anchor="w")
        self.txt_samples = tk.Text(manual_frame, height=5, wrap=tk.WORD)
        self.txt_samples.pack(fill=tk.BOTH, expand=True, pady=(2, 2))
        ttk.Label(
            manual_frame,
            text="示例：1,2,3,... （逗号、空格、换行、中文逗号等均可分隔）",
            font=("Microsoft YaHei", 8),
            foreground="#888888",
        ).pack(anchor="w")

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

        btn_run = ttk.Button(btn_frame, text="运行枚举算法（占位）", command=self.run_algorithm)
        btn_run.pack(side=tk.RIGHT, padx=(0, 10))

        result_frame = ttk.LabelFrame(parent, text="本次运算结果（占位）")
        result_frame.pack(fill=tk.BOTH, expand=True, padx=2, pady=(4, 2))

        ttk.Label(
            result_frame,
            text="这里原本显示你的算法计算出的全部枚举结果（每行一组）。",
            font=("Microsoft YaHei", 9),
            foreground="#555555",
        ).pack(anchor="w", padx=4, pady=(4, 2))

        self.lst_results = tk.Listbox(
            result_frame,
            height=22,
            font=("Consolas", 10),
        )
        scrollbar = ttk.Scrollbar(result_frame, orient=tk.VERTICAL, command=self.lst_results.yview)
        self.lst_results.configure(yscrollcommand=scrollbar.set)
        self.lst_results.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(4, 0), pady=(0, 4))
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 4), pady=(0, 4))

    def _build_history_page(self, parent):
        ttk.Label(
            parent,
            text="历史记录页面（占位）：算法接入后，可在此读取 results 目录中的 DB 文件并展示。",
            font=("Microsoft YaHei", 9),
            foreground="#555555",
            wraplength=760,
            justify=tk.LEFT,
        ).pack(anchor="nw", padx=10, pady=10)

    def clear_inputs(self):
        self.var_m.set("")
        self.var_n.set("")
        self.var_k.set("")
        self.var_j.set("")
        self.var_s.set("")
        self.var_sample_mode.set("random")
        self.var_special_indices.set("")
        self.txt_samples.delete("1.0", tk.END)
        self.lst_results.delete(0, tk.END)

    def run_algorithm(self):
        """
        点击“运行枚举算法（占位）”按钮后的回调。

        目前只做两件事：
        1. 简单读取当前界面的输入参数；
        2. 给出一个弹窗，提示“这里可以接入你的算法”，并在下方列表中展示示例占位文字。

        【在这里接入你的算法】
        ---------------------------------------------------------------
        你可以参考 main.py 中的实现，大致步骤如下：

        1. 从界面读取参数并做基本校验：
           - m = int(self.var_m.get())
           - n = int(self.var_n.get())
           - k = int(self.var_k.get())
           - j = int(self.var_j.get())
           - s = int(self.var_s.get())

        2. 根据 self.var_sample_mode 获取样本列表 samples（长度为 n）：
           - 如果 sample_mode == 'random'：
               samples = [f\"S{i+1}\" for i in range(n)]
           - 否则从 self.txt_samples 中解析出 n 个样本（用逗号 / 空格 / 换行分隔）

        3. 根据 self.var_special_indices 解析出“重点样本”的索引列表 special_indices。

        4. 调用你自己的算法函数，例如：
               groups = your_enumerate_function(samples, special_indices, m, n, k, j, s)
           要求 groups 是一个二维列表，例如：
               [[\"S1\", \"S2\", ...], [\"S3\", \"S4\", ...], ...]

        5. 把结果显示到列表中：
               self.lst_results.delete(0, tk.END)
               for idx, g in enumerate(groups, start=1):
                   self.lst_results.insert(tk.END, f\"#{idx}: \" + \", \".join(g))

        6. （可选）把结果写入文件 / 弹出预览窗口 / 打印等。
        ---------------------------------------------------------------
        """
        m = self.var_m.get() or "?"
        n = self.var_n.get() or "?"
        k = self.var_k.get() or "?"
        j = self.var_j.get() or "?"
        s = self.var_s.get() or "?"

        self.lst_results.delete(0, tk.END)
        self.lst_results.insert(
            tk.END,
            f"当前参数：m={m}, n={n}, k={k}, j={j}, s={s}",
        )
        self.lst_results.insert(
            tk.END,
            "算法尚未接入：请在 ui_stub.py 的 run_algorithm() 中加入你的算法调用逻辑。",
        )

        messagebox.showinfo(
            "算法占位",
            "当前 exe 仅包含界面，未接入真正的计算算法。\n\n"
            "请打开 ui_stub.py，在 run_algorithm() 中按注释说明调用你的算法。",
        )


def main():
    root = tk.Tk()
    app = SampleSelectionAppStub(root)
    root.mainloop()


if __name__ == "__main__":
    main()

