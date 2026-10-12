import os
import sys
import re
import logging
import ctypes
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import subprocess
import webbrowser

# Initialize global file mapping log stream tracker to record ring-0 sub-process states
logging.basicConfig(
    filename="parser_debug.log",
    filemode="w",
    level=logging.DEBUG,
    format="[%(asctime)s] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

class ScewinGuiParser:
    def __init__(self, root):
        self.root = root
        self.root.title("AMI SCEWIN BIOS Editor - by RobTech")
        self.root.geometry("1350x850")
        
        self.file_path = "BIOSData.txt"
        self.detected_encoding = "utf-8"
        
        # USER-PROVIDED LOCAL RESOLVER: Tracks local folders next to the application launcher
        if getattr(sys, 'frozen', False):
            self.base_resource_dir = os.path.dirname(sys.executable)
            logging.info(f"Packaged runtime execution path mapped to folder directory: {self.base_resource_dir}")
        else:
            self.base_resource_dir = os.path.dirname(os.path.abspath(__file__))
            logging.info("Developer execution path mapped to folder directory.")
            
        self.exe_path = os.path.join(self.base_resource_dir, "scewin_64.exe")
        
        self.file_elements = []
        self.ui_elements = {}
        
        self.tab_canvases = {}
        self.tab_content_frames = {}
        self.tab_index_map = {}
        self.allocated_tabs = set()
        
        self.master_tab_frames = {}
        self.sidebar_listboxes = {}
        self.sub_frame_containers = {}
        
        self.search_canvas = None
        self.search_content_frame = None
        self.summary_content_frame = None
        
        self.recent_searches_list = []
        self.search_lookup_cache_map = []

        self.apply_dark_theme()
        self.setup_ui()
        logging.info("Unified portable application workspace initialized successfully.")

    def apply_dark_theme(self):
        """Applies a complete high-contrast tech dark theme with modern rounded elements."""
        logging.info("Applying high-contrast modern dark design variables...")
        self.bg_color = "#1e1e1e"
        self.frame_bg = "#2d2d2d"
        self.text_color = "#e0e0e0"
        self.accent_color = "#3a3a3a"
        self.select_bg = "#4f4f4f"

        self.root.configure(bg=self.bg_color)
        self.style = ttk.Style()
        self.style.theme_use("clam")
        
        self.style.configure(".", background=self.bg_color, foreground=self.text_color)
        self.style.configure("TFrame", background=self.bg_color)
        
        self.style.configure("TLabelframe", background=self.frame_bg, foreground=self.text_color, borderwidth=1, relief="groove")
        self.style.configure("TLabelframe.Label", background=self.frame_bg, foreground=self.text_color, font=("Segoe UI", 10, "bold"))
        
        self.style.configure("Modified.TLabelframe", background="#24303c", foreground="#ffb703", borderwidth=1, relief="solid")
        self.style.configure("Modified.TLabelframe.Label", background="#24303c", foreground="#ffb703", font=("Segoe UI", 10, "bold"))
        
        self.style.configure("TButton", background=self.frame_bg, foreground=self.text_color, borderwidth=1, relief="groove", font=("Segoe UI", 9))
        self.style.map("TButton", background=[("active", self.select_bg), ("pressed", self.accent_color)])
        
        self.style.configure("Donate.TButton", background="#00457c", foreground="#ffffff", borderwidth=1, relief="groove", font=("Segoe UI", 9, "bold"))
        self.style.map("Donate.TButton", background=[("active", "#0079c1"), ("pressed", "#002d56")])
        
        self.style.configure("TCheckbutton", background=self.bg_color, foreground=self.text_color, font=("Segoe UI", 9))
        
        self.style.configure("TNotebook", background=self.bg_color, borderwidth=0)
        self.style.configure("TNotebook.Tab", background=self.frame_bg, foreground=self.text_color, borderwidth=1, padding=6, relief="groove")
        self.style.map("TNotebook.Tab", background=[("selected", self.select_bg)], foreground=[("selected", "#ffffff")])
        self.style.configure("TEntry", fieldbackground=self.frame_bg, foreground=self.text_color, insertcolor=self.text_color, borderwidth=1, relief="groove")
        self.style.configure("TCombobox", fieldbackground=self.frame_bg, background=self.accent_color, foreground=self.text_color, arrowcolor=self.text_color, borderwidth=1, relief="groove")
        self.style.map("TCombobox", fieldbackground=[("readonly", self.frame_bg)], foreground=[("readonly", self.text_color)])
        self.style.configure("TLabel", background=self.bg_color, foreground=self.text_color)

    def setup_ui(self):
        top_frame = ttk.Frame(self.root, padding="10")
        top_frame.pack(fill=tk.X)

        ttk.Button(top_frame, text="Load BIOSData.txt", command=self.load_file).pack(side=tk.LEFT, padx=5)
        ttk.Button(top_frame, text="Save Changes", command=self.save_file).pack(side=tk.LEFT, padx=5)
        ttk.Button(top_frame, text="Read from BIOS", command=self.export_bios).pack(side=tk.LEFT, padx=5)
        ttk.Button(top_frame, text="Write to BIOS", command=self.import_bios).pack(side=tk.LEFT, padx=5)

        # GRID SEARCH WRAPPER: Aligns components flush along the bottom row via sticky=tk.S
        search_frame = ttk.Frame(self.root, padding="5")
        search_frame.pack(fill=tk.X)
        
        lbl_search = ttk.Label(search_frame, text="Search Settings: ", font=("Segoe UI", 10))
        lbl_search.grid(row=0, column=0, rowspan=2, padx=5, sticky=tk.S, pady=(0, 2))
        
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", self.on_search_entry_keystroke_tracer)
        
        self.search_entry = ttk.Combobox(search_frame, textvariable=self.search_var, width=60)
        self.search_entry.grid(row=0, column=1, rowspan=2, padx=5, sticky=tk.S)
        self.search_entry.bind("<<ComboboxSelected>>", lambda e: self.apply_search_filter(force_history_commit=True))
        self.search_entry.bind("<Return>", lambda e: self.apply_search_filter(force_history_commit=True))
        
        lbl_live = tk.Label(search_frame, text="Live", font=("Segoe UI", 8, "bold"), fg="#ffb703", bg=self.bg_color)
        lbl_live.grid(row=0, column=2, padx=15, sticky=tk.S)
        
        self.live_search_toggle_var = tk.BooleanVar(value=False)
        chk_live = ttk.Checkbutton(search_frame, variable=self.live_search_toggle_var, style="TCheckbutton")
        chk_live.grid(row=1, column=2, padx=15, sticky=tk.S, pady=(2, 0))
        
        btn_search = ttk.Button(search_frame, text="🔍 Search", command=lambda: self.apply_search_filter(force_history_commit=True))
        btn_search.grid(row=0, column=3, rowspan=2, padx=5, sticky=tk.S)
        
        btn_donate = ttk.Button(search_frame, text="❤️ Donate", style="Donate.TButton", command=self.open_donate_link)
        btn_donate.grid(row=0, column=4, rowspan=2, padx=(96, 5), sticky=tk.S)

        self.notebook_container = ttk.Frame(self.root)
        self.notebook_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.notebook = ttk.Notebook(self.notebook_container)
        self.notebook.pack(fill=tk.BOTH, expand=True)

    def open_donate_link(self):
        try:
            # FIXED TARGET PORTAL INTERFACE: Routes securely to your PayPal NCP hub link node
            url = "https://www.paypal.com/ncp/payment/MGSPUHHR9JLKS"
            webbrowser.open(url)
        except Exception as e:
            logging.error(f"Failed to initialize system browser thread: {str(e)}")

    def is_admin(self):
        """Verifies if the security token context of the script is running elevated."""
        try:
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except Exception:
            return False
    def export_bios(self):
        logging.info("SCEWIN Export (Read from BIOS) operation requested by user.")
        if not self.is_admin():
            messagebox.showerror("Access Denied", "SCEWIN must communicate with NVRAM at kernel ring-0.\n\nPlease close the program, right-click, and select 'Run as Administrator'.")
            return
        if not os.path.exists(self.exe_path):
            messagebox.showerror("Error", f"Executable file 'scewin_64.exe' not found adjacent to tool folder.")
            return
        if not messagebox.askyesno("Confirm Read", "Dump active motherboard NVRAM layout and compile the matching HII Database binary map?"):
            return
        try:
            # CLEAN READ PASS MATRIX: Runs a standard parameter baseline layout dump [1.3]
            cmd = [self.exe_path, "/o", "/s", self.file_path, "/h", "BIOSData.db", "/v"]
            result = subprocess.run(cmd, check=False, capture_output=True, text=True)
            if result.returncode == 0:
                messagebox.showinfo("Success", f"Motherboard NVRAM layout structured successfully!\n\nCreated Assets:\n- {self.file_path}\n- BIOSData.db")
                self.load_file()
            else:
                messagebox.showerror("Execution Fault", f"SCEWIN sub-process threw an operational error.\nCode: {result.returncode}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to communicate with execution thread: {str(e)}")

    def import_bios(self):
        logging.info("SCEWIN Import (Write to BIOS) flash operation requested by user.")
        if not self.is_admin():
            messagebox.showerror("Access Denied", "SCEWIN must communicate with NVRAM at kernel ring-0.\n\nPlease close the program, right-click, and select 'Run as Administrator'.")
            return
        target = "BIOSData_Modified.txt"
        if not os.path.exists(target):
            messagebox.showerror("Error", f"Modified text map file '{target}' not found.\n\nPlease save your configuration changes first.")
            return
        if not os.path.exists(self.exe_path):
            messagebox.showerror("Error", f"Executable file 'scewin_64.exe' not found adjacent to tool folder.")
            return
            
        warning_msg = (
            "⚠️ WARNING: CRITICAL HARDWARE NVRAM SYSTEM SELECTION SEQUENCE\n\n"
            "You are about to flash 'BIOSData_Modified.txt' directly to live NVRAM variables.\n\n"
            "Applying incorrect configurations can compromise stability.\n\n"
            "Do you want to proceed with flashing this configuration?"
        )
        if messagebox.askyesno("🚨 Confirm Motherboard Flash", warning_msg, icon=messagebox.WARNING):
            try:
                # RAW IMPORT DRIVER SCHEMA: Executes raw script configurations back onto chip layers [1.3]
                cmd = [self.exe_path, "/i", "/s", target]
                result = subprocess.run(cmd, check=False, capture_output=True, text=True)
                if result.returncode == 0:
                    messagebox.showinfo("Success", "BIOS modifications successfully written to NVRAM! Please restart your machine to apply.")
                else:
                    messagebox.showerror("Flashing Fault", f"Motherboard flasher rejected the modification parameters.\nCode: {result.returncode}\n\nReview 'parser_debug.log' tracks.")
            except Exception as e:
                messagebox.showerror("Error", f"Flashing process crashed: {str(e)}")
    def load_file(self):
        logging.info("Initial setup document text file loader routine called.")
        if not os.path.exists(self.file_path):
            path = filedialog.askopenfilename(filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")])
            if path: self.file_path = path
            else: return
        for tab in self.notebook.tabs(): self.notebook.forget(tab)
        self.file_elements, self.ui_elements, self.tab_canvases, self.tab_content_frames, self.tab_index_map, self.allocated_tabs, self.master_tab_frames, self.sidebar_listboxes, self.sub_frame_containers = [], {}, {}, {}, {}, set(), {}, {}, {}
        self.search_canvas, self.search_content_frame, self.search_lookup_cache_map = None, None, []
        
        raw_bytes = b""
        try:
            with open(self.file_path, "rb") as bf: raw_bytes = bf.read()
        except Exception as e:
            messagebox.showerror("Error", f"Read error: {str(e)}")
            return
        decoded_text = ""
        for enc in ["utf-16le", "utf-8", "utf-16", "cp1252"]: 
            try:
                decoded_text = raw_bytes.decode(enc)
                if decoded_text and "setup question" in decoded_text.lower():
                    self.detected_encoding = enc
                    break
            except Exception: continue
        sanitized = decoded_text.replace("\x00", "")
        raw_lines = sanitized.splitlines(keepends=True)
        lines = list(raw_lines)
        
        idx, n, editable_blocks_found = 0, len(lines), 0
        current_guid = "00000000-0000-0000-0000-000000000000"
        current_title, current_nested_header, last_valid_nested_header = "General Settings", "Base Options", "Base Options"
        disclaimer_form_titles = ["accept", "decline", "accepted", "declined"]
        
        while idx < n:
            line_clean = lines[idx]
            line_lower = line_clean.lower()
            if "form set" in line_lower and line_clean.lstrip().startswith("//"):
                lookahead = 1
                temp_guid, temp_title = None, None
                while idx + lookahead < n and lookahead < 6:
                    next_line = lines[idx + lookahead].replace("\x00", "")
                    if "guid" in next_line.lower() and "=" in next_line: temp_guid = next_line.split("=", 1)[-1].strip()
                    if "title" in next_line.lower() and "=" in next_line: temp_title = next_line.split("=", 1)[-1].strip()
                    if next_line.strip() and not next_line.lstrip().startswith("//"): break
                    lookahead += 1
                if temp_guid: current_guid = temp_guid
                if temp_title: 
                    current_title = temp_title
                    current_nested_header = "Base Options"
                    last_valid_nested_header = "Base Options"
            elif "form" in line_lower and line_clean.lstrip().startswith("//") and "form set" not in line_lower:
                lookahead = 1
                while idx + lookahead < n and lookahead < 8:
                    sub_line = lines[idx + lookahead].replace("\x00", "")
                    if "title" in sub_line.lower() and "=" in sub_line:
                        parsed_form_title = sub_line.split("=", 1)[-1].strip()
                        if parsed_form_title.lower() in disclaimer_form_titles: current_nested_header = last_valid_nested_header
                        else:
                            current_nested_header = parsed_form_title
                            last_valid_nested_header = parsed_form_title
                        break
                    if sub_line.strip() and not sub_line.lstrip().startswith("//"): break
                    lookahead += 1
            if "setup question" in line_lower and "=" in line_clean and not line_clean.lstrip().startswith("//"):
                token_id, offset_id, look_meta = f"TOK_{editable_blocks_found}", f"OFF_{editable_blocks_found}", 1
                while idx + look_meta < n and look_meta < 5:
                    m_line = lines[idx + look_meta]
                    if "token" in m_line.lower() and "=" in m_line: token_id = m_line.split("=", 1)[-1].split("//")[0].strip()
                    if "offset" in m_line.lower() and "=" in m_line: offset_id = m_line.split("=", 1)[-1].split("//")[0].strip()
                    look_meta += 1
                q_name = line_clean.split("=", 1)[-1].strip()
                composite_lookup_id = f"{current_guid}_{token_id}_{offset_id}"
                uses_padded_hex_indicators, bios_default_badge_string, original_unconverted_state, has_enclosing_brackets = False, "", "", False
                block = {"type": "editable_block", "composite_lookup_id": composite_lookup_id, "token_id": token_id, "offset_id": offset_id, "question_line": line_clean, "question_name": q_name, "help_string": "", "meta_lines": [], "mode": None, "options": [], "selected": None, "guid": current_guid, "title": current_title, "nested_header": current_nested_header, "ui_frame": None, "padded_hex": False, "bios_default": "", "original_initial_value": "", "is_duplicate_mirror": False, "uses_brackets": False}
                while idx + 1 < n:
                    peek_line = lines[idx + 1]
                    peek_lower = peek_line.lower()
                    if "help string" in peek_lower and "=" in peek_line:
                        raw_help = peek_line.split("=", 1)[-1].strip()
                        if raw_help.startswith('"') and raw_help.endswith('"'): raw_help = raw_help[1:-1].strip()
                        block["help_string"] = raw_help
                        block["meta_lines"].append(peek_line)
                        idx += 1
                    elif "bios default" in peek_lower and "=" in peek_line:
                        bios_default_badge_string = peek_line.split("=", 1)[-1].strip()
                        block["meta_lines"].append(peek_line)
                        idx += 1
                    elif any(k in peek_lower and "=" in peek_line for k in ["token", "offset", "width"]):
                        block["meta_lines"].append(peek_line)
                        idx += 1
                    elif "options" in peek_lower and "=" in peek_line:
                        block["mode"] = "options"
                        assignment_parts = peek_line.split("=", 1)
                        raw_value_side = assignment_parts[1].strip() if len(assignment_parts) > 1 else ""
                        raw_opt_parts = raw_value_side.split("//")
                        raw_opt = raw_opt_parts[0].strip() if raw_opt_parts else ""
                        if raw_opt.startswith("[0"): uses_padded_hex_indicators = True
                        if raw_opt.startswith("*"):
                            val = raw_opt.lstrip("*").strip()
                            block["selected"] = val
                            original_unconverted_state = val
                            block["options"].append(val)
                        else: block["options"].append(raw_opt)
                        idx += 1
                        while idx + 1 < n and (lines[idx+1].startswith(" ") or lines[idx+1].startswith("\t")) and lines[idx+1].strip():
                            idx += 1
                            next_raw_parts = lines[idx].strip().split("//")
                            next_raw = next_raw_parts[0].strip() if next_raw_parts else ""
                            if next_raw.startswith("*"):
                                v_next = next_raw.lstrip("*").strip()
                                block["selected"] = v_next
                                original_unconverted_state = v_next
                                block["options"].append(v_next)
                            else: block["options"].append(next_raw)
                        break
                    elif "value" in peek_lower and "=" in peek_line:
                        block["mode"] = "value"
                        assignment_parts = peek_line.split("=", 1)
                        raw_value_side = assignment_parts[1].strip() if len(assignment_parts) > 1 else ""
                        val_parts = raw_value_side.split("//")
                        val_part = val_parts[0].strip() if val_parts else ""
                        if val_part.startswith("<") and val_part.endswith(">"):
                            has_enclosing_brackets = True
                            val_part = val_part[1:-1].strip()
                        try:
                            decimal_translation = str(int(val_part, 16))
                            block["selected"] = decimal_translation
                            original_unconverted_state = decimal_translation
                        except ValueError:
                            block["selected"] = val_part
                            original_unconverted_state = val_part
                        idx += 1
                        break
                    else: break
                block["padded_hex"] = uses_padded_hex_indicators
                block["bios_default"] = bios_default_badge_string
                block["original_initial_value"] = original_unconverted_state
                block["uses_brackets"] = has_enclosing_brackets
                already_mounted = any(x.get("type") == "editable_block" and x["composite_lookup_id"] == composite_lookup_id for x in self.file_elements)
                if already_mounted: block["is_duplicate_mirror"] = True
                self.file_elements.append(block)
                if not block["is_duplicate_mirror"]:
                    self.render_block_ui(block)
                    self.search_lookup_cache_map.append(block)
                editable_blocks_found += 1
            else: self.file_elements.append({"type": "raw_line", "text": line_clean})
            idx += 1
        self.create_changes_summary_hub()
        for key, canvas in self.tab_canvases.items():
            canvas.update_idletasks()
            canvas.configure(scrollregion=canvas.bbox("all"))
        messagebox.showinfo("Load Complete", f"Successfully structured {editable_blocks_found} options categorized inside sidebar panes!")

    def create_sidebar_layout(self, guid, root_title):
        master_frame = ttk.Frame(self.notebook)
        display_label = f" {root_title} " if root_title != "General Settings" else f" {guid[:8]}... "
        self.notebook.add(master_frame, text=f"{display_label:<22}")
        self.tab_index_map[guid] = len(self.tab_index_map)
        self.master_tab_frames[guid] = master_frame
        left_pane = ttk.Frame(master_frame, padding="5")
        left_pane.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 5))
        ttk.Label(left_pane, text="Categories", font=("Segoe UI", 9, "bold")).pack(anchor=tk.W, pady=2)
        listbox = tk.Listbox(left_pane, width=32, bg=self.frame_bg, fg=self.text_color, selectbackground=self.select_bg, selectforeground="#ffffff", highlightthickness=0, font=("Segoe UI", 9))
        listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb = ttk.Scrollbar(left_pane, orient="vertical", command=listbox.yview)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        listbox.configure(yscrollcommand=sb.set)
        right_container = ttk.Frame(master_frame)
        right_container.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        self.sidebar_listboxes[guid] = listbox
        self.sub_frame_containers[guid] = right_container
        listbox.bind("<<ListboxSelect>>", lambda e, g=guid: self.on_sidebar_select(g))

    def on_sidebar_select(self, guid):
        lb = self.sidebar_listboxes[guid]
        selections = lb.curselection()
        if not selections: return
        selected_header = lb.get(selections)
        unique_sub_id = f"{guid}_{selected_header}"
        for key, canvas in self.tab_canvases.items():
            if key.startswith(guid): canvas.master.pack_forget()
        if unique_sub_id in self.tab_canvases: self.tab_canvases[unique_sub_id].master.pack(fill=tk.BOTH, expand=True)

    def create_tab_scroll_frame(self, guid, nested_title):
        unique_sub_id = f"{guid}_{nested_title}"
        right_container = self.sub_frame_containers[guid]
        outer_wrap = ttk.Frame(right_container)
        canvas = tk.Canvas(outer_wrap, highlightthickness=0, bg=self.bg_color)
        scrollbar = ttk.Scrollbar(outer_wrap, orient="vertical", command=canvas.yview)
        scrollable_content = ttk.Frame(canvas)
        scrollable_content.bind("<Configure>", lambda e, c=canvas: c.configure(scrollregion=c.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_content, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        canvas.bind_all("<MouseWheel>", lambda event, c=canvas: c.yview_scroll(int(-1*(event.delta/120)), "units"))
        self.tab_canvases[unique_sub_id] = canvas
        self.tab_content_frames[unique_sub_id] = scrollable_content
        self.sidebar_listboxes[guid].insert(tk.END, nested_title)
        return scrollable_content

    def on_search_entry_keystroke_tracer(self, *args):
        if self.live_search_toggle_var.get(): self.apply_search_filter(force_history_commit=False)
    def commit_search_to_recent_history_stack(self):
        raw_query = self.search_var.get().strip()
        if not raw_query: return
        if raw_query in self.recent_searches_list: self.recent_searches_list.remove(raw_query)
        self.recent_searches_list.insert(0, raw_query)
        if len(self.recent_searches_list) > 10: self.recent_searches_list.pop()
        self.search_entry.configure(values=self.recent_searches_list)
        logging.info(f"Search history stack updated. Active logs: {self.recent_searches_list}")

    def bg_delta_audit_thread(self, block):
        try:
            lookup_key = block["composite_lookup_id"]
            current_ui_value = self.ui_elements[lookup_key]["var"].get()
            original_value = block["original_initial_value"]
            frame_title_string = f" {block['question_name']} "
            if block["bios_default"]: frame_title_string += f"   [Default: {block['bios_default']}] "
            if current_ui_value != original_value:
                frame_title_string += f"   ⚠️ [Modified] (Was: {original_value}) "
                block["ui_frame"].configure(style="Modified.TLabelframe", text=frame_title_string)
            else: block["ui_frame"].configure(style="TLabelframe", text=frame_title_string)
            for element in self.file_elements:
                if element.get("type") == "editable_block" and element["composite_lookup_id"] == lookup_key: element["selected"] = current_ui_value
            self.refresh_changes_summary_sheet()
        except Exception: pass

    def render_block_ui(self, block):
        try:
            guid, nested_title = block["guid"], block["nested_header"]
            unique_sub_id = f"{guid}_{nested_title}"
            if guid not in self.master_tab_frames: self.create_sidebar_layout(guid, block["title"])
            if unique_sub_id not in self.allocated_tabs:
                self.create_tab_scroll_frame(guid, nested_title)
                self.allocated_tabs.add(unique_sub_id)
                if self.sidebar_listboxes[guid].size() == 1:
                    self.sidebar_listboxes[guid].selection_set(0)
                    self.tab_canvases[unique_sub_id].master.pack(fill=tk.BOTH, expand=True)
            parent_container = self.tab_content_frames[unique_sub_id]
            frame_title_string = f" {block['question_name']} "
            if block["bios_default"]: frame_title_string += f"   [Default: {block['bios_default']}] "
            frame = ttk.LabelFrame(parent_container, text=frame_title_string, padding="10")
            frame.pack(fill=tk.X, expand=True, padx=10, pady=5)
            block["ui_frame"] = frame
            if block["help_string"]:
                help_lbl = tk.Label(frame, text=block["help_string"], justify=tk.LEFT, anchor="w", fg="#aaaaaa", bg=self.frame_bg, font=("Segoe UI", 9, "italic"), wraplength=750)
                help_lbl.pack(fill=tk.X, side=tk.TOP, padx=5, pady=(2, 8))
            lookup_key = block["composite_lookup_id"]
            if block["mode"] == "options" and block["options"]:
                ttk.Label(frame, text="Option:", width=12).pack(side=tk.LEFT)
                var = tk.StringVar(value=block["selected"])
                var.trace_add("write", lambda *args, b=block: self.bg_delta_audit_thread(b))
                combo = ttk.Combobox(frame, textvariable=var, values=block["options"], state="readonly", width=50)
                combo.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
                self.ui_elements[lookup_key] = {"type": "options", "var": var}
                self.root.option_add("*TCombobox*Listbox.background", self.frame_bg)
                self.root.option_add("*TCombobox*Listbox.foreground", self.text_color)
                self.root.option_add("*TCombobox*Listbox.selectBackground", self.select_bg)
            elif block["mode"] == "value":
                ttk.Label(frame, text="Value:", width=12).pack(side=tk.LEFT)
                var = tk.StringVar(value=block["selected"])
                var.trace_add("write", lambda *args, b=block: self.bg_delta_audit_thread(b))
                entry = ttk.Entry(frame, textvariable=var, width=52)
                entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
                self.ui_elements[lookup_key] = {"type": "value", "var": var}
        except Exception as e: logging.error(f"UI component layout generation error: {block['question_name']} - {str(e)}")

    def create_changes_summary_hub(self):
        master_frame = ttk.Frame(self.notebook)
        self.notebook.add(master_frame, text="  [CHANGES SUMMARY]  ")
        canvas = tk.Canvas(master_frame, highlightthickness=0, bg=self.bg_color)
        scrollbar = ttk.Scrollbar(master_frame, orient="vertical", command=canvas.yview)
        scrollable_content = ttk.Frame(canvas)
        scrollable_content.bind("<Configure>", lambda e, c=canvas: c.configure(scrollregion=c.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_content, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self.summary_content_frame = scrollable_content

    def refresh_changes_summary_sheet(self):
        if not self.summary_content_frame: return
        for child in self.summary_content_frame.winfo_children(): child.destroy()
        tk.Label(self.summary_content_frame, text="📋 PENDING NVRAM MODIFICATIONS AUDIT TRACKER\n", font=("Segoe UI", 11, "bold"), fg="#ffb703", bg=self.bg_color).pack(anchor=tk.W, padx=15, pady=(10, 5))
        changes_found = 0
        for element in self.file_elements:
            if element.get("type") == "editable_block" and not element["is_duplicate_mirror"]:
                lookup_key = element["composite_lookup_id"]
                if lookup_key in self.ui_elements:
                    current_val = self.ui_elements[lookup_key]["var"].get()
                    original_val = element["original_initial_value"]
                    if current_val != original_val:
                        changes_found += 1
                        row_frame = ttk.LabelFrame(self.summary_content_frame, text=f" Change #{changes_found} ", padding="8", style="Modified.TLabelframe")
                        row_frame.pack(fill=tk.X, expand=True, padx=15, pady=5)
                        meta_label = f"Setting: {element['question_name']}\nLocation: {element['title']} -> {element['nested_header']}\nOriginal State: {original_val}\nProposed State: {current_val}"
                        tk.Label(row_frame, text=meta_label, justify=tk.LEFT, font=("Segoe UI", 9), fg="#ffffff", bg="#24303c").pack(anchor=tk.W, padx=5)
        if changes_found == 0: tk.Label(self.summary_content_frame, text="   No pending changes detected. Motherboard configurations match baseline files.", font=("Segoe UI", 9, "italic"), fg="#aaaaaa", bg=self.bg_color).pack(anchor=tk.W, padx=15, pady=10)

    def create_global_search_hub(self):
        master_frame = ttk.Frame(self.notebook)
        self.notebook.insert(0, master_frame, text=" [SEARCH RESULTS] ")
        canvas = tk.Canvas(master_frame, highlightthickness=0, bg=self.bg_color)
        scrollbar = ttk.Scrollbar(master_frame, orient="vertical", command=canvas.yview)
        scrollable_content = ttk.Frame(canvas)
        scrollable_content.bind("<Configure>", lambda e, c=canvas: c.configure(scrollregion=c.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_content, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self.search_canvas, self.search_content_frame = canvas, scrollable_content

    def apply_search_filter(self, force_history_commit=False):
        query = self.search_var.get().lower().strip()
        if self.search_content_frame:
            for child in self.search_content_frame.winfo_children(): child.destroy()
        if not query:
            try: self.notebook.forget(0)
            except Exception: pass
            return
        try:
            if self.notebook.tab(0, "text") != " [SEARCH RESULTS] ": self.create_global_search_hub()
        except Exception: self.create_global_search_hub()
        if force_history_commit: self.commit_search_to_recent_history_stack()
        matches_found = 0
        for element in self.search_lookup_cache_map:
            if query in element["question_name"].lower() or query in element["nested_header"].lower():
                lookup_key = element["composite_lookup_id"]
                if lookup_key in self.ui_elements:
                    matches_found += 1
                    var = self.ui_elements[lookup_key]["var"]
                    search_title = f" {element['question_name']}   ({element['title']} -> {element['nested_header']}) "
                    if element["bios_default"]: search_title += f"   [Default: {element['bios_default']}] "
                    c_frame = ttk.LabelFrame(self.search_content_frame, text=search_title, padding="10")
                    c_frame.pack(fill=tk.X, expand=True, padx=15, pady=6)
                    if element["help_string"]: tk.Label(c_frame, text=element["help_string"], justify=tk.LEFT, anchor="w", fg="#aaaaaa", bg=self.frame_bg, font=("Segoe UI", 9, "italic"), wraplength=900).pack(fill=tk.X, side=tk.TOP, padx=5, pady=(2, 8))
                    if element["options"] and element["mode"] == "options":
                        ttk.Label(c_frame, text="Option:", width=12).pack(side=tk.LEFT)
                        combo = ttk.Combobox(c_frame, textvariable=var, values=element["options"], state="readonly", width=50)
                        combo.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
                    elif element["mode"] == "value":
                        ttk.Label(c_frame, text="Value:", width=12).pack(side=tk.LEFT)
                        entry = ttk.Entry(c_frame, textvariable=var, width=52)
                        entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        if matches_found > 0:
            self.notebook.select(0)
            self.search_canvas.configure(scrollregion=self.search_canvas.bbox("all"))

    def save_file(self):
        if not self.file_elements: return
        target_file = "BIOSData_Modified.txt"
        try:
            with open(target_file, "w", encoding=self.detected_encoding) as f:
                for el in self.file_elements:
                    if el["type"] == "raw_line": f.write(el["text"])
                    elif el["type"] == "editable_block":
                        f.write(el["question_line"])
                        for m_line in el["meta_lines"]: f.write(m_line)
                        lookup_key = el["composite_lookup_id"]
                        user_val = el["selected"]
                        if el["mode"] == "options":
                            for i, opt in enumerate(el["options"]):
                                prefix = "*" if opt == user_val else ""
                                comment = "\t// Move \"*\" to the desired Option" if i == 0 else ""
                                opt_str = opt
                                if el["padded_hex"] and opt.startswith("[") and opt.index("]") == 2:
                                    raw_val_str = opt[1:2]
                                    if raw_val_str.isdigit() or raw_val_str.lower() in "abcdef": opt_str = f"[0{raw_val_str}]{opt[3:]}"
                                f.write(f"Options\t={prefix}{opt_str}{comment}\n" if i == 0 else f"         {prefix}{opt_str}\n")
                        elif el["mode"] == "value": 
                            output_value_string = user_val
                            try: output_value_string = hex(int(user_val))[2:].upper()
                            except ValueError: pass
                            if el["uses_brackets"]: output_value_string = f"<{output_value_string}>"
                            f.write(f"Value\t={output_value_string}\n")
            messagebox.showinfo("Success", f"Modifications written to: {target_file}")
            self.load_file()
        except Exception as e: messagebox.showerror("Error", f"Failed to save: {str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = ScewinGuiParser(root)
    root.mainloop()
