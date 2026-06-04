import traceback
from pathlib import Path

try:
    import pytesseract
except ImportError:
    pytesseract = None

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
    QComboBox,
    QCheckBox,
    QListWidget,
    QListWidgetItem,
    QAbstractItemView,
)

from src.summarizer.summarizer_core import analytical_summarize_pdf
from src.summarizer.summarizer_core import simple_summarize_pdf
from src.ner.entity_core import named_entity_recognition_pdf
from src.ocr.ocr_core import run_ocr
try:
    from src.translation.translation_core import translate_pdf
except ImportError:
    translate_pdf = None


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
# Tesseract language helpers
# ------------------------------------------------------------

TESSERACT_LANGUAGE_NAMES = {
    "afr": "Afrikaans",
    "ara": "Arabic",
    "ben": "Bengali",
    "bul": "Bulgarian",
    "cat": "Catalan",
    "ces": "Czech",
    "chi_sim": "Chinese - Simplified",
    "chi_tra": "Chinese - Traditional",
    "dan": "Danish",
    "deu": "German",
    "ell": "Greek",
    "eng": "English",
    "enm": "English, Middle",
    "fin": "Finnish",
    "fra": "French",
    "frk": "German, Fraktur",
    "frm": "French, Middle",
    "heb": "Hebrew",
    "hin": "Hindi",
    "hrv": "Croatian",
    "hun": "Hungarian",
    "ita": "Italian",
    "ita_old": "Italian, Old",
    "jpn": "Japanese",
    "lat": "Latin",
    "nld": "Dutch",
    "nor": "Norwegian",
    "pol": "Polish",
    "por": "Portuguese",
    "ron": "Romanian",
    "rus": "Russian",
    "slk": "Slovak",
    "slv": "Slovenian",
    "spa": "Spanish",
    "swe": "Swedish",
    "tur": "Turkish",
    "ukr": "Ukrainian",
}


def get_installed_tesseract_languages() -> list[str]:
    """Return installed Tesseract OCR languages, excluding OSD.

    Falls back to English if Tesseract or pytesseract is unavailable so the
    dialog remains usable and the error can surface later during OCR.
    """
    if pytesseract is None:
        return ["eng"]

    try:
        languages = pytesseract.get_languages(config="")
    except Exception:
        return ["eng"]

    languages = sorted(lang for lang in languages if lang != "osd")
    return languages or ["eng"]


def display_tesseract_language(code: str) -> str:
    name = TESSERACT_LANGUAGE_NAMES.get(code, code)
    return f"{name} ({code})"


# ------------------------------------------------------------
# OCR Options Dialog
# ------------------------------------------------------------

class OCROptionsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("OCR Options")
        self.resize(460, 220)

        self.ocr_mode_combo = QComboBox()
        self.ocr_mode_combo.addItem("Extract pre-existing OCR text", "extract_text")
        self.ocr_mode_combo.addItem("Tesseract only", "tesseract")
        self.ocr_mode_combo.addItem("LLM Vision only", "vision_llm")
        self.ocr_mode_combo.addItem("Tesseract + LLM Vision", "tesseract_plus_vision")

        self.tesseract_language_combo = QComboBox()
        for code in get_installed_tesseract_languages():
            self.tesseract_language_combo.addItem(display_tesseract_language(code), code)

        default_language_index = self.tesseract_language_combo.findData("eng")
        if default_language_index >= 0:
            self.tesseract_language_combo.setCurrentIndex(default_language_index)

        self.ocr_mode_combo.currentIndexChanged.connect(self.update_tesseract_language_enabled)

        self.preprocess_combo = QComboBox()
        self.preprocess_combo.addItem("None", "none")
        self.preprocess_combo.addItem("Basic - recommended", "basic")
        self.preprocess_combo.addItem("Archival - aggressive", "archival")
        self.preprocess_combo.setCurrentIndex(1)
        
        self.save_images_checkbox = QCheckBox("Save rendered page images")
        self.save_images_checkbox.setChecked(False)

        form_layout = QFormLayout()
        form_layout.addRow("OCR method:", self.ocr_mode_combo)
        form_layout.addRow("Tesseract language:", self.tesseract_language_combo)
        form_layout.addRow("Image preprocessing:", self.preprocess_combo)
        form_layout.addRow("", self.save_images_checkbox)

        self.buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
        )
        self.buttons.button(QDialogButtonBox.StandardButton.Ok).setText("Start")
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)

        main_layout = QVBoxLayout()
        main_layout.addLayout(form_layout)
        main_layout.addWidget(self.buttons)

        self.setLayout(main_layout)
        self.update_tesseract_language_enabled()

    def update_tesseract_language_enabled(self):
        uses_tesseract = self.selected_ocr_mode() in {"tesseract", "tesseract_plus_vision"}
        self.tesseract_language_combo.setEnabled(uses_tesseract)

    def selected_ocr_mode(self) -> str:
        return self.ocr_mode_combo.currentData()

    def selected_preprocess_mode(self) -> str:
        return self.preprocess_combo.currentData()

    def selected_tesseract_language(self) -> str:
        return self.tesseract_language_combo.currentData() or "eng"
    
    def should_save_page_images(self) -> bool:
        return self.save_images_checkbox.isChecked()

