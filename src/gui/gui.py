import traceback
from pathlib import Path

from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSettings
from PyQt6.QtWidgets import (
    QWidget,
    QLabel,
    QPushButton,
    QTextEdit,
    QFileDialog,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QLineEdit,
    QMessageBox,
    QDialog,
    QDialogButtonBox,
    QGroupBox,
)

from src.summarizer.summarizer_core import run_summarizer


# ------------------------------------------------------------
# Backend functions
# ------------------------------------------------------------

def summarize_pdf(pdf_path: Path, model_path: str, progress_callback):
    return run_summarizer(
        pdf_path=pdf_path,
        model_path=model_path,
        progress_callback=progress_callback,
    )


def ocr_pdf(pdf_path: Path, model_path: str, progress_callback):
    progress_callback("Starting OCR...")
    progress_callback(f"PDF: {pdf_path}")
    progress_callback(f"Model path/server: {model_path}")

    # TODO: Replace this with your real OCR pipeline.
    return f"# OCR Output\n\nOCR text from PDF: `{pdf_path.name}`\n"


def translate_pdf(pdf_path: Path, model_path: str, progress_callback):
    progress_callback("Starting translation...")
    progress_callback(f"PDF: {pdf_path}")
    progress_callback(f"Model path/server: {model_path}")

    # TODO: Replace this with your real translation pipeline.
    return f"# Translation\n\nTranslated PDF: `{pdf_path.name}`\n"


# ------------------------------------------------------------
# Settings Dialog
# ------------------------------------------------------------

class SettingsDialog(QDialog):
    def __init__(self, settings: QSettings, parent=None):
        super().__init__(parent)

        self.settings = settings
        self.setWindowTitle("Settings")
        self.resize(650, 160)

        self.model_path_input = QLineEdit()
        self.model_path_input.setPlaceholderText("Path to local model or LM Studio server URL")
        self.model_path_input.setText(self.settings.value("model_path", ""))

        self.browse_model_button = QPushButton("Browse")
        self.browse_model_button.clicked.connect(self.choose_model_path)

        model_path_layout = QHBoxLayout()
        model_path_layout.addWidget(self.model_path_input)
        model_path_layout.addWidget(self.browse_model_button)

        form_layout = QFormLayout()
        form_layout.addRow("Model path / server URL:", model_path_layout)

        self.buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )
        self.buttons.accepted.connect(self.save_settings)
        self.buttons.rejected.connect(self.reject)

        main_layout = QVBoxLayout()
        main_layout.addLayout(form_layout)
        main_layout.addWidget(self.buttons)

        self.setLayout(main_layout)

    def choose_model_path(self):
        path = QFileDialog.getExistingDirectory(
            self,
            "Choose Model Directory",
            "",
        )
        if path:
            self.model_path_input.setText(path)

    def save_settings(self):
        self.settings.setValue("model_path", self.model_path_input.text().strip())
        self.accept()


# ------------------------------------------------------------
# Worker Thread
# ------------------------------------------------------------

class Worker(QThread):
    progress = pyqtSignal(str)
    finished = pyqtSignal(str)
    failed = pyqtSignal(str)

    def __init__(self, task_name: str, pdf_path: Path, save_path: Path, model_path: str):
        super().__init__()
        self.task_name = task_name
        self.pdf_path = pdf_path
        self.save_path = save_path
        self.model_path = model_path

    def run(self):
        try:
            if self.task_name == "summarize":
                markdown = summarize_pdf(
                    self.pdf_path,
                    self.model_path,
                    self.progress.emit,
                )
            elif self.task_name == "ocr":
                markdown = ocr_pdf(
                    self.pdf_path,
                    self.model_path,
                    self.progress.emit,
                )
            elif self.task_name == "translate":
                markdown = translate_pdf(
                    self.pdf_path,
                    self.model_path,
                    self.progress.emit,
                )
            else:
                raise ValueError(f"Unknown task: {self.task_name}")

            self.save_path.write_text(markdown, encoding="utf-8")
            self.finished.emit(f"Saved output to:\n{self.save_path}")

        except Exception:
            self.failed.emit(traceback.format_exc())


# ------------------------------------------------------------
# Drag-and-drop PDF area
# ------------------------------------------------------------

class DropArea(QLabel):
    pdf_selected = pyqtSignal(Path)

    def __init__(self):
        super().__init__()
        self.setText("Drag and drop a PDF here\nor click to choose one")
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setAcceptDrops(True)
        self.setMinimumHeight(170)
        self.setStyleSheet("""
            QLabel {
                border: 2px dashed #777;
                border-radius: 12px;
                padding: 24px;
                font-size: 16px;
            }
        """)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if urls and urls[0].toLocalFile().lower().endswith(".pdf"):
                event.acceptProposedAction()

    def dropEvent(self, event):
        path = Path(event.mimeData().urls()[0].toLocalFile())
        if path.suffix.lower() == ".pdf":
            self.pdf_selected.emit(path)

    def mousePressEvent(self, event):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Choose PDF",
            "",
            "PDF Files (*.pdf)",
        )
        if file_path:
            self.pdf_selected.emit(Path(file_path))


