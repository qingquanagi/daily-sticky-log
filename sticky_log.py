import json
import sys
import tkinter as tk
from dataclasses import asdict, dataclass
from datetime import date, datetime
from pathlib import Path
from tkinter import filedialog, messagebox, ttk


APP_DIR = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parent
DATA_FILE = APP_DIR / "records.json"

STATUSES = ("待处理", "处理中", "已完成")
TYPES = ("工作", "问题", "想法", "复盘")

COLORS = {
    "app": "#eef1e8",
    "ink": "#18211c",
    "muted": "#687269",
    "panel": "#fffaf0",
    "paper": "#fffef9",
    "line": "#d9d7c7",
    "header": "#24352c",
    "header_sub": "#f1c76b",
    "green": "#2f684e",
    "green_dark": "#1f4937",
    "blue": "#476f99",
    "orange": "#d7663b",
    "danger": "#9b3333",
    "chip": "#eee0ba",
}


@dataclass
class Record:
    id: str
    day: str
    title: str
    detail: str
    type: str
    status: str
    tags: list[str]
    created_at: str


class StickyLogApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("日常问题便签")
        self.geometry("460x740+1080+90")
        self.minsize(420, 620)
        self.configure(bg=COLORS["app"])
        self.attributes("-topmost", True)

        self.records: list[Record] = []
        self.active_status = tk.StringVar(value="全部")
        self.always_on_top = tk.BooleanVar(value=True)
        self.form_collapsed = tk.BooleanVar(value=True)
        self.list_collapsed = tk.BooleanVar(value=False)

        self.day_var = tk.StringVar(value=date.today().isoformat())
        self.type_var = tk.StringVar(value=TYPES[0])
        self.status_var = tk.StringVar(value=STATUSES[0])
        self.title_var = tk.StringVar()
        self.tags_var = tk.StringVar()
        self.search_var = tk.StringVar()

        self._configure_style()
        self._build_ui()
        self._bind_events()
        self._load_records()
        self._render()

    def _configure_style(self) -> None:
        self.option_add("*Font", ("Microsoft YaHei UI", 10))
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TFrame", background=COLORS["app"])
        style.configure("Panel.TFrame", background=COLORS["panel"], relief="flat")
        style.configure("List.TFrame", background=COLORS["panel"], relief="flat")
        style.configure("TLabel", background=COLORS["app"], foreground=COLORS["ink"])
        style.configure("Muted.TLabel", background=COLORS["panel"], foreground=COLORS["muted"], font=("Microsoft YaHei UI", 8))
        style.configure("Title.TLabel", background=COLORS["app"], foreground=COLORS["ink"], font=("Microsoft YaHei UI", 16, "bold"))
        style.configure("Primary.TButton", background=COLORS["green"], foreground="#ffffff", borderwidth=0, padding=(10, 6))
        style.map("Primary.TButton", background=[("active", COLORS["green_dark"])])
        style.configure("Ghost.TButton", background=COLORS["paper"], foreground=COLORS["ink"], borderwidth=1, padding=(8, 5))
        style.map("Ghost.TButton", background=[("active", "#ece5d2")])
        style.configure("Danger.TButton", background="#fff2ee", foreground=COLORS["danger"], borderwidth=1, padding=(8, 5))
        style.configure("TCheckbutton", background=COLORS["app"], foreground=COLORS["ink"])
        style.configure("TRadiobutton", background=COLORS["app"], foreground=COLORS["ink"])

    def _build_ui(self) -> None:
        root = ttk.Frame(self, padding=10)
        root.pack(fill="both", expand=True)

        header = tk.Frame(root, bg=COLORS["header"], highlightthickness=0)
        header.pack(fill="x")
        title_block = tk.Frame(header, bg=COLORS["header"])
        title_block.pack(side="left", fill="x", expand=True, padx=14, pady=12)
        tk.Label(
            title_block,
            text="Daily Sticky Log",
            bg=COLORS["header"],
            fg=COLORS["header_sub"],
            font=("Microsoft YaHei UI", 8, "bold"),
        ).pack(anchor="w")
        tk.Label(
            title_block,
            text="日常问题便签",
            bg=COLORS["header"],
            fg="#ffffff",
            font=("Microsoft YaHei UI", 18, "bold"),
        ).pack(anchor="w")
        tk.Checkbutton(
            header,
            text="置顶",
            variable=self.always_on_top,
            command=self._toggle_topmost,
            bg=COLORS["header"],
            fg="#ffffff",
            selectcolor=COLORS["header"],
            activebackground=COLORS["header"],
            activeforeground="#ffffff",
            relief="flat",
        ).pack(side="right", padx=12)

        summary = ttk.Frame(root)
        summary.pack(fill="x", pady=(8, 6))
        self.total_label = self._summary_cell(summary, "全部", 0)
        self.open_label = self._summary_cell(summary, "待办", 1)
        self.done_label = self._summary_cell(summary, "完成", 2)

        form = tk.Frame(root, bg=COLORS["panel"], highlightthickness=1, highlightbackground="#d2c99d")
        form.pack(fill="x", pady=(0, 8))
        form_header = tk.Frame(form, bg=COLORS["panel"])
        form_header.pack(fill="x", padx=9, pady=7)
        tk.Label(form_header, text="新增记录", bg=COLORS["panel"], fg=COLORS["ink"], font=("Microsoft YaHei UI", 10, "bold")).pack(side="left")
        self.form_toggle_button = ttk.Button(form_header, text="", style="Ghost.TButton", command=self._toggle_form_collapsed)
        self.form_toggle_button.pack(side="right")

        self.form_body = ttk.Frame(form, style="Panel.TFrame", padding=(9, 0, 9, 9))
        form_inner = self.form_body

        row1 = ttk.Frame(form_inner, style="Panel.TFrame")
        row1.pack(fill="x")
        self._labeled(row1, "日期", lambda frame: self._entry(frame, textvariable=self.day_var), 0)
        self._labeled(row1, "类型", lambda frame: self._combo(frame, self.type_var, TYPES), 1)

        ttk.Label(form_inner, text="标题", style="Muted.TLabel").pack(anchor="w", pady=(6, 2))
        self.title_entry = ttk.Entry(form_inner, textvariable=self.title_var)
        self.title_entry.pack(fill="x")

        ttk.Label(form_inner, text="内容", style="Muted.TLabel").pack(anchor="w", pady=(6, 2))
        self.detail_text = tk.Text(form_inner, height=3, wrap="word", bd=1, relief="solid", highlightthickness=0, bg="#fffefa")
        self.detail_text.pack(fill="x")

        row2 = ttk.Frame(form_inner, style="Panel.TFrame")
        row2.pack(fill="x", pady=(7, 0))
        self._labeled(row2, "状态", lambda frame: self._combo(frame, self.status_var, STATUSES), 0)
        self._labeled(row2, "标签", lambda frame: self._entry(frame, textvariable=self.tags_var), 1)

        ttk.Button(form_inner, text="保存记录", style="Primary.TButton", command=self._add_record).pack(fill="x", pady=(8, 0))
        self._sync_form_visibility()

        tools = ttk.Frame(root)
        tools.pack(fill="x", pady=(0, 6))
        self.search_entry = ttk.Entry(tools, textvariable=self.search_var)
        self.search_entry.pack(side="left", fill="x", expand=True)
        for label in ("全部", "待处理", "已完成"):
            ttk.Radiobutton(tools, text=label, value=label, variable=self.active_status, command=self._render).pack(side="left", padx=(6, 0))

        action_row = ttk.Frame(root)
        action_row.pack(fill="x", pady=(0, 6))
        ttk.Label(action_row, text="记录列表", font=("Microsoft YaHei UI", 11, "bold")).pack(side="left")
        self.list_count_label = ttk.Label(action_row, text="0 条", foreground="#6c706c", font=("Microsoft YaHei UI", 9))
        self.list_count_label.pack(side="left", padx=(8, 0))
        ttk.Button(action_row, text="清理已完成", style="Danger.TButton", command=self._clear_done).pack(side="right")
        ttk.Button(action_row, text="导出 Markdown", style="Ghost.TButton", command=self._export_markdown).pack(side="right", padx=(0, 6))
        self.list_toggle_button = ttk.Button(action_row, text="", style="Ghost.TButton", command=self._toggle_list_collapsed)
        self.list_toggle_button.pack(side="right", padx=(0, 6))

        self.list_shell = tk.Frame(root, bg=COLORS["panel"], highlightthickness=1, highlightbackground="#adbcae")
        self.list_shell.pack(fill="both", expand=True)
        self.list_canvas = tk.Canvas(self.list_shell, bg=COLORS["panel"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.list_shell, orient="vertical", command=self.list_canvas.yview)
        self.list_canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.list_canvas.pack(side="left", fill="both", expand=True, padx=(6, 0), pady=6)
        self.list_frame = ttk.Frame(self.list_canvas, style="List.TFrame")
        self.list_window = self.list_canvas.create_window((0, 0), window=self.list_frame, anchor="nw")
        self._sync_list_visibility()

    def _summary_cell(self, parent: ttk.Frame, label: str, column: int) -> ttk.Label:
        accents = (COLORS["blue"], COLORS["orange"], COLORS["green"])
        cell = tk.Frame(parent, bg=COLORS["paper"], highlightthickness=1, highlightbackground=COLORS["line"])
        cell.grid(row=0, column=column, sticky="ew", padx=(0 if column == 0 else 6, 0))
        parent.columnconfigure(column, weight=1)
        tk.Frame(cell, height=3, bg=accents[column]).pack(fill="x")
        number = tk.Label(cell, text="0", bg=COLORS["paper"], fg=COLORS["ink"], font=("Microsoft YaHei UI", 15, "bold"))
        number.pack(anchor="w", padx=10, pady=(5, 0))
        tk.Label(cell, text=label, bg=COLORS["paper"], fg=COLORS["muted"], font=("Microsoft YaHei UI", 8)).pack(anchor="w", padx=10, pady=(0, 6))
        return number

    def _entry(self, parent: ttk.Frame, **kwargs) -> ttk.Entry:
        return ttk.Entry(parent, **kwargs)

    def _combo(self, parent: ttk.Frame, variable: tk.StringVar, values: tuple[str, ...]) -> ttk.Combobox:
        return ttk.Combobox(parent, textvariable=variable, values=values, state="readonly")

    def _labeled(self, parent: ttk.Frame, label: str, widget_factory, column: int) -> None:
        frame = ttk.Frame(parent, style="Panel.TFrame")
        frame.grid(row=0, column=column, sticky="ew", padx=(0 if column == 0 else 8, 0))
        parent.columnconfigure(column, weight=1)
        ttk.Label(frame, text=label, style="Muted.TLabel").pack(anchor="w", pady=(0, 2))
        widget = widget_factory(frame)
        widget.pack(fill="x")

    def _bind_events(self) -> None:
        self.search_var.trace_add("write", lambda *_: self._render())
        self.list_frame.bind("<Configure>", self._update_scroll_region)
        self.list_canvas.bind("<Configure>", self._resize_list_window)
        self.bind("<Control-s>", lambda _event: self._add_record())
        self.bind("<Control-n>", lambda _event: self._expand_form())
        self.bind("<Control-l>", lambda _event: self._toggle_list_collapsed())
        self.bind("<Escape>", lambda _event: self._reset_form())

    def _toggle_topmost(self) -> None:
        self.attributes("-topmost", self.always_on_top.get())

    def _toggle_form_collapsed(self) -> None:
        self.form_collapsed.set(not self.form_collapsed.get())
        self._sync_form_visibility()
        if not self.form_collapsed.get():
            self.after(50, self.title_entry.focus_set)

    def _expand_form(self) -> None:
        if self.form_collapsed.get():
            self.form_collapsed.set(False)
            self._sync_form_visibility()
        self.after(50, self.title_entry.focus_set)

    def _sync_form_visibility(self) -> None:
        if self.form_collapsed.get():
            self.form_body.pack_forget()
            self.form_toggle_button.configure(text="展开新增")
        else:
            self.form_body.pack(fill="x")
            self.form_toggle_button.configure(text="收起新增")

    def _toggle_list_collapsed(self) -> None:
        self.list_collapsed.set(not self.list_collapsed.get())
        self._sync_list_visibility()

    def _sync_list_visibility(self) -> None:
        if self.list_collapsed.get():
            self.list_shell.pack_forget()
            self.list_toggle_button.configure(text="展开列表")
        else:
            self.list_shell.pack(fill="both", expand=True)
            self.list_toggle_button.configure(text="收起列表")

    def _load_records(self) -> None:
        if not DATA_FILE.exists():
            self.records = []
            return
        try:
            raw_records = json.loads(DATA_FILE.read_text(encoding="utf-8"))
            self.records = [Record(**item) for item in raw_records]
        except (OSError, json.JSONDecodeError, TypeError):
            messagebox.showwarning("读取失败", "记录文件损坏或格式异常，已使用空列表启动。")
            self.records = []

    def _save_records(self) -> None:
        DATA_FILE.write_text(
            json.dumps([asdict(record) for record in self.records], ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _add_record(self) -> None:
        title = self.title_var.get().strip()
        if not title:
            messagebox.showinfo("还差标题", "先给这条记录起个标题。")
            return

        record = Record(
            id=datetime.now().strftime("%Y%m%d%H%M%S%f"),
            day=self.day_var.get().strip() or date.today().isoformat(),
            title=title,
            detail=self.detail_text.get("1.0", "end").strip(),
            type=self.type_var.get(),
            status=self.status_var.get(),
            tags=self._parse_tags(self.tags_var.get()),
            created_at=datetime.now().isoformat(timespec="seconds"),
        )
        self.records.insert(0, record)
        self._save_records()
        self._reset_form()
        self._render()

    def _reset_form(self) -> None:
        self.day_var.set(date.today().isoformat())
        self.type_var.set(TYPES[0])
        self.status_var.set(STATUSES[0])
        self.title_var.set("")
        self.tags_var.set("")
        self.detail_text.delete("1.0", "end")

    def _parse_tags(self, value: str) -> list[str]:
        normalized = value.replace("，", ",").replace(" ", ",")
        return [tag.strip() for tag in normalized.split(",") if tag.strip()][:6]

    def _visible_records(self) -> list[Record]:
        keyword = self.search_var.get().strip().lower()
        status = self.active_status.get()
        records = [record for record in self.records if status == "全部" or record.status == status]
        if keyword:
            records = [
                record
                for record in records
                if keyword in " ".join([record.day, record.title, record.detail, record.type, record.status, *record.tags]).lower()
            ]
        return sorted(records, key=lambda item: (item.day, item.created_at), reverse=True)

    def _render(self) -> None:
        for child in self.list_frame.winfo_children():
            child.destroy()

        self.total_label.configure(text=str(len(self.records)))
        self.open_label.configure(text=str(sum(1 for record in self.records if record.status != "已完成")))
        self.done_label.configure(text=str(sum(1 for record in self.records if record.status == "已完成")))

        records = self._visible_records()
        self.list_count_label.configure(text=f"{len(records)} 条")
        if not records:
            empty = tk.Label(
                self.list_frame,
                text="还没有记录\n把今天完成的事、卡住的问题、下一步写下来。",
                bg=COLORS["panel"],
                fg=COLORS["muted"],
                justify="center",
                pady=42,
                font=("Microsoft YaHei UI", 10),
            )
            empty.pack(fill="x", pady=10)
            return

        last_day = ""
        for record in records:
            if record.day != last_day:
                tk.Label(
                    self.list_frame,
                    text=record.day,
                    bg="#e7dec2",
                    fg="#5f604f",
                    padx=10,
                    pady=3,
                    font=("Microsoft YaHei UI", 8, "bold"),
                ).pack(anchor="w", pady=(4, 4))
                last_day = record.day
            self._record_card(record)

    def _record_card(self, record: Record) -> None:
        status_colors = {
            "待处理": "#d7663b",
            "处理中": "#476f99",
            "已完成": "#2f684e",
        }
        card = tk.Frame(self.list_frame, bg=COLORS["paper"], highlightthickness=1, highlightbackground="#d0d4c8")
        card.pack(fill="x", pady=6, padx=(0, 6))
        tk.Frame(card, width=5, bg=status_colors.get(record.status, "#2f684e")).pack(side="left", fill="y")
        body = tk.Frame(card, bg=COLORS["paper"])
        body.pack(side="left", fill="both", expand=True, padx=12, pady=10)

        meta = f"{record.type} · {record.status}"
        tk.Label(
            body,
            text=meta,
            bg="#e8efe7",
            fg=COLORS["green_dark"],
            padx=7,
            pady=2,
            font=("Microsoft YaHei UI", 8, "bold"),
        ).pack(anchor="w")
        title_font = ("Microsoft YaHei UI", 12, "overstrike" if record.status == "已完成" else "bold")
        tk.Label(body, text=record.title, bg=COLORS["paper"], fg=COLORS["ink"], font=title_font, wraplength=300, justify="left").pack(anchor="w", pady=(6, 0))
        detail = record.detail or "无补充内容"
        tk.Label(body, text=detail, bg=COLORS["paper"], fg=COLORS["muted"], wraplength=300, justify="left").pack(anchor="w", pady=(4, 0))
        if record.tags:
            tk.Label(
                body,
                text=" ".join(f"#{tag}" for tag in record.tags),
                bg=COLORS["chip"],
                fg="#6f5525",
                padx=7,
                pady=2,
                font=("Microsoft YaHei UI", 8),
            ).pack(anchor="w", pady=(7, 0))

        actions = tk.Frame(card, bg=COLORS["paper"])
        actions.pack(side="right", padx=(0, 8), pady=8)
        next_label = "重开" if record.status == "已完成" else "完成"
        ttk.Button(actions, text=next_label, style="Ghost.TButton", command=lambda: self._toggle_done(record.id)).pack(fill="x")
        ttk.Button(actions, text="删除", style="Danger.TButton", command=lambda: self._delete_record(record.id)).pack(fill="x", pady=(6, 0))

    def _toggle_done(self, record_id: str) -> None:
        for record in self.records:
            if record.id == record_id:
                record.status = "待处理" if record.status == "已完成" else "已完成"
                break
        self._save_records()
        self._render()

    def _delete_record(self, record_id: str) -> None:
        if not messagebox.askyesno("确认删除", "确定删除这条记录吗？"):
            return
        self.records = [record for record in self.records if record.id != record_id]
        self._save_records()
        self._render()

    def _clear_done(self) -> None:
        if not any(record.status == "已完成" for record in self.records):
            return
        if not messagebox.askyesno("确认清理", "确定清理所有已完成记录吗？"):
            return
        self.records = [record for record in self.records if record.status != "已完成"]
        self._save_records()
        self._render()

    def _format_markdown(self, records: list[Record]) -> str:
        lines = ["# 日常问题记录", ""]
        for record in records:
            detail = record.detail or "无"
            if record.tags:
                detail = f"{detail}\n标签：{' '.join(f'#{tag}' for tag in record.tags)}"
            lines.extend(
                [
                    f"## 日期：{record.day}：{record.type}-{record.status}",
                    f"## 标题：{record.title}",
                    f"## 内容：{detail}",
                    "",
                ]
            )
        return "\n".join(lines)

    def _export_markdown(self) -> None:
        records = self._visible_records()
        if not records:
            messagebox.showinfo("没有内容", "当前筛选下没有可导出的记录。")
            return

        target = filedialog.asksaveasfilename(
            title="导出 Markdown",
            defaultextension=".md",
            initialfile=f"daily-work-log-{date.today().isoformat()}.md",
            filetypes=(("Markdown", "*.md"), ("Text", "*.txt"), ("All files", "*.*")),
        )
        if not target:
            return

        Path(target).write_text(self._format_markdown(records), encoding="utf-8")
        messagebox.showinfo("导出完成", f"已导出到：\n{target}")

    def _update_scroll_region(self, _event: tk.Event) -> None:
        self.list_canvas.configure(scrollregion=self.list_canvas.bbox("all"))

    def _resize_list_window(self, event: tk.Event) -> None:
        self.list_canvas.itemconfigure(self.list_window, width=event.width)


if __name__ == "__main__":
    app = StickyLogApp()
    app.mainloop()