# ------------------------------------------------------------
# Worker Thread
# ------------------------------------------------------------
# ------------------------------------------------------------
# Worker Thread
# ------------------------------------------------------------

TASK_OUTPUT_SUFFIXES = {
    "analytical_summarize": "_analytical_summary.md",
    "simple_summarize": "_simple_summary.md",
    "ner": "_entities.md",
    "ocr": "_ocr.txt",
    "translate": "_translation.md",
}

TASK_LABELS = {
    "analytical_summarize": "Analytical Summarizer",
    "simple_summarize": "Simple Narrative Summarizer",
    "ner": "Named Entity Recognition",
    "ocr": "OCR",
    "translate": "Translate",
}


TRANSLATION_TARGET_LANGUAGES = [
    ("English", "English"),
    ("German", "German"),
    ("French", "French"),
    ("Spanish", "Spanish"),
    ("Italian", "Italian"),
    ("Portuguese", "Portuguese"),
    ("Dutch", "Dutch"),
    ("Polish", "Polish"),
    ("Russian", "Russian"),
    ("Ukrainian", "Ukrainian"),
    ("Czech", "Czech"),
    ("Slovak", "Slovak"),
    ("Hungarian", "Hungarian"),
    ("Romanian", "Romanian"),
    ("Bulgarian", "Bulgarian"),
    ("Serbian", "Serbian"),
    ("Croatian", "Croatian"),
    ("Bosnian", "Bosnian"),
    ("Slovenian", "Slovenian"),
    ("Macedonian", "Macedonian"),
    ("Albanian", "Albanian"),
    ("Greek", "Greek"),
    ("Turkish", "Turkish"),
    ("Arabic", "Arabic"),
    ("Hebrew", "Hebrew"),
    ("Persian (Farsi)", "Persian (Farsi)"),
    ("Chinese (Simplified)", "Chinese (Simplified)"),
    ("Chinese (Traditional)", "Chinese (Traditional)"),
    ("Japanese", "Japanese"),
    ("Korean", "Korean"),
    ("Vietnamese", "Vietnamese"),
    ("Thai", "Thai"),
    ("Indonesian", "Indonesian"),
    ("Malay", "Malay"),
    ("Hindi", "Hindi"),
    ("Urdu", "Urdu"),
    ("Bengali", "Bengali"),
    ("Tamil", "Tamil"),
    ("Telugu", "Telugu"),
    ("Marathi", "Marathi"),
    ("Gujarati", "Gujarati"),
    ("Punjabi", "Punjabi"),
    ("Sanskrit", "Sanskrit"),
    ("Latin", "Latin"),
    ("Ancient Greek", "Ancient Greek"),
    ("Old English", "Old English"),
    ("Middle English", "Middle English"),
    ("Old French", "Old French"),
    ("Middle High German", "Middle High German"),
    ("Old Norse", "Old Norse"),
    ("Danish", "Danish"),
    ("Norwegian", "Norwegian"),
    ("Swedish", "Swedish"),
    ("Finnish", "Finnish"),
    ("Estonian", "Estonian"),
    ("Latvian", "Latvian"),
    ("Lithuanian", "Lithuanian"),
    ("Irish", "Irish"),
    ("Scottish Gaelic", "Scottish Gaelic"),
    ("Welsh", "Welsh"),
    ("Basque", "Basque"),
    ("Catalan", "Catalan"),
    ("Galician", "Galician"),
    ("Occitan", "Occitan"),
    ("Afrikaans", "Afrikaans"),
    ("Swahili", "Swahili"),
    ("Amharic", "Amharic"),
]


