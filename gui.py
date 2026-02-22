import os
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from star_trails import create_star_trail, create_star_trail_video, FOURCC_MAP


class StarTrailApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Star Trails - 星轨合成工具")
        self.root.resizable(False, False)

        self.input_files = []
        self.running = False

        self._build_ui()

    def _build_ui(self):
        pad = {"padx": 8, "pady": 4}

        # === 输入 ===
        input_frame = ttk.LabelFrame(self.root, text="输入", padding=8)
        input_frame.grid(row=0, column=0, sticky="ew", **pad)
        input_frame.columnconfigure(1, weight=1)

        ttk.Label(input_frame, text="图像目录:").grid(row=0, column=0, sticky="w")
        self.input_var = tk.StringVar()
        ttk.Entry(input_frame, textvariable=self.input_var, width=50).grid(row=0, column=1, sticky="ew", padx=(4, 4))
        ttk.Button(input_frame, text="浏览...", command=self._browse_input).grid(row=0, column=2)

        ttk.Label(input_frame, text="文件格式:").grid(row=1, column=0, sticky="w", pady=(4, 0))
        self.pattern_var = tk.StringVar(value="*.jpg")
        pattern_combo = ttk.Combobox(input_frame, textvariable=self.pattern_var, width=10,
                                     values=["*.jpg", "*.jpeg", "*.png", "*.tif", "*.tiff", "*.bmp"])
        pattern_combo.grid(row=1, column=1, sticky="w", padx=(4, 0), pady=(4, 0))

        self.file_count_var = tk.StringVar(value="未选择目录")
        ttk.Label(input_frame, textvariable=self.file_count_var, foreground="gray").grid(
            row=2, column=0, columnspan=3, sticky="w", pady=(4, 0))

        self.input_var.trace_add("write", lambda *_: self._update_file_count())
        self.pattern_var.trace_add("write", lambda *_: self._update_file_count())

        # === 模式 ===
        mode_frame = ttk.LabelFrame(self.root, text="输出模式", padding=8)
        mode_frame.grid(row=1, column=0, sticky="ew", **pad)

        self.mode_var = tk.StringVar(value="image")
        ttk.Radiobutton(mode_frame, text="合成图片", variable=self.mode_var,
                        value="image", command=self._on_mode_change).grid(row=0, column=0, padx=(0, 16))
        ttk.Radiobutton(mode_frame, text="生成视频", variable=self.mode_var,
                        value="video", command=self._on_mode_change).grid(row=0, column=1)

        # === 输出 ===
        output_frame = ttk.LabelFrame(self.root, text="输出", padding=8)
        output_frame.grid(row=2, column=0, sticky="ew", **pad)
        output_frame.columnconfigure(1, weight=1)

        ttk.Label(output_frame, text="保存路径:").grid(row=0, column=0, sticky="w")
        self.output_var = tk.StringVar(value="star_trail.jpg")
        ttk.Entry(output_frame, textvariable=self.output_var, width=50).grid(row=0, column=1, sticky="ew", padx=(4, 4))
        ttk.Button(output_frame, text="浏览...", command=self._browse_output).grid(row=0, column=2)

        # === 选项 ===
        opts_frame = ttk.LabelFrame(self.root, text="选项", padding=8)
        opts_frame.grid(row=3, column=0, sticky="ew", **pad)

        self.preprocess_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(opts_frame, text="启用预处理（降噪 + 对比度增强）",
                        variable=self.preprocess_var).grid(row=0, column=0, columnspan=4, sticky="w")

        # 视频选项
        self.video_opts_frame = ttk.Frame(opts_frame)
        self.video_opts_frame.grid(row=1, column=0, columnspan=4, sticky="ew", pady=(4, 0))

        ttk.Label(self.video_opts_frame, text="帧率:").grid(row=0, column=0, sticky="w")
        self.fps_var = tk.IntVar(value=30)
        ttk.Spinbox(self.video_opts_frame, textvariable=self.fps_var,
                     from_=1, to=120, width=6).grid(row=0, column=1, padx=(4, 16))

        ttk.Label(self.video_opts_frame, text="总帧数:").grid(row=0, column=2, sticky="w")
        self.frames_var = tk.StringVar(value="")
        ttk.Entry(self.video_opts_frame, textvariable=self.frames_var, width=8).grid(row=0, column=3, padx=(4, 0))
        ttk.Label(self.video_opts_frame, text="(留空 = 与图像数量相同)",
                  foreground="gray").grid(row=0, column=4, padx=(4, 0))

        self.video_opts_frame.grid_remove()

        # === 进度 ===
        progress_frame = ttk.Frame(self.root, padding=(8, 4))
        progress_frame.grid(row=4, column=0, sticky="ew")
        progress_frame.columnconfigure(0, weight=1)

        self.progress_var = tk.DoubleVar(value=0)
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.grid(row=0, column=0, sticky="ew")

        self.status_var = tk.StringVar(value="就绪")
        ttk.Label(progress_frame, textvariable=self.status_var).grid(row=1, column=0, sticky="w")

        # === 按钮 ===
        btn_frame = ttk.Frame(self.root, padding=8)
        btn_frame.grid(row=5, column=0, sticky="e")

        self.start_btn = ttk.Button(btn_frame, text="开始", command=self._start)
        self.start_btn.grid(row=0, column=0)

    def _browse_input(self):
        directory = filedialog.askdirectory(title="选择图像所在目录")
        if directory:
            self.input_var.set(directory)

    def _browse_output(self):
        if self.mode_var.get() == "image":
            filetypes = [("JPEG", "*.jpg"), ("PNG", "*.png"), ("所有文件", "*.*")]
            default_ext = ".jpg"
        else:
            filetypes = [(ext.upper().lstrip("."), f"*{ext}") for ext in FOURCC_MAP]
            filetypes.append(("所有文件", "*.*"))
            default_ext = ".mp4"
        path = filedialog.asksaveasfilename(title="保存输出文件", filetypes=filetypes,
                                            defaultextension=default_ext)
        if path:
            self.output_var.set(path)

    def _update_file_count(self):
        directory = self.input_var.get()
        pattern = self.pattern_var.get()
        if directory and os.path.isdir(directory):
            import glob
            count = len(glob.glob(os.path.join(directory, pattern)))
            self.file_count_var.set(f"找到 {count} 个匹配文件")
        else:
            self.file_count_var.set("未选择目录" if not directory else "目录不存在")

    def _on_mode_change(self):
        if self.mode_var.get() == "video":
            self.video_opts_frame.grid()
            current = self.output_var.get()
            base, ext = os.path.splitext(current)
            if ext.lower() in (".jpg", ".jpeg", ".png", ".tif", ".tiff", ".bmp"):
                self.output_var.set(base + ".mp4")
        else:
            self.video_opts_frame.grid_remove()
            current = self.output_var.get()
            base, ext = os.path.splitext(current)
            if ext.lower() in (".mp4", ".avi", ".mov", ".mkv"):
                self.output_var.set(base + ".jpg")

    def _validate(self):
        directory = self.input_var.get()
        if not directory or not os.path.isdir(directory):
            messagebox.showerror("错误", "请选择有效的图像目录")
            return False
        output = self.output_var.get()
        if not output:
            messagebox.showerror("错误", "请指定输出文件路径")
            return False
        if self.mode_var.get() == "video":
            ext = os.path.splitext(output)[1].lower()
            if ext not in FOURCC_MAP:
                messagebox.showerror("错误", f"不支持的视频格式 '{ext}'，支持: {', '.join(FOURCC_MAP)}")
                return False
        return True

    def _on_progress(self, current, total):
        pct = current / total * 100 if total > 0 else 0
        self.root.after(0, self._update_progress, pct, f"处理中... {current}/{total}")

    def _update_progress(self, pct, text):
        self.progress_var.set(pct)
        self.status_var.set(text)

    def _start(self):
        if self.running:
            return
        if not self._validate():
            return

        self.running = True
        self.start_btn.configure(state="disabled")
        self.progress_var.set(0)
        self.status_var.set("处理中...")

        thread = threading.Thread(target=self._run_task, daemon=True)
        thread.start()

    def _run_task(self):
        try:
            directory = self.input_var.get()
            pattern = self.pattern_var.get()
            input_path = os.path.join(directory, pattern)
            output_file = self.output_var.get()

            if self.mode_var.get() == "image":
                create_star_trail(
                    input_path=input_path,
                    output_file=output_file,
                    enable_preprocess=self.preprocess_var.get(),
                    on_progress=self._on_progress,
                )
            else:
                frames_text = self.frames_var.get().strip()
                total_frames = int(frames_text) if frames_text else None
                create_star_trail_video(
                    input_path=input_path,
                    output_file=output_file,
                    fps=self.fps_var.get(),
                    total_frames=total_frames,
                    enable_preprocess=self.preprocess_var.get(),
                    on_progress=self._on_progress,
                )
            self.root.after(0, self._on_done, None)
        except Exception as e:
            self.root.after(0, self._on_done, str(e))

    def _on_done(self, error):
        self.running = False
        self.start_btn.configure(state="normal")
        if error:
            self.progress_var.set(0)
            self.status_var.set("出错")
            messagebox.showerror("错误", error)
        else:
            self.progress_var.set(100)
            self.status_var.set("完成")
            messagebox.showinfo("完成", f"已保存至 {self.output_var.get()}")


def run_gui():
    root = tk.Tk()
    StarTrailApp(root)
    root.mainloop()
