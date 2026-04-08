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
        self.main_window = toga.MainWindow(
            title=self.name if hasattr(self, 'name') else "Optimal Sample Selection System")

        # Set window size large enough for development
        self.main_window.size = (1400, 900)

        self.results_dir = os.path.join(os.path.dirname(__file__), "results")
        os.makedirs(self.results_dir, exist_ok=True)

        self.container = toga.OptionContainer(style=Pack(flex=1))
        self.calc_box = self.create_calc_page()
        self.container.content.append("Run", self.calc_box)
        self.history_box = self.create_history_page()
        self.container.content.append("History", self.history_box)

        self.main_window.content = self.container
        self.main_window.show()
        self.create_about_menu()
        self.refresh_history()

    def create_calc_page(self):
        main_box = toga.Box(style=Pack(direction=COLUMN, padding=5))

        params_box = toga.Box(style=Pack(direction=COLUMN, padding=1))

        # First row parameters
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

        # Second row parameters
        row2 = toga.Box(style=Pack(direction=ROW, padding=2))
        j_box = toga.Box(style=Pack(direction=COLUMN, flex=1))
        j_box.add(toga.Label("j (s≤j≤k)", style=Pack(font_size=12)))
        self.j_input = toga.TextInput(placeholder="j value")
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

        # Mode selection buttons (vertical layout)
        mode_button_box = toga.Box(style=Pack(direction=COLUMN, padding=2))
        
        self.random_btn = toga.Button(
            "Auto Generate",
            on_press=self.set_random_mode,
            style=Pack(flex=1, padding=2, height=50)
        )
        self.manual_btn = toga.Button(
            "Manual Input",
            on_press=self.set_manual_mode,
            style=Pack(flex=1, padding=2, height=50)
        )
        mode_button_box.add(self.random_btn)
        mode_button_box.add(self.manual_btn)
        main_box.add(mode_button_box)

        # Manual input area
        self.manual_box = toga.Box(style=Pack(direction=COLUMN, padding=2))
        self.manual_box.add(toga.Label("Manual sample list (only used in manual mode):"))
        self.samples_input = toga.MultilineTextInput(
            placeholder="Example: A1, A2, A3,.",
            style=Pack(height=50)
        )
        self.manual_box.add(self.samples_input)
        self.manual_box.enabled = False
        main_box.add(self.manual_box)

        # Special sample indices
        special_box = toga.Box(style=Pack(direction=COLUMN, padding=2))
        special_box.add(toga.Label("Key sample indices (1~n, total j values):"))
        self.special_input = toga.TextInput(
            placeholder="Leave blank to use first j samples by default"
        )
        special_box.add(self.special_input)
        main_box.add(special_box)

        # Action buttons (vertical layout)
        action_button_box = toga.Box(style=Pack(direction=COLUMN, padding=2))
        
        run_button = toga.Button(
            "Run Enumeration",
            on_press=self.run_algorithm,
            style=Pack(flex=1, padding=3, height=50)
        )
        clear_button = toga.Button(
            "Clear Inputs",
            on_press=self.clear_inputs,
            style=Pack(flex=1, padding=3, height=40)
        )
        action_button_box.add(run_button)
        action_button_box.add(clear_button)
        main_box.add(action_button_box)

        # Result display area
        result_label = toga.Label("Current Run Results",
                                  style=Pack(font_size=13, font_weight="bold", padding=(5, 0, 2, 0)))
        main_box.add(result_label)
        self.result_count = toga.Label("0 groups", style=Pack(font_size=11, color="#1a73e8"))
        main_box.add(self.result_count)
        self.result_list = toga.MultilineTextInput(readonly=True, style=Pack(flex=1))
        main_box.add(self.result_list)

        # Default to random (auto) mode
        self.mode = "random"
        self.random_btn.style.background_color = "#1a73e8"
        self.random_btn.style.color = "white"
        # Reset manual button style (remove any existing custom style)
        try:
            del self.manual_btn.style.background_color
        except (AttributeError, KeyError):
            pass
        try:
            del self.manual_btn.style.color
        except (AttributeError, KeyError):
            pass

        return main_box

    def create_history_page(self):
        history_box = toga.Box(style=Pack(direction=COLUMN, padding=10))

        title_box = toga.Box(style=Pack(direction=ROW, padding=5))
        title_label = toga.Label("History Results", style=Pack(font_size=16, font_weight="bold"))
        title_box.add(title_label)
        refresh_btn = toga.Button("Refresh", on_press=self.refresh_history, style=Pack(padding=5))
        title_box.add(refresh_btn)
        clear_btn = toga.Button("Delete All", on_press=self.clear_all_history, style=Pack(padding=5))
        title_box.add(clear_btn)
        history_box.add(title_box)

        self.history_list = toga.Table(
            headings=["Time", "Parameters (m,n,k,j,s,t)", "Result Count", "Filename"],
            multiple_select=False,
            style=Pack(flex=1, padding=5)
        )
        self.history_list.on_select = self.on_history_select
        history_box.add(self.history_list)

        button_box = toga.Box(style=Pack(direction=ROW, padding=5))
        view_btn = toga.Button("View Selected", on_press=self.view_selected_history, style=Pack(flex=1, padding=5))
        button_box.add(view_btn)
        delete_btn = toga.Button("Delete Selected", on_press=self.delete_selected_history,
                                 style=Pack(flex=1, padding=5))
        button_box.add(delete_btn)
        history_box.add(button_box)

        path_label = toga.Label(f"Results directory: {self.results_dir}",
                                style=Pack(font_size=10, color="#666666", padding=5))
        history_box.add(path_label)

        return history_box

    def on_history_select(self, widget, **kwargs):
        pass

    def create_about_menu(self):
        about_text = """
Optimal Sample Selection System
Version 1.0.0

AI Course Project - CS360/SE360

Features:
- Select n samples from m samples
- Form k-tuples from n samples
- Ensure each j-tuple contains at least s key samples
- Support t parameter to control coverage count

Development Team:
Xu Yanxi
Xia Yutong
xxx
xxx

Project URL:
https://github.com/yourname/sample_selector

License: MIT License
"""

        def show_about(widget):
            self.main_window.info_dialog("About", about_text.strip())

        about_cmd = toga.Command(
            show_about,
            text="About",
            tooltip="Show about information",
            shortcut=None,
            group=toga.Group.HELP
        )
        self.commands.add(about_cmd)

    def set_random_mode(self, widget):
        """Force switch to auto-generate mode."""
        self.mode = "random"
        self.manual_box.enabled = False
        # Set random button as active (blue)
        self.random_btn.style.background_color = "#1a73e8"
        self.random_btn.style.color = "white"
        # Reset manual button to default style
        try:
            del self.manual_btn.style.background_color
        except (AttributeError, KeyError):
            pass
        try:
            del self.manual_btn.style.color
        except (AttributeError, KeyError):
            pass

    def set_manual_mode(self, widget):
        """Force switch to manual input mode."""
        self.mode = "manual"
        self.manual_box.enabled = True
        # Set manual button as active (blue)
        self.manual_btn.style.background_color = "#1a73e8"
        self.manual_btn.style.color = "white"
        # Reset random button to default style
        try:
            del self.random_btn.style.background_color
        except (AttributeError, KeyError):
            pass
        try:
            del self.random_btn.style.color
        except (AttributeError, KeyError):
            pass

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
        self.result_count.text = "0 groups"
        # Reset to auto mode
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
            errors.append("All parameters must be integers")
            return None, None, None, None, None, None, errors

        if not m or m < 1 or m > 10000:
            errors.append("m should be between 1 and 10000")
        if not n or n < 7 or n > 25:
            errors.append("n should be between 7 and 25")
        if not k or k < 4 or k > 7:
            errors.append("k should be between 4 and 7")
        if not j:
            errors.append("j cannot be empty")
        if not s or s < 3 or s > 7:
            errors.append("s should be between 3 and 7")
        if t < 1:
            errors.append("t must be ≥ 1")

        if j and s and j < s:
            errors.append("Must satisfy j ≥ s")
        if j and k and j > k:
            errors.append("Must satisfy j ≤ k")
        if k and n and k > n:
            errors.append("Must satisfy k ≤ n")

        return m, n, k, j, s, t, errors

    def run_algorithm(self, widget):
        m, n, k, j, s, t, errors = self.validate_inputs()
        if errors:
            self.main_window.error_dialog("Input Error", "\n".join(errors))
            return

        try:
            if self.mode == "manual":
                samples = parse_samples(self.samples_input.value, n, "manual")
            else:
                samples = parse_samples("", n, "random")
            special_indices = parse_special_indices(self.special_input.value, n, j)
        except ValueError as e:
            self.main_window.error_dialog("Input Error", str(e))
            return

        start_time = time.time()
        try:
            groups = enumerate_groups(samples, special_indices, m, n, k, j, s, t)
        except Exception as e:
            self.main_window.error_dialog("Algorithm Error", f"Calculation failed: {str(e)}")
            return
        elapsed_ms = int((time.time() - start_time) * 1000)

        self.result_count.text = f"{len(groups)} groups"
        result_text = ""
        for idx, g in enumerate(groups, 1):
            result_text += f"#{idx}: {', '.join(g)}\n"
        self.result_list.value = result_text

        params = {"m": m, "n": n, "k": k, "j": j, "s": s, "t": t}
        self.save_result(params, samples, special_indices, groups, elapsed_ms)

        self.main_window.info_dialog("Calculation Complete",
                                     f"Found {len(groups)} results\nTime: {elapsed_ms} ms\nResults saved")
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
                param_str = f"{params.get('m', '?')},{params.get('n', '?')},{params.get('k', '?')},{params.get('j', '?')},{params.get('s', '?')},{params.get('t', 1)}"
                count = len(data.get("groups", []))
                items.append((timestamp, param_str, str(count), name))
            except Exception:
                continue
        items.sort(reverse=True)
        for item in items:
            self.history_list.data.append(item)

    def view_selected_history(self, widget=None):
        selection = self.history_list.selection
        if selection is None:
            self.main_window.info_dialog("Info", "Please select a record first")
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

        if filename is None and hasattr(selection, 'filename'):
            filename = selection.filename

        if filename is None:
            self.main_window.error_dialog("Error", "Unable to get filename")
            return

        path = os.path.join(self.results_dir, filename)
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.show_history_detail(data, filename)
        except Exception as e:
            self.main_window.error_dialog("Error", f"Failed to read file: {e}")

    def show_history_detail(self, data, filename):
        params = data.get("params", {})
        groups = data.get("groups", [])

        param_text = f"Parameters: m={params.get('m')}, n={params.get('n')}, k={params.get('k')}, j={params.get('j')}, s={params.get('s')}, t={params.get('t', 1)}"
        time_text = f"Time: {data.get('timestamp', '')}"
        count_text = f"Result count: {len(groups)} groups"

        result_text = ""
        for idx, g in enumerate(groups, 1):
            result_text += f"#{idx}: {', '.join(g)}\n"

        full_text = f"{param_text}\n{time_text}\n{count_text}\n\nResults:\n{result_text}"
        self.main_window.info_dialog(f"Details: {filename}", full_text)

    def delete_selected_history(self, widget=None):
        selection = self.history_list.selection
        if selection is None:
            self.main_window.info_dialog("Info", "Please select a record first")
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

        if filename is None and hasattr(selection, 'filename'):
            filename = selection.filename

        if filename is None:
            self.main_window.error_dialog("Error", "Unable to get filename")
            return

        def on_confirm(widget, result):
            if result:
                path = os.path.join(self.results_dir, filename)
                try:
                    os.remove(path)
                    self.refresh_history()
                    self.main_window.info_dialog("Success", "File deleted")
                except Exception as e:
                    self.main_window.error_dialog("Error", f"Deletion failed: {e}")

        self.main_window.confirm_dialog("Confirm Deletion", f"Are you sure you want to delete file '{filename}'?",
                                        on_confirm)

    def clear_all_history(self, widget=None):
        if not os.path.isdir(self.results_dir):
            return
        files = [f for f in os.listdir(self.results_dir) if f.endswith('.json')]
        count = len(files)
        if count == 0:
            self.main_window.info_dialog("Info", "No history records")
            return

        def on_confirm(widget, result):
            if result:
                deleted = 0
                for name in files:
                    try:
                        os.remove(os.path.join(self.results_dir, name))
                        deleted += 1
                    except Exception as e:
                        print(f"Failed to delete {name}: {e}")
                self.refresh_history()
                if deleted > 0:
                    self.main_window.info_dialog("Success", f"Deleted {deleted} files")

        self.main_window.confirm_dialog("Confirm Clear All",
                                        f"Are you sure you want to delete all {count} history files? This action cannot be undone.",
                                        on_confirm)


def main():
    return SampleSelector("Optimal Sample Selection System", "com.yourname.sampleselector")