class Worker(QThread):
    progress = pyqtSignal(str)
    finished = pyqtSignal(str)
    failed = pyqtSignal(str)

    def __init__(
        self,
        tasks: list[str],
        pdf_paths: list[Path],
        model_path: str,
        ocr_mode: str = "extract_text",
        preprocess_mode: str = "basic",
        save_page_images: bool = False,
        tesseract_language: str = "eng",
        target_language: str = "English",
    ):
        super().__init__()
        self.tasks = tasks
        self.pdf_paths = pdf_paths
        self.model_path = model_path
        self.ocr_mode = ocr_mode
        self.preprocess_mode = preprocess_mode
        self.save_page_images = save_page_images
        self.tesseract_language = tesseract_language
        self.target_language = target_language

    def output_path_for(self, pdf_path: Path, task_name: str) -> Path:
        if task_name == "translate":
            safe_language = self.target_language.lower().replace(" ", "_")
            return pdf_path.parent / f"{pdf_path.stem}_translated_{safe_language}.md"

        suffix = TASK_OUTPUT_SUFFIXES[task_name]
        return pdf_path.parent / f"{pdf_path.stem}{suffix}"

    def run_task(self, task_name: str, pdf_path: Path) -> str:
        if task_name == "analytical_summarize":
            return analytical_summarize_pdf(
                pdf_path,
                self.model_path,
                self.progress.emit,
            )

        if task_name == "simple_summarize":
            return simple_summarize_pdf(
                pdf_path,
                self.model_path,
                self.progress.emit,
            )

        if task_name == "ner":
            return named_entity_recognition_pdf(
                pdf_path,
                self.model_path,
                self.progress.emit,
            )

        if task_name == "ocr":
            result = run_ocr(
                input_path=pdf_path,
                output_dir=pdf_path.parent,
                mode=self.ocr_mode or "extract_text",
                model_path=self.model_path,
                preprocess_mode=self.preprocess_mode or "basic",
                save_txt=False,
                save_page_images=self.save_page_images,
                tesseract_language=self.tesseract_language,
                progress_callback=self.progress.emit,
            )
            return result.full_text

        if task_name == "translate":
            if translate_pdf is None:
                raise RuntimeError(
                    "Translation is selected, but src.translation.translation_core.translate_pdf "
                    "could not be imported. Re-enable or implement the translation backend first."
                )
            return translate_pdf(
                pdf_path=pdf_path,
                model_path=self.model_path,
                target_language=self.target_language,
                progress_callback=self.progress.emit,
                ocr_mode=self.ocr_mode or "extract_text",
                preprocess_mode=self.preprocess_mode or "basic",
                save_page_images=self.save_page_images,
                tesseract_language=self.tesseract_language,
            )

        raise ValueError(f"Unknown task: {task_name}")

    def run(self):
        try:
            outputs_written: list[Path] = []

            for pdf_index, pdf_path in enumerate(self.pdf_paths, start=1):
                self.progress.emit("")
                self.progress.emit(f"Processing document {pdf_index} of {len(self.pdf_paths)}: {pdf_path.name}")

                for task_index, task_name in enumerate(self.tasks, start=1):
                    label = TASK_LABELS.get(task_name, task_name)
                    save_path = self.output_path_for(pdf_path, task_name)

                    self.progress.emit(f"Starting {label} ({task_index} of {len(self.tasks)})")
                    self.progress.emit(f"Output will be saved to: {save_path}")

                    markdown = self.run_task(task_name, pdf_path)
                    save_path.write_text(markdown, encoding="utf-8")
                    outputs_written.append(save_path)

                    self.progress.emit(f"Saved output to: {save_path}")

            self.finished.emit(f"Finished. Wrote {len(outputs_written)} output file(s).")

        except Exception:
            self.failed.emit(traceback.format_exc())


