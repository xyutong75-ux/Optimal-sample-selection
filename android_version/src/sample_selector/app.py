# src/sample_selector/app.py

import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW
import json
import os
import time
from datetime import datetime
from .algorithms import enumerate_groups, parse_samples, parse_special_indices


class SampleSelector(toga.App):
    def startup(self):
        self.main_window = toga.MainWindow(title=self.name if hasattr(self, 'name') else "最优样本选择系统")
        
        # 窗口大小设为足够大，方便开发
        self.main_window.size = (1300, 900)
        
        self.results_dir = os.path.join(os.path.dirname(__file__), "results")
        os.makedirs(self.results_dir, exist_ok=True)
        
        self.container = toga.OptionContainer(style=Pack(flex=1))
        self.calc_box = self.create_calc_page()
        self.container.content.append("运算", self.calc_box)
        self.history_box = self.create_history_page()
        self.container.content.append("历史记录", self.history_box)
        
        self.main_window.content = self.container
        self.main_window.show()
        # 在 show() 之后添加 About 菜单
        self.create_about_menu()
        self.refresh_history()
    
    def create_calc_page(self):
        main_box = toga.Box(style=Pack(direction=COLUMN, padding=5))
        
        # 标题已删除（因为有重复）
        
        params_box = toga.Box(style=Pack(direction=COLUMN, padding=1))
        
        # 第一行参数
        row1 = toga.Box(style=Pack(direction=ROW, padding=2))
        m_box = toga.Box(style=Pack(direction=COLUMN, flex=1))
        m_box.add(toga.Label("m (45-54)", style=Pack(font_size=12)))
        self.m_input = toga.TextInput(placeholder="45-54")
        m_box.add(self.m_input)
        row1.add(m_box)
        
        n_box = toga.Box(style=Pack(direction=COLUMN, flex=1))
        n_box.add(toga.Label("n (7-25)", style=Pack(font_size=12)))
        self.n_input = toga.TextInput(placeholder="7-25")
        n_box.add(self.n_input)
        row1.add(n_box)
        
        k_box = toga.Box(style=Pack(direction=COLUMN, flex=1))
        k_box.add(toga.Label("k (4-7)", style=Pack(font_size=12)))
        self.k_input = toga.TextInput(placeholder="4-7")
        k_box.add(self.k_input)
        row1.add(k_box)
        params_box.add(row1)
        
        # 第二行参数
        row2 = toga.Box(style=Pack(direction=ROW, padding=2))
        j_box = toga.Box(style=Pack(direction=COLUMN, flex=1))
        j_box.add(toga.Label("j (s≤j≤k)", style=Pack(font_size=12)))
        self.j_input = toga.TextInput(placeholder="j值")
        j_box.add(self.j_input)
        row2.add(j_box)
        
        s_box = toga.Box(style=Pack(direction=COLUMN, flex=1))
        s_box.add(toga.Label("s (3-7)", style=Pack(font_size=12)))
        self.s_input = toga.TextInput(placeholder="3-7")
        s_box.add(self.s_input)
        row2.add(s_box)
        
        t_box = toga.Box(style=Pack(direction=COLUMN, flex=1))
        t_box.add(toga.Label("t (≥1)", style=Pack(font_size=12)))
        self.t_input = toga.TextInput(placeholder="1", value="1")
        t_box.add(self.t_input)
        row2.add(t_box)
        params_box.add(row2)
        main_box.add(params_box)
        
        # 样本模式选择
        mode_box = toga.Box(style=Pack(direction=ROW, padding=2))
        self.random_btn = toga.Button("随机生成", on_press=self.set_random_mode, style=Pack(flex=1, padding=2))
        self.manual_btn = toga.Button("手动输入", on_press=self.set_manual_mode, style=Pack(flex=1, padding=2))
        mode_box.add(self.random_btn)
        mode_box.add(self.manual_btn)
        main_box.add(mode_box)
        
        # 手动输入区域
        self.manual_box = toga.Box(style=Pack(direction=COLUMN, padding=2))
        self.manual_box.add(toga.Label("手动输入样本（用逗号/空格分隔）:"))
        self.samples_input = toga.MultilineTextInput(placeholder="例如: S1, S2, S3, ...", style=Pack(height=50))
        self.manual_box.add(self.samples_input)
        self.manual_box.enabled = False
        main_box.add(self.manual_box)
        
        # 重点样本序号
        special_box = toga.Box(style=Pack(direction=COLUMN, padding=2))
        special_box.add(toga.Label("重点样本序号（1~n，j个，用逗号分隔，留空默认前j个）:"))
        self.special_input = toga.TextInput(placeholder="例如: 1,2,3")
        special_box.add(self.special_input)
        main_box.add(special_box)
        
        # 按钮区域
        button_box = toga.Box(style=Pack(direction=ROW, padding=2))
        run_button = toga.Button("运行算法", on_press=self.run_algorithm, style=Pack(flex=1, padding=3))
        button_box.add(run_button)
        clear_button = toga.Button("清空", on_press=self.clear_inputs, style=Pack(flex=1, padding=3))
        button_box.add(clear_button)
        main_box.add(button_box)
        
        # 结果显示区域
        result_label = toga.Label("计算结果:", style=Pack(font_size=13, font_weight="bold", padding=(5, 0, 2, 0)))
        main_box.add(result_label)
        self.result_count = toga.Label("0 组", style=Pack(font_size=11, color="#1a73e8"))
        main_box.add(self.result_count)
        self.result_list = toga.MultilineTextInput(readonly=True, style=Pack(flex=1))
        main_box.add(self.result_list)
        
        self.mode = "random"
        self.random_btn.style.background_color = "#1a73e8"
        self.random_btn.style.color = "white"
        
        return main_box
    
    def create_history_page(self):
        history_box = toga.Box(style=Pack(direction=COLUMN, padding=10))
        
        title_box = toga.Box(style=Pack(direction=ROW, padding=5))
        title_label = toga.Label("历史记录", style=Pack(font_size=16, font_weight="bold"))
        title_box.add(title_label)
        refresh_btn = toga.Button("刷新", on_press=self.refresh_history, style=Pack(padding=5))
        title_box.add(refresh_btn)
        clear_btn = toga.Button("清空全部", on_press=self.clear_all_history, style=Pack(padding=5))
        title_box.add(clear_btn)
        history_box.add(title_box)
        
        self.history_list = toga.Table(
            headings=["时间", "参数 (m,n,k,j,s,t)", "结果数", "文件名"],
            multiple_select=False,
            style=Pack(flex=1, padding=5)
        )
        self.history_list.on_select = self.on_history_select
        history_box.add(self.history_list)
        
        button_box = toga.Box(style=Pack(direction=ROW, padding=5))
        view_btn = toga.Button("查看选中", on_press=self.view_selected_history, style=Pack(flex=1, padding=5))
        button_box.add(view_btn)
        delete_btn = toga.Button("删除选中", on_press=self.delete_selected_history, style=Pack(flex=1, padding=5))
        button_box.add(delete_btn)
        history_box.add(button_box)
        
        path_label = toga.Label(f"结果保存目录: {self.results_dir}", style=Pack(font_size=10, color="#666666", padding=5))
        history_box.add(path_label)
        
        return history_box
    
    def on_history_select(self, widget, **kwargs):
        pass
    
    def create_about_menu(self):
        """创建关于菜单"""
        # 创建关于对话框的内容
        about_text = """
最优样本选择系统
版本 1.0.0

人工智能课程项目 - CS360/SE360

功能说明：
- 从 m 个样本中选出 n 个
- 从 n 个样本中组成 k 元组
- 确保每个 j 元组中至少有 s 个重点样本
- 支持 t 参数控制覆盖次数

开发团队：
许彦熙
夏雨桐
xxx
xxx

项目地址：
https://github.com/yourname/sample_selector

许可证：MIT License
"""
        
        # 创建关于命令
        def show_about(widget):
            self.main_window.info_dialog("关于", about_text.strip())
        
        # 添加到帮助菜单
        about_cmd = toga.Command(
            show_about,
            text="关于",
            tooltip="显示关于信息",
            shortcut=None,
            group=toga.Group.HELP  # 放在帮助菜单组
        )
        self.commands.add(about_cmd)

    def set_random_mode(self, widget):
        self.mode = "random"
        self.manual_box.enabled = False
        self.random_btn.style.background_color = "#1a73e8"
        self.random_btn.style.color = "white"
        self.manual_btn.style.background_color = None
        self.manual_btn.style.color = None
    
    def set_manual_mode(self, widget):
        self.mode = "manual"
        self.manual_box.enabled = True
        self.manual_btn.style.background_color = "#1a73e8"
        self.manual_btn.style.color = "white"
        self.random_btn.style.background_color = None
        self.random_btn.style.color = None
    
    def clear_inputs(self, widget):
        self.m_input.value = ""
        self.n_input.value = ""
        self.k_input.value = ""
        self.j_input.value = ""
        self.s_input.value = ""
        self.t_input.value = "1"
        self.samples_input.value = ""
        self.special_input.value = ""
        self.result_list.value = ""
        self.result_count.text = "0 组"
        self.set_random_mode(None)
    
    def validate_inputs(self):
        errors = []
        try:
            m = int(self.m_input.value) if self.m_input.value else None
            n = int(self.n_input.value) if self.n_input.value else None
            k = int(self.k_input.value) if self.k_input.value else None
            j = int(self.j_input.value) if self.j_input.value else None
            s = int(self.s_input.value) if self.s_input.value else None
            t = int(self.t_input.value) if self.t_input.value else 1
        except ValueError:
            errors.append("所有参数必须是整数")
            return None, None, None, None, None, None, errors
        
        if not m or m < 1 or m > 10000:
            errors.append("m 应在 1-10000 之间")
        if not n or n < 7 or n > 25:
            errors.append("n 应在 7-25 之间")
        if not k or k < 4 or k > 7:
            errors.append("k 应在 4-7 之间")
        if not j:
            errors.append("j 不能为空")
        if not s or s < 3 or s > 7:
            errors.append("s 应在 3-7 之间")
        if t < 1:
            errors.append("t 必须 ≥ 1")
        
        if j and s and j < s:
            errors.append("必须满足 j ≥ s")
        if j and k and j > k:
            errors.append("必须满足 j ≤ k")
        if k and n and k > n:
            errors.append("必须满足 k ≤ n")
        
        return m, n, k, j, s, t, errors
    
    def run_algorithm(self, widget):
        m, n, k, j, s, t, errors = self.validate_inputs()
        if errors:
            self.main_window.error_dialog("输入错误", "\n".join(errors))
            return
        
        try:
            if self.mode == "manual":
                samples = parse_samples(self.samples_input.value, n, "manual")
            else:
                samples = parse_samples("", n, "random")
            special_indices = parse_special_indices(self.special_input.value, n, j)
        except ValueError as e:
            self.main_window.error_dialog("输入错误", str(e))
            return
        
        start_time = time.time()
        try:
            groups = enumerate_groups(samples, special_indices, m, n, k, j, s, t)
        except Exception as e:
            self.main_window.error_dialog("算法错误", f"计算失败：{str(e)}")
            return
        elapsed_ms = int((time.time() - start_time) * 1000)
        
        self.result_count.text = f"{len(groups)} 组"
        result_text = ""
        for idx, g in enumerate(groups, 1):
            result_text += f"#{idx}: {', '.join(g)}\n"
        self.result_list.value = result_text
        
        params = {"m": m, "n": n, "k": k, "j": j, "s": s, "t": t}
        self.save_result(params, samples, special_indices, groups, elapsed_ms)
        
        self.main_window.info_dialog("计算完成", f"找到 {len(groups)} 组结果\n耗时：{elapsed_ms} ms\n结果已保存")
        self.refresh_history()
    
    def save_result(self, params, samples, special_indices, groups, elapsed_ms):
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        filename = f"result_{timestamp}.json"
        path = os.path.join(self.results_dir, filename)
        data = {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "params": params,
            "samples": samples,
            "special_indices": special_indices,
            "groups": groups,
            "elapsed_ms": elapsed_ms
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return filename
    
    def refresh_history(self, widget=None):
        self.history_list.data.clear()
        if not os.path.isdir(self.results_dir):
            return
        items = []
        for name in sorted(os.listdir(self.results_dir), reverse=True):
            if not name.endswith(".json"):
                continue
            path = os.path.join(self.results_dir, name)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                params = data.get("params", {})
                timestamp = data.get("timestamp", "").replace("T", " ")[:19]
                param_str = f"{params.get('m','?')},{params.get('n','?')},{params.get('k','?')},{params.get('j','?')},{params.get('s','?')},{params.get('t',1)}"
                count = len(data.get("groups", []))
                items.append((timestamp, param_str, str(count), name))
            except Exception:
                continue
        items.sort(reverse=True)
        for item in items:
            self.history_list.data.append(item)
    
    def view_selected_history(self, widget=None):
        """查看选中的历史记录"""
        selection = self.history_list.selection
        if selection is None:
            self.main_window.info_dialog("提示", "请先选中一条记录")
            return

        filename = None

        # 尝试从 selection 中获取文件名
        if hasattr(selection, '__getitem__'):
            try:
                filename = selection[3]  # 索引3对应文件名
            except (IndexError, TypeError, KeyError):
                pass

        if filename is None:
            try:
                idx = int(selection)
                if 0 <= idx < len(self.history_list.data):
                    row = self.history_list.data[idx]
                    if len(row) >= 4:
                        filename = row[3]
            except (ValueError, TypeError, IndexError):
                pass

        if filename is None and hasattr(selection, '文件名'):
            filename = selection.文件名

        if filename is None:
            self.main_window.error_dialog("错误", "无法获取文件名")
            return

        path = os.path.join(self.results_dir, filename)
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.show_history_detail(data, filename)
        except Exception as e:
            self.main_window.error_dialog("错误", f"读取文件失败: {e}")
    
    def show_history_detail(self, data, filename):
        """显示历史记录详情（使用信息对话框，兼容Android）"""
        params = data.get("params", {})
        groups = data.get("groups", [])
        
        # 构建显示文本
        param_text = f"参数: m={params.get('m')}, n={params.get('n')}, k={params.get('k')}, j={params.get('j')}, s={params.get('s')}, t={params.get('t',1)}"
        time_text = f"时间: {data.get('timestamp', '')}"
        count_text = f"结果数: {len(groups)} 组"
        
        result_text = ""
        for idx, g in enumerate(groups, 1):
            result_text += f"#{idx}: {', '.join(g)}\n"
        
        full_text = f"{param_text}\n{time_text}\n{count_text}\n\n结果:\n{result_text}"
        
        # 使用 InfoDialog 显示
        self.main_window.info_dialog(f"详情: {filename}", full_text)
    
    def delete_selected_history(self, widget=None):
        """删除选中的历史记录"""
        selection = self.history_list.selection
        if selection is None:
            self.main_window.info_dialog("提示", "请先选中一条记录")
            return

        filename = None

        if hasattr(selection, '__getitem__'):
            try:
                filename = selection[3]
            except (IndexError, TypeError, KeyError):
                pass

        if filename is None:
            try:
                idx = int(selection)
                if 0 <= idx < len(self.history_list.data):
                    row = self.history_list.data[idx]
                    if len(row) >= 4:
                        filename = row[3]
            except (ValueError, TypeError, IndexError):
                pass

        if filename is None and hasattr(selection, '文件名'):
            filename = selection.文件名

        if filename is None:
            self.main_window.error_dialog("错误", "无法获取文件名")
            return

        def on_confirm(widget, result):
            if result:
                path = os.path.join(self.results_dir, filename)
                try:
                    os.remove(path)
                    self.refresh_history()
                    self.main_window.info_dialog("成功", "文件已删除")
                except Exception as e:
                    self.main_window.error_dialog("错误", f"删除失败: {e}")

        self.main_window.confirm_dialog("确认删除", f"确定要删除文件 '{filename}' 吗？", on_confirm)
    
    def clear_all_history(self, widget=None):
        if not os.path.isdir(self.results_dir):
            return
        files = [f for f in os.listdir(self.results_dir) if f.endswith('.json')]
        count = len(files)
        if count == 0:
            self.main_window.info_dialog("提示", "没有历史记录")
            return
        
        def on_confirm(widget, result):
            if result:
                deleted = 0
                for name in files:
                    try:
                        os.remove(os.path.join(self.results_dir, name))
                        deleted += 1
                    except Exception as e:
                        print(f"删除失败 {name}: {e}")
                self.refresh_history()
                if deleted > 0:
                    self.main_window.info_dialog("成功", f"已删除 {deleted} 个文件")
        
        self.main_window.confirm_dialog("确认清空", f"确定要删除全部 {count} 个历史记录文件吗？此操作不可恢复。", on_confirm)


def main():
    return SampleSelector("最优样本选择系统", "com.yourname.sampleselector")