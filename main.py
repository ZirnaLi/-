import sys
import os
import sqlite3
import bcrypt
import datetime
import pandas as pd
from PyQt5.QtGui import QTextDocument
from PyQt5.QtPrintSupport import QPrinter
from PyQt5.QtCore import Qt
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtPrintSupport import QPrinter
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QLineEdit, QPushButton, QMessageBox, QTableWidget, QTableWidgetItem,
                             QHeaderView, QFileDialog, QComboBox, QInputDialog, QDialog, QSizePolicy)

DATABASE_NAME = "database.db"


def init_db():
    conn = sqlite3.connect(DATABASE_NAME)
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password_hash BLOB,
        is_admin INTEGER DEFAULT 0
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS wages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        姓名 TEXT,
        点数 REAL, 基本奖 REAL, CT REAL, CT照相摆位 REAL, DX REAL, MR科研 REAL, 值班 REAL, MG REAL, MR REAL,
        急诊CT REAL, 发热 REAL, 加班费 REAL, 床旁 REAL, 急诊补助 REAL, 穿刺 REAL, 值班补助 REAL, 授权职能 REAL,
        其它 REAL, 奖金总计 REAL,绩效 REAL, 
        年 INTEGER,
        月 INTEGER
    )''')

    conn.commit()
    conn.close()

    preset_data()


def preset_data():
    if get_user("管理员") is None:
        register_user("管理员", "admin", True)
    if get_user("testuser") is None:
        register_user("testuser", "123456", False)

    # 插入测试数据(如果不存在)
    conn = sqlite3.connect(DATABASE_NAME)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM wages WHERE username='testuser'")
    count = c.fetchone()[0]
    if count == 0:
        test_data = [
            ["testuser", "张三", 10, 500, 100, 50, 60, 20, 30, 40, 10, 5, 3, 200, 10, 20, 5, 10, 5, 10, 15, 10, 2024, 3],
            ["testuser", "张三", 12, 520, 120, 60, 70, 25, 35, 45, 15, 6, 4, 220, 15, 25, 8, 12, 6, 12, 18, 12, 2024, 4],
            ["testuser", "张三", 15, 550, 130, 70, 80, 30, 40, 50, 20, 7, 5, 250, 20, 30, 10, 15, 8, 15, 20, 15, 2024, 5]
        ]
        for row in test_data:
            insert_wage_data(tuple(row))
    conn.close()


def get_user(username):
    conn = sqlite3.connect(DATABASE_NAME)
    c = conn.cursor()
    c.execute("SELECT id, username, password_hash, is_admin FROM users WHERE username=?", (username,))
    user = c.fetchone()
    conn.close()
    return user


def register_user(username, password, is_admin=False):
    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    conn = sqlite3.connect(DATABASE_NAME)
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (username, password_hash, is_admin) VALUES (?, ?, ?)",
                  (username, hashed, 1 if is_admin else 0))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        conn.close()
        return False


def verify_password(username, password):
    user = get_user(username)
    if user is None:
        return False
    hashed = user[2]
    return bcrypt.checkpw(password.encode('utf-8'), hashed)


def update_password(username, new_password):
    user = get_user(username)
    if user is None:
        return False
    hashed = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
    conn = sqlite3.connect(DATABASE_NAME)
    c = conn.cursor()
    c.execute("UPDATE users SET password_hash=? WHERE username=?", (hashed, username))
    conn.commit()
    conn.close()
    return True



def insert_wage_data(row_data):
    conn = sqlite3.connect(DATABASE_NAME)
    c = conn.cursor()
    c.execute('''INSERT INTO wages (username, 姓名, 点数, 基本奖, CT, CT照相摆位, DX, MR科研, 值班, MG, MR, 急诊CT, 发热,
                                   加班费, 床旁, 急诊补助, 穿刺, 值班补助, 授权职能, 其它, 奖金总计, 绩效, 年, 月)
                 VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''', row_data)
    conn.commit()
    conn.close()


def update_wage_data(wage_id, data_dict):
    numeric_fields = ["点数", "基本奖", "CT", "CT照相摆位", "DX", "MR科研", "值班", "MG", "MR", "急诊CT", "发热",
                      "加班费", "床旁", "急诊补助", "穿刺", "值班补助", "授权职能", "其它", "奖金总计" "绩效" ]
    #total = 0.0
    #for f in numeric_fields:
        #val = data_dict.get(f, 0.0)
        #if val is None:
           #val = 0.0
        #total += float(val)
   # data_dict["奖金总计"] = total

    set_clauses = ", ".join([f"{key}=?" for key in data_dict.keys()])
    values = list(data_dict.values())
    values.append(wage_id)
    conn = sqlite3.connect(DATABASE_NAME)
    c = conn.cursor()
    c.execute(f"UPDATE wages SET {set_clauses} WHERE id=?", values)
    conn.commit()
    conn.close()


def delete_wage_data(wage_id):
    conn = sqlite3.connect(DATABASE_NAME)
    c = conn.cursor()
    c.execute("DELETE FROM wages WHERE id=?", (wage_id,))
    conn.commit()
    conn.close()


def query_wages(username=None, is_admin=False, year=None, month=None, search_name=None, filter_user=None):
    conn = sqlite3.connect(DATABASE_NAME)
    c = conn.cursor()
    query = "SELECT id, username, 姓名, 点数, 基本奖, CT, CT照相摆位, DX, MR科研, 值班, MG, MR, 急诊CT, 发热, 加班费, 床旁, 急诊补助, 穿刺, 值班补助, 授权职能, 其它, 奖金总计, 绩效, 年, 月 FROM wages WHERE 1=1"
    params = []
    if not is_admin:
        query += " AND username=?"
        params.append(username)
    if year is not None:
        query += " AND 年=?"
        params.append(year)
    if month is not None:
        query += " AND 月=?"
        params.append(month)
    if is_admin and search_name is not None and search_name.strip() != "":
        query += " AND 姓名 LIKE ?"
        params.append(f"%{search_name}%")
    if is_admin and filter_user is not None and filter_user != "所有用户":
        query += " AND 姓名=?"
        params.append(filter_user)
    c.execute(query, params)
    rows = c.fetchall()
    conn.close()
    return rows


def get_all_names_from_wages():
    conn = sqlite3.connect(DATABASE_NAME)
    c = conn.cursor()
    c.execute("SELECT DISTINCT 姓名 FROM wages")
    names = [row[0] for row in c.fetchall()]
    conn.close()
    return names


def get_latest_year_month():
    conn = sqlite3.connect(DATABASE_NAME)
    c = conn.cursor()
    c.execute("SELECT 年, 月 FROM wages ORDER BY 年 DESC, 月 DESC LIMIT 1")
    row = c.fetchone()
    conn.close()
    if row:
        return row[0], row[1]
    return None, None


class LoginWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("用户登录")
        self.resize(300, 300)

        main_layout = QVBoxLayout()

        self.username_edit = QLineEdit()
        self.username_edit.setPlaceholderText("请输入中文姓名")
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.Password)
        self.password_edit.setPlaceholderText("密码")

        main_layout.addWidget(self.username_edit)
        main_layout.addWidget(self.password_edit)

        btn_layout = QHBoxLayout()
        self.login_button = QPushButton("登录")
        self.login_button.clicked.connect(self.login)
        self.register_button = QPushButton("注册")
        self.register_button.clicked.connect(self.open_register)
        btn_layout.addWidget(self.login_button)
        btn_layout.addWidget(self.register_button)
        main_layout.addLayout(btn_layout)

        forgot_layout = QHBoxLayout()
        forgot_layout.addStretch()
        self.forgot_button = QPushButton("忘记密码")
        self.forgot_button.clicked.connect(self.open_forgot_password)
        forgot_layout.addWidget(self.forgot_button)
        main_layout.addLayout(forgot_layout)

        self.setLayout(main_layout)

    def login(self):
        username = self.username_edit.text().strip()
        password = self.password_edit.text().strip()

        user = get_user(username)
        if user is None:
            QMessageBox.warning(self, "错误", "用户不存在")
            return

        if verify_password(username, password):
            is_admin = (user[3] == 1)
            self.main_window = MainWindow(username, is_admin)
            self.main_window.show()
            self.close()
        else:
            QMessageBox.warning(self, "错误", "密码错误")

    def open_register(self):
        self.reg_window = RegisterWindow()
        self.reg_window.show()

    def open_forgot_password(self):
        self.forgot_window = ForgotPasswordWindow()
        self.forgot_window.show()


class RegisterWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("用户注册")
        layout = QVBoxLayout()

        self.username_edit = QLineEdit()
        self.username_edit.setPlaceholderText("请输入中文姓名")
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.Password)
        self.password_edit.setPlaceholderText("密码")
        self.confirm_edit = QLineEdit()
        self.confirm_edit.setEchoMode(QLineEdit.Password)
        self.confirm_edit.setPlaceholderText("确认密码")

        self.register_button = QPushButton("注册")
        self.register_button.clicked.connect(self.register)

        layout.addWidget(self.username_edit)
        layout.addWidget(self.password_edit)
        layout.addWidget(self.confirm_edit)
        layout.addWidget(self.register_button)
        self.setLayout(layout)

    def register(self):
        username = self.username_edit.text().strip()
        password = self.password_edit.text().strip()
        confirm = self.confirm_edit.text().strip()

        if username == "管理员":
            QMessageBox.warning(self, "错误", "不允许注册管理员用户")
            return

        if password != confirm:
            QMessageBox.warning(self, "错误", "两次输入的密码不一致")
            return

        if register_user(username, password, False):
            QMessageBox.information(self, "成功", "注册成功")
            self.close()
        else:
            QMessageBox.warning(self, "错误", "用户名已存在")


class ForgotPasswordWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("忘记密码")
        layout = QVBoxLayout()

        self.username_edit = QLineEdit()
        self.username_edit.setPlaceholderText("用户名")

        self.new_password_edit = QLineEdit()
        self.new_password_edit.setEchoMode(QLineEdit.Password)
        self.new_password_edit.setPlaceholderText("新密码")

        self.admin_password_edit = QLineEdit()
        self.admin_password_edit.setEchoMode(QLineEdit.Password)
        self.admin_password_edit.setPlaceholderText("管理员密码验证")

        layout.addWidget(self.username_edit)
        layout.addWidget(self.new_password_edit)
        layout.addWidget(self.admin_password_edit)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        self.reset_button = QPushButton("重置密码")
        self.reset_button.clicked.connect(self.reset_password)
        btn_layout.addWidget(self.reset_button)
        layout.addLayout(btn_layout)

        self.setLayout(layout)

    def reset_password(self):
        username = self.username_edit.text().strip()
        new_password = self.new_password_edit.text().strip()
        admin_password = self.admin_password_edit.text().strip()

        admin_username, ok = QInputDialog.getText(self, "管理员验证", "请输入管理员用户名:")
        if not ok or not admin_username.strip():
            return

        admin_user = get_user(admin_username.strip())
        if admin_user is None or admin_user[3] != 1:
            QMessageBox.warning(self, "错误", "管理员账号不存在或无权限")
            return

        if not verify_password(admin_username.strip(), admin_password):
            QMessageBox.warning(self, "错误", "管理员密码验证失败")
            return

        if update_password(username, new_password):
            QMessageBox.information(self, "成功", "密码重置成功")
            self.close()
        else:
            QMessageBox.warning(self, "错误", "用户不存在，无法重置")


class EntryDialog(QDialog):
    def __init__(self, is_admin=False, init_data=None):
        super().__init__()
        self.setWindowTitle("条目编辑")
        self.is_admin = is_admin

        self.editors = {}
        layout = QVBoxLayout()

        # 我们这里会要求username与姓名保持一致，为确保后续查询方便，请在新增、编辑时也维持这个逻辑。
        # 因此在对话框中依旧提供username字段，但最终存储时我们会强制将username = 姓名。
        # 为防止管理员手动修改出错，我们也可以选择直接不显示username编辑框。
        # 这里保留，以防管理员需要设置，但逻辑中强制username = 姓名。
        self.fields = ["username", "姓名", "点数", "基本奖", "CT", "CT照相摆位", "DX", "MR科研", "值班", "MG", "MR",
                       "急诊CT", "发热", "加班费", "床旁", "急诊补助", "穿刺", "值班补助", "授权职能", "其它", "奖金总计", "绩效", "年", "月"]
        for f in self.fields:
            hl = QHBoxLayout()
            label = QLabel(f"{f}:")
            edit = QLineEdit()
            hl.addWidget(label)
            hl.addWidget(edit)
            layout.addLayout(hl)
            self.editors[f] = edit

        if init_data:
            for f in self.fields:
                if f in init_data:
                    self.editors[f].setText(str(init_data[f]))

        btn_layout = QHBoxLayout()
        ok_btn = QPushButton("确定")
        ok_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

        self.setLayout(layout)

    def get_data(self):
        data = {}
        numeric_fields = ["点数", "基本奖", "CT", "CT照相摆位", "DX", "MR科研", "值班", "MG", "MR", "急诊CT", "发热",
                          "加班费", "床旁", "急诊补助", "穿刺", "值班补助", "授权职能","其它", "奖金总计" ,"绩效" ]
        for f in self.fields:
            text = self.editors[f].text().strip()
            if f in numeric_fields:
                try:
                    data[f] = float(text)
                except:
                    data[f] = 0.0
            elif f in ["年", "月"]:
                try:
                    data[f] = int(text)
                except:
                    data[f] = None
            else:
                data[f] = text

        # 强制username = 姓名，以便后续匹配注册用户名
        data["username"] = data.get("姓名", "")
        return data


class AdminChangePasswordDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("修改管理员密码")
        layout = QVBoxLayout()

        self.new_password_edit = QLineEdit()
        self.new_password_edit.setEchoMode(QLineEdit.Password)
        self.new_password_edit.setPlaceholderText("新密码")

        self.confirm_password_edit = QLineEdit()
        self.confirm_password_edit.setEchoMode(QLineEdit.Password)
        self.confirm_password_edit.setPlaceholderText("确认新密码")

        layout.addWidget(QLabel("新密码:"))
        layout.addWidget(self.new_password_edit)
        layout.addWidget(QLabel("确认新密码:"))
        layout.addWidget(self.confirm_password_edit)

        btn_layout = QHBoxLayout()
        ok_btn = QPushButton("确定")
        ok_btn.clicked.connect(self.change_password)
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

        self.setLayout(layout)

    def change_password(self):
        p1 = self.new_password_edit.text().strip()
        p2 = self.confirm_password_edit.text().strip()
        if p1 != p2:
            QMessageBox.warning(self, "错误", "两次输入的密码不一致")
            return
        if update_password("管理员", p1):
            QMessageBox.information(self, "成功", "管理员密码修改成功")
            self.accept()
        else:
            QMessageBox.warning(self, "错误", "修改失败")


class MainWindow(QMainWindow):
    def __init__(self, username, is_admin):
        super().__init__()
        self.username = username
        self.is_admin = is_admin
        self.setWindowTitle("工资查询与管理系统")
        self.resize(1400, 500)

        self.year_filter = None
        self.month_filter = None
        self.search_name = None
        self.filter_user = None

        central_widget = QWidget()
        main_layout = QVBoxLayout()

        top_layout = QHBoxLayout()

        self.year_combo = QComboBox()
        self.year_combo.addItem("所有年份")
        for y in range(2024, 2101):
            self.year_combo.addItem(str(y))
        self.year_combo.currentIndexChanged.connect(self.apply_filters)

        self.month_combo = QComboBox()
        self.month_combo.addItem("所有月份")
        for m in range(1, 13):
            self.month_combo.addItem(str(m))
        self.month_combo.currentIndexChanged.connect(self.apply_filters)

        top_layout.addWidget(QLabel("年份筛选:"))
        top_layout.addWidget(self.year_combo)
        top_layout.addWidget(QLabel("月份筛选:"))
        top_layout.addWidget(self.month_combo)

        if self.is_admin:
            self.search_edit = QLineEdit()
            self.search_edit.setPlaceholderText("根据姓名搜索")
            self.search_edit.textChanged.connect(self.apply_filters)

            self.user_combo = QComboBox()
            self.user_combo.addItem("所有用户")
            all_names = get_all_names_from_wages()
            for n in all_names:
                self.user_combo.addItem(n)
            self.user_combo.currentIndexChanged.connect(self.apply_filters)

            top_layout.addWidget(self.search_edit)
            top_layout.addWidget(QLabel("用户筛选:"))
            top_layout.addWidget(self.user_combo)
        else:
            self.search_edit = None
            self.user_combo = None

        main_layout.addLayout(top_layout)

        self.table = QTableWidget()
        headers = ["id", "username", "姓名", "点数", "基本奖", "CT", "CT照相摆位", "DX", "MR科研", "值班", "MG", "MR",
                   "急诊CT", "发热", "加班费", "床旁", "急诊补助", "穿刺", "值班补助", "授权职能",  "其它", "奖金总计","绩效", "年", "月"]
        self.all_headers = headers
        self.display_headers = ["姓名", "点数", "基本奖", "CT", "CT照相摆位", "DX", "MR科研", "值班", "MG", "MR",
                                "急诊CT", "发热", "加班费", "床旁", "急诊补助", "穿刺", "值班补助", "授权职能", "其它", "奖金总计", "绩效"]
        self.table.setColumnCount(len(self.all_headers))
        self.table.setHorizontalHeaderLabels(self.all_headers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        main_layout.addWidget(self.table)

        bottom_layout = QHBoxLayout()
        self.back_button = QPushButton("回退")
        self.back_button.clicked.connect(self.go_back)

        bottom_layout.addWidget(self.back_button)
        bottom_layout.addStretch()

        if self.is_admin:
            self.add_button = QPushButton("增加条目")
            self.add_button.clicked.connect(self.add_entry)
            bottom_layout.addWidget(self.add_button)

            self.edit_button = QPushButton("编辑选中条目")
            self.edit_button.clicked.connect(self.edit_entry)
            bottom_layout.addWidget(self.edit_button)

            self.delete_button = QPushButton("删除选中条目")
            self.delete_button.clicked.connect(self.delete_entry)
            bottom_layout.addWidget(self.delete_button)

            self.import_button = QPushButton("导入Excel/CSV")
            self.import_button.clicked.connect(self.import_data)
            bottom_layout.addWidget(self.import_button)

            self.admin_change_pass_button = QPushButton("修改管理员密码")
            self.admin_change_pass_button.clicked.connect(self.change_admin_password)
            bottom_layout.addWidget(self.admin_change_pass_button)

        self.export_button = QPushButton("导出当前页面为PDF")
        self.export_button.clicked.connect(self.export_pdf)
        bottom_layout.addWidget(self.export_button)

        main_layout.addLayout(bottom_layout)

        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

        self.load_data()
        self.set_default_year_month()

    def set_default_year_month(self):
        y, m = get_latest_year_month()
        if y and m:
            year_index = self.year_combo.findText(str(y))
            if year_index >= 0:
                self.year_combo.setCurrentIndex(year_index)
            month_index = self.month_combo.findText(str(m))
            if month_index >= 0:
                self.month_combo.setCurrentIndex(month_index)
            self.apply_filters()

    def load_data(self):
        if self.year_combo.currentIndex() == 0:
            year = None
        else:
            year = int(self.year_combo.currentText())

        if self.month_combo.currentIndex() == 0:
            month = None
        else:
            month = int(self.month_combo.currentText())

        search_name = None
        if self.is_admin and self.search_edit:
            search_name = self.search_edit.text().strip() if self.search_edit.text() else None

        filter_user = None
        if self.is_admin and self.user_combo:
            filter_user = self.user_combo.currentText()

        rows = query_wages(self.username, self.is_admin, year, month, search_name, filter_user)
        self.table.setRowCount(len(rows))
        for i, row in enumerate(rows):
            for j, val in enumerate(row):
                item = QTableWidgetItem(str(val) if val is not None else "")
                self.table.setItem(i, j, item)

        id_col = self.all_headers.index("id")
        username_col = self.all_headers.index("username")
        year_col = self.all_headers.index("年")
        month_col = self.all_headers.index("月")

        self.table.setColumnHidden(id_col, True)
        self.table.setColumnHidden(username_col, True)
        self.table.setColumnHidden(year_col, True)
        self.table.setColumnHidden(month_col, True)

    def apply_filters(self):
        self.load_data()

    def add_entry(self):
        dialog = EntryDialog(is_admin=True)
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_data()
            # username = 姓名
            row = [
                data.get("姓名", ""),  # username = 姓名
                data.get("姓名", ""),
                data.get("点数", 0.0),
                data.get("基本奖", 0.0),
                data.get("CT", 0.0),
                data.get("CT照相摆位", 0.0),
                data.get("DX", 0.0),
                data.get("MR科研", 0.0),
                data.get("值班", 0.0),
                data.get("MG", 0.0),
                data.get("MR", 0.0),
                data.get("急诊CT", 0.0),
                data.get("发热", 0.0),
                data.get("加班费", 0.0),
                data.get("床旁", 0.0),
                data.get("急诊补助", 0.0),
                data.get("穿刺", 0.0),
                data.get("值班补助", 0.0),
                data.get("授权职能", 0.0),
                data.get("其它", 0.0),
                data.get("奖金总计", 0.0),
                data.get("绩效", 0.0),
                data.get("年", None),
                data.get("月", None)
            ]
            # 将username（第一列）改为和姓名一致
            row[0] = row[1]  # username = 姓名
            insert_wage_data(tuple(row))
            self.load_data()

    def edit_entry(self):
        selected = self.table.currentRow()
        if selected < 0:
            QMessageBox.warning(self, "警告", "请先选择一行进行编辑")
            return
        row_data = {}
        for i, col_name in enumerate(self.all_headers):
            item = self.table.item(selected, i)
            row_data[col_name] = item.text() if item else ""

        dialog = EntryDialog(is_admin=True, init_data=row_data)
        if dialog.exec_() == QDialog.Accepted:
            new_data = dialog.get_data()
            wage_id = int(row_data["id"])
            # username = 姓名
            new_data["username"] = new_data.get("姓名", "")
            update_wage_data(wage_id, new_data)
            self.load_data()

    def delete_entry(self):
        selected = self.table.currentRow()
        if selected < 0:
            QMessageBox.warning(self, "警告", "请先选择一行进行删除")
            return
        item = self.table.item(selected, 0)
        if not item:
            return
        wage_id = int(item.text())
        reply = QMessageBox.question(self, "确认", "确定要删除此条目吗？", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            delete_wage_data(wage_id)
            self.load_data()

    def import_data(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "选择Excel或CSV文件", "", "Excel/CSV Files (*.xlsx *.xls *.csv)")
        if not file_path:
            return
        try:
            if file_path.endswith(".csv"):
                df = pd.read_csv(file_path)
            else:
                df = pd.read_excel(file_path)

            expected_cols = ["姓名", "点数", "基本奖", "CT", "CT照相摆位", "DX", "MR科研", "值班", "MG", "MR", "急诊CT", "发热",
                "加班费", "床旁", "急诊补助", "穿刺", "值班补助", "授权职能", "其它", "奖金总计", "绩效", "时间"]
            for col in expected_cols:
                if col not in df.columns:
                    QMessageBox.warning(self, "错误", f"导入文件中缺少列: {col}")
                    return

            def parse_year_month(x):
                if "-" in str(x):
                    parts = str(x).split("-")
                elif "/" in str(x):
                    parts = str(x).split("/")
                else:
                    now = datetime.datetime.now()
                    return now.year, now.month
                if len(parts) >= 2:
                    try:
                        year = int(parts[0])
                        month = int(parts[1])
                        return year, month
                    except:
                        now = datetime.datetime.now()
                        return now.year, now.month
                else:
                    now = datetime.datetime.now()
                    return now.year, now.month

            if len(df) > 0:
                first_time = df.iloc[0]["时间"]
                年, 月 = parse_year_month(first_time)
            else:
                return

            for idx, row in df.iterrows():
                姓名 = row["姓名"]
                # 关键改动：无论用户是否注册，username始终设为姓名。
                username = 姓名

                line = [
                    username,
                    姓名,
                    row["点数"], row["基本奖"], row["CT"], row["CT照相摆位"], row["DX"], row["MR科研"], row["值班"],
                    row["MG"], row["MR"], row["急诊CT"], row["发热"], row["加班费"], row["床旁"], row["急诊补助"],
                    row["穿刺"], row["值班补助"], row["授权职能"], row["其它"], row["奖金总计"],row["绩效"],
                    年, 月
                ]
                insert_wage_data(tuple(line))

            self.load_data()
            QMessageBox.information(self, "成功", "数据导入成功！")

            if self.is_admin and self.user_combo:
                self.user_combo.clear()
                self.user_combo.addItem("所有用户")
                all_names = get_all_names_from_wages()
                for n in all_names:
                    self.user_combo.addItem(n)

        except Exception as e:
            QMessageBox.warning(self, "错误", f"导入数据失败: {e}")

    def export_pdf(self):
        printer = QPrinter(QPrinter.HighResolution)
        printer.setOutputFormat(QPrinter.PdfFormat)
        file_path, _ = QFileDialog.getSaveFileName(self, "导出PDF", "", "PDF Files (*.pdf)")
        if not file_path:
           return
        printer.setOutputFileName(file_path)
    
    # 构建HTML表格
        html = "<html><head><meta charset='utf-8'></head><body>"
        html += "<table border='1' cellspacing='0' cellpadding='1.5' style='font-size:5pt; border-collapse:collapse; width:250%; line-height:0.1'>"
    # 表头
        html += "<tr>"
        for col in self.display_headers:
            html += f"<th>{col}</th>"
        html += "</tr>"
    # 数据行
        row_count = self.table.rowCount()
        for r in range(row_count):
            html += "<tr>"
            for col_header in self.display_headers:
                col_index = self.all_headers.index(col_header)
                item = self.table.item(r, col_index)
                text = item.text() if item else ""
                html += f"<td>{text}</td>"
            html += "</tr>"

        html += "</table></body></html>"

    # 使用QTextDocument打印
        document = QTextDocument()
        document.setHtml(html)
        document.print(printer)

        QMessageBox.information(self, "成功", "导出成功！")
    #def export_pdf(self):
        #printer = QPrinter(QPrinter.HighResolution)
        #printer.setOutputFormat(QPrinter.PdfFormat)
        #file_path, _ = QFileDialog.getSaveFileName(self, "导出PDF", "", "PDF Files (*.pdf)")
        #if file_path:
            #printer.setOutputFileName(file_path)
            #painter = QtGui.QPainter(printer)
            #painter.setRenderHint(QtGui.QPainter.Antialiasing)

            #show_cols = []
           # for h in self.display_headers:
                #show_cols.append(self.all_headers.index(h))

           # start_y = 50
           # start_x = 50
           # row_height = 30
           # page_width = printer.pageRect().width()
           # col_count = len(show_cols)
           # col_width = page_width // (col_count + 1)

           # x = start_x
           # for col in show_cols:
           #     painter.drawText(x, start_y, self.all_headers[col])
            #    x += col_width

            #row_count = self.table.rowCount()
           # y = start_y + row_height
            #for r in range(row_count):
             #   x = start_x
             #   for col in show_cols:
             #       item = self.table.item(r, col)
             #       text = item.text() if item else ""
              #      painter.drawText(x, y, text)
              #      x += col_width
              #  y += row_height

              #  if y > printer.pageRect().bottom() - 50:
                 #   printer.newPage()
                 #   y = start_y + row_height
                 #   x = start_x
                 #   for col in show_cols:
                   #     painter.drawText(x, start_y, self.all_headers[col])
                  #      x += col_width
            #font = painter.font()
            #font.setPointSize(3)  # 设置较小的字体大小
           # painter.setFont(font)

            # 假设 col_width 已根据页面宽度和列数进行了合理分配
            # 使用 drawText 的 QRectF 来确定文本区域，避免重叠
            #painter.drawText(QtCore.QRectF(x, y - row_height, col_width, row_height),
                 #QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter,
                 #text)            
            #painter.end()
            #QMessageBox.information(self, "成功", "导出成功！")

    def change_admin_password(self):
        dialog = AdminChangePasswordDialog()
        dialog.exec_()

    def go_back(self):
        self.close()
        self.login_window = LoginWindow()
        self.login_window.show()


if __name__ == "__main__":
    init_db()
    app = QApplication(sys.argv)
    login_window = LoginWindow()
    login_window.show()
    sys.exit(app.exec_())