# ------------------------------------------------------------
# Drag-and-drop PDF list
# ------------------------------------------------------------

class PDFListWidget(QListWidget):
    pdfs_dropped = pyqtSignal(list)

    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.setMinimumHeight(170)
        self.setToolTip("Drag and drop PDF files here.")
        self.setStyleSheet("""
            QListWidget {
                border: 2px dashed #777;
                border-radius: 12px;
                padding: 8px;
                font-size: 14px;
            }
        """)

    def dragEnterEvent(self, event):
        if self._event_has_pdf_urls(event):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if self._event_has_pdf_urls(event):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        pdf_paths = self._pdf_paths_from_event(event)
        if pdf_paths:
            self.pdfs_dropped.emit(pdf_paths)
            event.acceptProposedAction()
        else:
            event.ignore()

    def _event_has_pdf_urls(self, event) -> bool:
        return bool(self._pdf_paths_from_event(event))

    def _pdf_paths_from_event(self, event) -> list[Path]:
        if not event.mimeData().hasUrls():
            return []

        return [
            Path(url.toLocalFile())
            for url in event.mimeData().urls()
            if url.isLocalFile() and url.toLocalFile().lower().endswith(".pdf")
        ]


# ------------------------------------------------------------
# Main GUI
# ------------------------------------------------------------

