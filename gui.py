"""PyQt6 GUI for Invoice Extractor"""

import sys
from pathlib import Path

from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QIcon
from PyQt6.QtWidgets import (
    QApplication,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from config import DEFAULT_OUTPUT_FILENAME
from financial import InvoiceExtractor


class WorkerThread(QThread):
    """后台工作线程，避免界面卡顿"""

    progress = pyqtSignal(str, int, int)  # 进度信号: (文件名, 已完成, 总数)
    finished = pyqtSignal(str)  # 完成信号: (输出文件路径)
    error = pyqtSignal(str)  # 错误信号: (错误信息)

    def __init__(self, pdf_paths: list[str], output_path: str):
        super().__init__()
        self.pdf_paths = pdf_paths
        self.output_path = output_path

    def run(self):
        """在后台线程中执行提取任务"""
        try:
            extractor = InvoiceExtractor()

            def progress_callback(filename: str, completed: int, total: int):
                self.progress.emit(filename, completed, total)

            extractor.extract_to_excel(
                pdf_paths=self.pdf_paths,
                excel_path=self.output_path,
                progress_callback=progress_callback,
            )
            self.finished.emit(self.output_path)
        except Exception as e:
            self.error.emit(str(e))


class MainWindow(QMainWindow):
    """主窗口"""

    def __init__(self):
        super().__init__()
        self.pdf_files = []
        self.output_path = ""
        self.worker_thread = None

        self.init_ui()

    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle("阿珍的发票解析工具")
        self.setGeometry(100, 100, 900, 700)

        # 中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 主布局
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)

        # 标题
        title = QLabel("📄 阿珍的发票解析工具")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title)

        # 文件选择区域
        file_section = QVBoxLayout()
        file_label = QLabel("1. 选择PDF发票文件:")
        file_label_font = QFont()
        file_label_font.setPointSize(12)
        file_label_font.setBold(True)
        file_label.setFont(file_label_font)
        file_section.addWidget(file_label)

        # 文件列表
        self.file_list = QListWidget()
        self.file_list.setMaximumHeight(150)
        file_section.addWidget(self.file_list)

        # 文件按钮
        file_buttons = QHBoxLayout()
        self.add_files_btn = QPushButton("添加文件")
        self.add_files_btn.clicked.connect(self.add_files)
        self.clear_files_btn = QPushButton("清空列表")
        self.clear_files_btn.clicked.connect(self.clear_files)
        file_buttons.addWidget(self.add_files_btn)
        file_buttons.addWidget(self.clear_files_btn)
        file_buttons.addStretch()
        file_section.addLayout(file_buttons)

        main_layout.addLayout(file_section)

        # 输出路径选择
        output_section = QVBoxLayout()
        output_label = QLabel("2. 选择输出Excel文件路径:")
        output_label.setFont(file_label_font)
        output_section.addWidget(output_label)

        output_path_layout = QHBoxLayout()
        self.output_path_label = QLabel("未选择")
        self.output_path_label.setStyleSheet("padding: 5px; background-color: #f0f0f0; border-radius: 3px;")
        output_path_layout.addWidget(self.output_path_label)
        self.select_output_btn = QPushButton("选择路径")
        self.select_output_btn.clicked.connect(self.select_output_path)
        output_path_layout.addWidget(self.select_output_btn)
        output_section.addLayout(output_path_layout)

        main_layout.addLayout(output_section)

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)

        # 控制台输出区域
        console_label = QLabel("3. 处理日志:")
        console_label.setFont(file_label_font)
        main_layout.addWidget(console_label)

        self.console = QTextEdit()
        self.console.setReadOnly(True)
        self.console.setStyleSheet(
            "background-color: #1e1e1e; color: #d4d4d4; font-family: Consolas, Monaco, monospace;"
        )
        main_layout.addWidget(self.console)

        # 执行按钮
        self.execute_btn = QPushButton("开始生成Excel")
        self.execute_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #0066cc;
                color: white;
                font-size: 14px;
                font-weight: bold;
                padding: 10px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #0052a3;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """
        )
        self.execute_btn.clicked.connect(self.execute)
        main_layout.addWidget(self.execute_btn)

    def add_files(self):
        """添加PDF文件"""
        files, _ = QFileDialog.getOpenFileNames(self, "选择PDF发票文件", "", "PDF Files (*.pdf);;All Files (*)")
        if files:
            for file in files:
                if file not in self.pdf_files:
                    self.pdf_files.append(file)
                    self.file_list.addItem(Path(file).name)
            self.log(f"已添加 {len(files)} 个文件")

    def clear_files(self):
        """清空文件列表"""
        self.pdf_files.clear()
        self.file_list.clear()
        self.log("文件列表已清空")

    def select_output_path(self):
        """选择输出路径"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存Excel文件", DEFAULT_OUTPUT_FILENAME, "Excel Files (*.xlsx);;All Files (*)"
        )
        if file_path:
            if not file_path.endswith(".xlsx"):
                file_path += ".xlsx"
            self.output_path = file_path
            self.output_path_label.setText(file_path)
            self.log(f"输出路径已设置: {file_path}")

    def log(self, message: str):
        """输出日志到控制台"""
        self.console.append(message)
        # 自动滚动到底部
        consoleBar = self.console.verticalScrollBar()
        assert consoleBar
        consoleBar.setValue(consoleBar.maximum())

    def execute(self):
        """执行发票提取"""
        # 验证输入
        if not self.pdf_files:
            QMessageBox.warning(self, "警告", "请先添加PDF文件！")
            return

        if not self.output_path:
            QMessageBox.warning(self, "警告", "请先选择输出路径！")
            return

        # 禁用按钮
        self.execute_btn.setEnabled(False)
        self.add_files_btn.setEnabled(False)
        self.clear_files_btn.setEnabled(False)
        self.select_output_btn.setEnabled(False)

        # 显示进度条
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.progress_bar.setMaximum(len(self.pdf_files))

        # 清空控制台
        self.console.clear()
        self.log("=" * 50)
        self.log(f"开始处理 {len(self.pdf_files)} 个PDF文件...")
        self.log("=" * 50)

        # 启动后台线程
        self.worker_thread = WorkerThread(self.pdf_files, self.output_path)
        self.worker_thread.progress.connect(self.on_progress)
        self.worker_thread.finished.connect(self.on_finished)
        self.worker_thread.error.connect(self.on_error)
        self.worker_thread.start()

    def on_progress(self, filename: str, completed: int, total: int):
        """进度更新"""
        self.progress_bar.setValue(completed)
        self.log(f"✓ 已完成: {filename} ({completed}/{total})")

    def on_finished(self, output_path: str):
        """任务完成"""
        self.progress_bar.setValue(self.progress_bar.maximum())
        self.log("=" * 50)
        self.log("✓ 全部完成！Excel文件已保存到:")
        self.log(f"  {output_path}")
        self.log("=" * 50)

        # 恢复按钮
        self.execute_btn.setEnabled(True)
        self.add_files_btn.setEnabled(True)
        self.clear_files_btn.setEnabled(True)
        self.select_output_btn.setEnabled(True)

        QMessageBox.information(self, "完成", f"处理完成！\n\nExcel文件已保存到:\n{output_path}")

    def on_error(self, error_msg: str):
        """错误处理"""
        self.log("=" * 50)
        self.log(f"✗ 错误: {error_msg}")
        self.log("=" * 50)

        # 恢复按钮
        self.execute_btn.setEnabled(True)
        self.add_files_btn.setEnabled(True)
        self.clear_files_btn.setEnabled(True)
        self.select_output_btn.setEnabled(True)
        self.progress_bar.setVisible(False)

        QMessageBox.critical(self, "错误", f"处理过程中出现错误:\n\n{error_msg}")


def main():
    """主函数"""
    app = QApplication(sys.argv)
    icon_path = Path(__file__).parent / 'financial.jpg'
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