# ------------------------------------------------------------
# Main GUI
# ------------------------------------------------------------

class HistorianToolkitGUI(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Local LLM Toolkit for Historical Text Analysis")
        self.resize(850, 650)

        self.settings = QSettings("GoodwinDH", "LocalLLMToolkit")
        self.pdf_path: Path | None = None
        self.worker: Worker | None = None

        self.drop_area = DropArea()
        self.drop_area.pdf_selected.connect(self.set_pdf)

        self.selected_pdf_label = QLabel("No PDF selected")

        self.summarize_button = QPushButton("Summarize")
        self.ocr_button = QPushButton("OCR")
        self.translate_button = QPushButton("Translate")
        self.settings_button = QPushButton("Settings")

        self.summarize_button.clicked.connect(lambda: self.start_task("summarize"))
        self.ocr_button.clicked.connect(lambda: self.start_task("ocr"))
        self.translate_button.clicked.connect(lambda: self.start_task("translate"))
        self.settings_button.clicked.connect(self.open_settings)

        self.progress_output = QTextEdit()
        self.progress_output.setReadOnly(True)

        self.build_layout()

    def build_layout(self):
        main_layout = QVBoxLayout()

        main_layout.addWidget(self.drop_area)
        main_layout.addWidget(self.selected_pdf_label)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.summarize_button)
        button_layout.addWidget(self.ocr_button)
        button_layout.addWidget(self.translate_button)
        button_layout.addWidget(self.settings_button)
        main_layout.addLayout(button_layout)

        progress_group = QGroupBox("Progress Output")
        progress_layout = QVBoxLayout()
        progress_layout.addWidget(self.progress_output)
        progress_group.setLayout(progress_layout)

        main_layout.addWidget(progress_group)

        self.setLayout(main_layout)

    def set_pdf(self, path: Path):
        self.pdf_path = path
        self.selected_pdf_label.setText(f"Selected PDF: {path}")
        self.log(f"Selected PDF: {path}")

    def open_settings(self):
        dialog = SettingsDialog(self.settings, self)
        if dialog.exec():
            self.log("Settings saved.")

    def start_task(self, task_name: str):
        if self.pdf_path is None:
            QMessageBox.warning(
                self,
                "No PDF Selected",
                "Please select a PDF first.",
            )
            return

        model_path = self.settings.value("model_path", "").strip()

        if not model_path:
            QMessageBox.warning(
                self,
                "Missing Model Setting",
                "Please open Settings and enter a model path or LM Studio server URL.",
            )
            return

        suggested_name = self.pdf_path.with_suffix("").name

        if task_name == "summarize":
            suggested_name += "_summary.md"
        elif task_name == "ocr":
            suggested_name += "_ocr.md"
        elif task_name == "translate":
            suggested_name += "_translation.md"

        save_path_str, _ = QFileDialog.getSaveFileName(
            self,
            "Save Markdown Output",
            str(self.pdf_path.parent / suggested_name),
            "Markdown Files (*.md)",
        )

        if not save_path_str:
            self.log("Save cancelled.")
            return

        save_path = Path(save_path_str)

        if save_path.suffix.lower() != ".md":
            save_path = save_path.with_suffix(".md")

        self.set_buttons_enabled(False)

        self.log(f"Starting task: {task_name}")
        self.log(f"Output will be saved to: {save_path}")

        self.worker = Worker(
            task_name=task_name,
            pdf_path=self.pdf_path,
            save_path=save_path,
            model_path=model_path,
        )

        self.worker.progress.connect(self.log)
        self.worker.finished.connect(self.task_finished)
        self.worker.failed.connect(self.task_failed)
        self.worker.start()

    def task_finished(self, message: str):
        self.log(message)
        self.log("Done.")
        self.set_buttons_enabled(True)

    def task_failed(self, error_text: str):
        self.log("ERROR:")
        self.log(error_text)
        QMessageBox.critical(self, "Task Failed", error_text)
        self.set_buttons_enabled(True)

    def set_buttons_enabled(self, enabled: bool):
        self.summarize_button.setEnabled(enabled)
        self.ocr_button.setEnabled(enabled)
        self.translate_button.setEnabled(enabled)
        self.settings_button.setEnabled(enabled)

    def log(self, message: str):
        self.progress_output.append(message)