class HistorianToolkitGUI(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Local LLM Toolkit for Historical Text Analysis")
        self.resize(900, 760)

        self.settings = QSettings("GoodwinDH", "LocalLLMToolkit")
        self.pdf_paths: list[Path] = []
        self.worker: Worker | None = None

        self.pdf_list = PDFListWidget()
        self.pdf_list.pdfs_dropped.connect(self.add_pdfs)

        self.add_files_button = QPushButton("Add Files")
        self.remove_files_button = QPushButton("Remove Selected")
        self.clear_files_button = QPushButton("Clear All")

        self.add_files_button.clicked.connect(self.choose_pdfs)
        self.remove_files_button.clicked.connect(self.remove_selected_pdfs)
        self.clear_files_button.clicked.connect(self.clear_pdfs)

        self.selected_pdf_label = QLabel("No PDFs selected")

        self.analytical_summarize_checkbox = QCheckBox("Analytical Summarizer")
        self.simple_summarize_checkbox = QCheckBox("Simple Narrative Summarizer")
        self.ner_checkbox = QCheckBox("Named Entity Recognition")
        self.ocr_checkbox = QCheckBox("OCR")
        self.translate_checkbox = QCheckBox("Translate")

        self.target_language_combo = QComboBox()
        for label, value in TRANSLATION_TARGET_LANGUAGES:
            self.target_language_combo.addItem(label, value)

        self.ocr_mode_combo = QComboBox()
        self.ocr_mode_combo.addItem("Extract pre-existing OCR text", "extract_text")
        self.ocr_mode_combo.addItem("Tesseract only", "tesseract")
        self.ocr_mode_combo.addItem("LLM Vision only", "vision_llm")
        self.ocr_mode_combo.addItem("Tesseract + LLM Vision", "tesseract_plus_vision")

        self.tesseract_language_combo = QComboBox()
        for code in get_installed_tesseract_languages():
            self.tesseract_language_combo.addItem(display_tesseract_language(code), code)

        default_language_index = self.tesseract_language_combo.findData("eng")
        if default_language_index >= 0:
            self.tesseract_language_combo.setCurrentIndex(default_language_index)

        self.preprocess_combo = QComboBox()
        self.preprocess_combo.addItem("None", "none")
        self.preprocess_combo.addItem("Basic - recommended", "basic")
        self.preprocess_combo.addItem("Archival - aggressive", "archival")
        self.preprocess_combo.setCurrentIndex(1)

        self.save_images_checkbox = QCheckBox("Save rendered page images")
        self.save_images_checkbox.setChecked(False)

        self.ocr_checkbox.toggled.connect(self.update_ocr_options_enabled)
        self.translate_checkbox.toggled.connect(self.update_ocr_options_enabled)
        self.ocr_mode_combo.currentIndexChanged.connect(self.update_ocr_options_enabled)

        self.process_button = QPushButton("Process Document(s)")
        self.settings_button = QPushButton("Settings")
        self.exit_button = QPushButton("Exit")

        self.process_button.clicked.connect(self.process_documents)
        self.settings_button.clicked.connect(self.open_settings)
        self.exit_button.clicked.connect(self.close)

        self.progress_output = QTextEdit()
        self.progress_output.setReadOnly(True)

        self.build_layout()
        self.update_ocr_options_enabled()

    def build_layout(self):
        main_layout = QVBoxLayout()

        files_group = QGroupBox("Documents")
        files_layout = QVBoxLayout()
        files_layout.addWidget(QLabel("Drag PDF files into the list below, or use Add Files."))
        files_layout.addWidget(self.pdf_list)

        file_button_layout = QHBoxLayout()
        file_button_layout.addWidget(self.add_files_button)
        file_button_layout.addWidget(self.remove_files_button)
        file_button_layout.addWidget(self.clear_files_button)
        files_layout.addLayout(file_button_layout)
        files_layout.addWidget(self.selected_pdf_label)

        files_group.setLayout(files_layout)
        main_layout.addWidget(files_group)

        tasks_group = QGroupBox("Processing Options")
        tasks_layout = QVBoxLayout()
        tasks_layout.addWidget(self.analytical_summarize_checkbox)
        tasks_layout.addWidget(self.simple_summarize_checkbox)
        tasks_layout.addWidget(self.ner_checkbox)
        tasks_layout.addWidget(self.ocr_checkbox)
        tasks_layout.addWidget(self.translate_checkbox)
        tasks_group.setLayout(tasks_layout)
        main_layout.addWidget(tasks_group)

        self.ocr_options_group = QGroupBox("OCR Options")
        ocr_options_layout = QFormLayout()
        ocr_options_layout.addRow("OCR method:", self.ocr_mode_combo)
        ocr_options_layout.addRow("Tesseract language:", self.tesseract_language_combo)
        ocr_options_layout.addRow("Image preprocessing:", self.preprocess_combo)
        ocr_options_layout.addRow("", self.save_images_checkbox)
        self.ocr_options_group.setLayout(ocr_options_layout)
        main_layout.addWidget(self.ocr_options_group)

        self.translation_options_group = QGroupBox("Translation Options")
        translation_options_layout = QFormLayout()
        translation_options_layout.addRow("Source language:", QLabel("Auto-detect"))
        translation_options_layout.addRow("Target language:", self.target_language_combo)
        self.translation_options_group.setLayout(translation_options_layout)
        main_layout.addWidget(self.translation_options_group)

        action_layout = QHBoxLayout()
        action_layout.addWidget(self.process_button)
        action_layout.addWidget(self.settings_button)
        action_layout.addWidget(self.exit_button)
        main_layout.addLayout(action_layout)

        progress_group = QGroupBox("Progress Output")
        progress_layout = QVBoxLayout()
        progress_layout.addWidget(self.progress_output)
        progress_group.setLayout(progress_layout)

        main_layout.addWidget(progress_group)

        self.setLayout(main_layout)

    def choose_pdfs(self):
        file_paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Choose PDF files",
            "",
            "PDF Files (*.pdf)",
        )
        if file_paths:
            self.add_pdfs([Path(file_path) for file_path in file_paths])

    def add_pdfs(self, paths: list[Path]):
        existing_paths = {path.resolve() for path in self.pdf_paths}
        added_paths: list[Path] = []

        for path in paths:
            path = Path(path)
            if path.suffix.lower() != ".pdf":
                continue

            resolved_path = path.resolve()
            if resolved_path in existing_paths:
                continue

            self.pdf_paths.append(path)
            existing_paths.add(resolved_path)
            added_paths.append(path)

            item = QListWidgetItem(path.name)
            item.setToolTip(str(path))
            item.setData(Qt.ItemDataRole.UserRole, path)
            self.pdf_list.addItem(item)

        self.update_selected_pdf_label()

        if added_paths:
            self.log(f"Added {len(added_paths)} PDF file(s).")

    def remove_selected_pdfs(self):
        selected_items = self.pdf_list.selectedItems()
        if not selected_items:
            return

        selected_paths = {item.data(Qt.ItemDataRole.UserRole).resolve() for item in selected_items}
        self.pdf_paths = [path for path in self.pdf_paths if path.resolve() not in selected_paths]

        for item in selected_items:
            row = self.pdf_list.row(item)
            self.pdf_list.takeItem(row)

        self.update_selected_pdf_label()
        self.log(f"Removed {len(selected_items)} PDF file(s).")

    def clear_pdfs(self):
        if not self.pdf_paths:
            return

        count = len(self.pdf_paths)
        self.pdf_paths.clear()
        self.pdf_list.clear()
        self.update_selected_pdf_label()
        self.log(f"Cleared {count} PDF file(s).")

    def update_selected_pdf_label(self):
        count = len(self.pdf_paths)

        if count == 0:
            label = "No PDFs selected"
        elif count == 1:
            label = f"Selected PDF: {self.pdf_paths[0]}"
        else:
            names = ", ".join(path.name for path in self.pdf_paths[:5])
            if count > 5:
                names += f", and {count - 5} more"
            label = f"Selected PDFs ({count}): {names}"

        self.selected_pdf_label.setText(label)

    def open_settings(self):
        dialog = SettingsDialog(self.settings, self)
        if dialog.exec():
            self.log("Settings saved.")

    def selected_tasks(self) -> list[str]:
        tasks: list[str] = []

        if self.analytical_summarize_checkbox.isChecked():
            tasks.append("analytical_summarize")
        if self.simple_summarize_checkbox.isChecked():
            tasks.append("simple_summarize")
        if self.ner_checkbox.isChecked():
            tasks.append("ner")
        if self.ocr_checkbox.isChecked():
            tasks.append("ocr")
        if self.translate_checkbox.isChecked():
            tasks.append("translate")

        return tasks

    def selected_ocr_mode(self) -> str:
        return self.ocr_mode_combo.currentData() or "extract_text"

    def selected_preprocess_mode(self) -> str:
        return self.preprocess_combo.currentData() or "basic"

    def selected_tesseract_language(self) -> str:
        return self.tesseract_language_combo.currentData() or "eng"

    def selected_target_language(self) -> str:
        return self.target_language_combo.currentData() or "English"

    def update_ocr_options_enabled(self):
        ocr_enabled = self.ocr_checkbox.isChecked()
        translate_enabled = self.translate_checkbox.isChecked()
        text_source_options_enabled = ocr_enabled or translate_enabled
        uses_tesseract = self.selected_ocr_mode() in {"tesseract", "tesseract_plus_vision"}

        # Translation also needs these settings because scanned PDFs may need OCR
        # before they can be sent to the LLM.
        self.ocr_options_group.setEnabled(text_source_options_enabled)
        self.ocr_mode_combo.setEnabled(text_source_options_enabled)
        self.preprocess_combo.setEnabled(text_source_options_enabled)
        self.save_images_checkbox.setEnabled(text_source_options_enabled)
        self.tesseract_language_combo.setEnabled(text_source_options_enabled and uses_tesseract)

        self.translation_options_group.setEnabled(translate_enabled)
        self.target_language_combo.setEnabled(translate_enabled)

    def process_documents(self):
        if not self.pdf_paths:
            QMessageBox.warning(
                self,
                "No PDFs Selected",
                "Please select one or more PDFs first.",
            )
            return

        tasks = self.selected_tasks()
        if not tasks:
            QMessageBox.warning(
                self,
                "No Processing Options Selected",
                "Please select at least one processing option.",
            )
            return

        if "translate" in tasks and translate_pdf is None:
            QMessageBox.warning(
                self,
                "Translation Not Available",
                "Translation is selected, but the translation backend is not currently available. "
                "Re-enable or implement src.translation.translation_core.translate_pdf first.",
            )
            return

        model_path = self.settings.value("model_path", "").strip()
        ocr_mode = self.selected_ocr_mode()

        tasks_requiring_model = {"analytical_summarize", "simple_summarize", "ner", "translate"}
        ocr_requires_model = "ocr" in tasks and ocr_mode in {"vision_llm", "tesseract_plus_vision"}

        if (tasks_requiring_model.intersection(tasks) or ocr_requires_model) and not model_path:
            QMessageBox.warning(
                self,
                "Missing Model Setting",
                "Please open Settings and enter a model path or LM Studio server URL.",
            )
            return

        self.set_controls_enabled(False)

        self.log("")
        self.log("Starting document processing.")
        self.log(f"Selected document(s): {len(self.pdf_paths)}")
        self.log("Selected task(s): " + ", ".join(TASK_LABELS[task] for task in tasks))

        if "ocr" in tasks or "translate" in tasks:
            self.log(f"Text extraction/OCR method: {ocr_mode}")
            self.log(f"Image preprocessing: {self.selected_preprocess_mode()}")
            if ocr_mode in {"tesseract", "tesseract_plus_vision"}:
                self.log(f"Tesseract language: {self.selected_tesseract_language()}")
            self.log(f"Save rendered page images: {self.save_images_checkbox.isChecked()}")

        if "translate" in tasks:
            self.log(f"Translation source language: Auto-detect")
            self.log(f"Translation target language: {self.selected_target_language()}")

        self.worker = Worker(
            tasks=tasks,
            pdf_paths=self.pdf_paths,
            model_path=model_path,
            ocr_mode=ocr_mode,
            preprocess_mode=self.selected_preprocess_mode(),
            save_page_images=self.save_images_checkbox.isChecked(),
            tesseract_language=self.selected_tesseract_language(),
            target_language=self.selected_target_language(),
        )

        self.worker.progress.connect(self.log)
        self.worker.finished.connect(self.task_finished)
        self.worker.failed.connect(self.task_failed)
        self.worker.start()

    def task_finished(self, message: str):
        self.log(message)
        self.log("Done.")
        self.set_controls_enabled(True)

    def task_failed(self, error_text: str):
        self.log("ERROR:")
        self.log(error_text)
        QMessageBox.critical(self, "Task Failed", error_text)
        self.set_controls_enabled(True)

    def set_controls_enabled(self, enabled: bool):
        self.pdf_list.setEnabled(enabled)
        self.add_files_button.setEnabled(enabled)
        self.remove_files_button.setEnabled(enabled)
        self.clear_files_button.setEnabled(enabled)
        self.analytical_summarize_checkbox.setEnabled(enabled)
        self.simple_summarize_checkbox.setEnabled(enabled)
        self.ner_checkbox.setEnabled(enabled)
        self.ocr_checkbox.setEnabled(enabled)
        self.translate_checkbox.setEnabled(enabled)
        self.process_button.setEnabled(enabled)
        self.settings_button.setEnabled(enabled)
        self.exit_button.setEnabled(enabled)

        if enabled:
            self.update_ocr_options_enabled()
        else:
            self.ocr_options_group.setEnabled(False)
            self.translation_options_group.setEnabled(False)

    def log(self, message: str):
        self.progress_output.append(message)
