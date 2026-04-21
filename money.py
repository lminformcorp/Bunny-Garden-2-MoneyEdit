import sys
import threading
import time
import ctypes
import struct
import os
from pymem import Pymem
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLineEdit, QPushButton, QCheckBox, QLabel, 
                             QMessageBox, QFileDialog)
from PyQt6.QtCore import pyqtSignal, QObject

# --- Windows API 常數與結構 ---
MEM_COMMIT = 0x1000
PAGE_READWRITE = 0x04

class MEMORY_BASIC_INFORMATION(ctypes.Structure):
    _fields_ = [
        ("BaseAddress", ctypes.c_void_p),
        ("AllocationBase", ctypes.c_void_p),
        ("AllocationProtect", ctypes.c_uint32),
        ("RegionSize", ctypes.c_size_t),
        ("State", ctypes.c_uint32),
        ("Protect", ctypes.c_uint32),
        ("Type", ctypes.c_uint32),
    ]

# 管理員權限檢查
if not ctypes.windll.shell32.IsUserAnAdmin():
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
    sys.exit()

class StatusSignals(QObject):
    update = pyqtSignal(str, str)

class FileSelectTrainer(QWidget):
    def __init__(self):
        super().__init__()
        self.pm = None
        self.target_process_name = ""
        self.found_addresses = []
        self.is_frozen = False
        self.signals = StatusSignals()
        self.signals.update.connect(self.set_status)
        self.init_ui()
        # 背景監控執行緒
        threading.Thread(target=self.auto_attach_loop, daemon=True).start()

    def init_ui(self):
        self.setWindowTitle("兔兔秘密花園 2 - 檔案選取修改器")
        self.setFixedSize(450, 350)
        layout = QVBoxLayout()

        # 1. 檔案選取區
        layout.addWidget(QLabel("第一步：選取遊戲執行檔 (.exe)"))
        file_layout = QHBoxLayout()
        self.file_path_label = QLineEdit()
        self.file_path_label.setReadOnly(True)
        self.file_path_label.setPlaceholderText("請選擇遊戲路徑...")
        self.select_btn = QPushButton("選取檔案")
        self.select_btn.clicked.connect(self.open_file_dialog)
        file_layout.addWidget(self.file_path_label)
        file_layout.addWidget(self.select_btn)
        layout.addLayout(file_layout)

        self.status_label = QLabel("狀態: 請先選取遊戲執行檔")
        self.status_label.setStyleSheet("font-weight: bold; color: gray;")
        layout.addWidget(self.status_label)

        # 2. 搜尋區
        layout.addWidget(QLabel("第二步：輸入目前遊戲看到的金額"))
        h1 = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("例如: 168000")
        self.search_btn = QPushButton("開始搜尋")
        self.search_btn.clicked.connect(self.start_scan_thread)
        h1.addWidget(self.search_input)
        h1.addWidget(self.search_btn)
        layout.addLayout(h1)

        # 3. 修改區
        layout.addWidget(QLabel("第三步：輸入想修改的金額"))
        h2 = QHBoxLayout()
        self.money_input = QLineEdit()
        self.apply_btn = QPushButton("執行修改")
        self.apply_btn.clicked.connect(self.apply_change)
        h2.addWidget(self.money_input)
        h2.addWidget(self.apply_btn)
        layout.addLayout(h2)

        self.freeze_cb = QCheckBox("持續鎖定金額 (固定數值)")
        layout.addWidget(self.freeze_cb)

        self.hint = QLabel("💡 提示：選取 .exe 後，程式會自動對照進程名稱進行連接。\n若搜尋失敗，請嘗試在遊戲中讓金額變動後重新搜尋。")
        self.hint.setStyleSheet("font-size: 11px; color: #1565c0; background: #e3f2fd; padding: 8px; border-radius: 4px;")
        layout.addWidget(self.hint)

        self.setLayout(layout)

    def set_status(self, text, color):
        self.status_label.setText(f"狀態: {text}")
        self.status_label.setStyleSheet(f"font-weight: bold; color: {color};")

    def open_file_dialog(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "選取遊戲執行檔", "", "Executable Files (*.exe)")
        if file_path:
            self.file_path_label.setText(file_path)
            # 自動提取進程名稱 (例如: C:/Game/Bunny.exe -> Bunny.exe)
            self.target_process_name = os.path.basename(file_path)
            self.pm = None # 重置連接
            self.signals.update.emit(f"已選取: {self.target_process_name}，等待遊戲啟動...", "orange")

    def auto_attach_loop(self):
        """背景自動連接執行緒"""
        while True:
            if self.target_process_name and not self.pm:
                try:
                    self.pm = Pymem(self.target_process_name)
                    self.signals.update.emit(f"已成功連線至: {self.target_process_name}", "green")
                except:
                    pass
            time.sleep(2)

    def start_scan_thread(self):
        if not self.pm:
            QMessageBox.warning(self, "錯誤", "尚未連接遊戲進程，請先選取檔案並啟動遊戲！")
            return
        threading.Thread(target=self.fuzzy_scan_logic, daemon=True).start()

    def fuzzy_scan_logic(self):
        try:
            raw_input = "".join(filter(str.isdigit, self.search_input.text().strip()))
            if not raw_input: return

            # 準備搜尋模式：8-byte 完整、8-byte 截斷
            val_full = int(raw_input)
            val_truncated = int(raw_input[:-1]) if len(raw_input) > 1 else val_full
            
            patterns = [struct.pack("<q", val_full), struct.pack("<q", val_truncated)]
            self.found_addresses = []
            self.signals.update.emit("深度掃描記憶體中...", "orange")
            
            # 使用 Windows API 遍歷，解決圖片中 list_mer 報錯問題
            base_address = 0
            max_address = 0x7FFFFFFFFFFF
            while base_address < max_address:
                mbi = MEMORY_BASIC_INFORMATION()
                # 確保傳入正確的類型轉型
                if ctypes.windll.kernel32.VirtualQueryEx(self.pm.process_handle, ctypes.c_void_p(base_address), ctypes.byref(mbi), ctypes.sizeof(mbi)):
                    if mbi.State == MEM_COMMIT and (mbi.Protect & PAGE_READWRITE):
                        try:
                            buffer = self.pm.read_bytes(mbi.BaseAddress, mbi.RegionSize)
                            for p in patterns:
                                offset = buffer.find(p)
                                while offset != -1:
                                    self.found_addresses.append(mbi.BaseAddress + offset)
                                    offset = buffer.find(p, offset + 1)
                        except: pass
                    base_address += mbi.RegionSize
                else: break

            if self.found_addresses:
                self.found_addresses = list(set(self.found_addresses)) # 去重
                self.signals.update.emit(f"捕捉成功！找到 {len(self.found_addresses)} 處", "green")
            else:
                self.signals.update.emit("搜尋不到，請變動金額再試一次", "red")
        except Exception as e:
            self.signals.update.emit(f"發生異常", "red")

    def apply_change(self):
        if not self.found_addresses:
            QMessageBox.warning(self, "失敗", "請先搜尋位址")
            return
        try:
            new_money = int("".join(filter(str.isdigit, self.money_input.text().strip())))
            for addr in self.found_addresses:
                try:
                    self.pm.write_longlong(addr, new_money)
                except: pass
            
            self.is_frozen = self.freeze_cb.isChecked()
            if self.is_frozen:
                threading.Thread(target=self.freeze_worker, args=(new_money,), daemon=True).start()
            QMessageBox.information(self, "完成", "修改已送出！")
        except:
            QMessageBox.critical(self, "錯誤", "金額輸入有誤")

    def freeze_worker(self, val):
        while self.is_frozen:
            for addr in self.found_addresses:
                try: self.pm.write_longlong(addr, val)
                except: pass
            time.sleep(0.5)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FileSelectTrainer()
    window.show()
    sys.exit(app.exec())