# Historians Local LLM Toolkit

A local-first desktop application for historians, archivists, genealogists, and digital humanists who work with scanned documents, multilingual sources, and large collections of PDFs.

The Historians Local LLM Toolkit combines OCR, translation, and AI-assisted document analysis into a single workflow powered entirely by locally hosted models. No cloud APIs are required, allowing researchers to maintain full control over sensitive archival materials and research data.

**Version 1.0**

---

## Why This Project Exists

Historical research increasingly depends on large collections of digitized materials. Researchers often spend substantial time extracting text from scanned documents, translating foreign-language sources, organizing outputs, and preparing materials for analysis.

This toolkit was built to reduce that overhead.

Instead of relying on multiple disconnected tools and cloud services, the Historians Local LLM Toolkit provides a unified environment for:

- OCR of scanned documents
- Translation of historical texts
- AI-assisted analysis and summarization
- Batch processing of research collections

All processing occurs locally using models hosted through LM Studio (or another OpenAI compatible API).

---

## Key Features

### Desktop Application

- Drag-and-drop PDF loading
- Multi-document processing
- Batch workflows
- File management interface
- Processing queue
- One-click document processing
- Configurable settings panel

### Optical Character Recognition (OCR)

#### Tesseract OCR

- Fast local OCR engine
- Multi-language support
- User-selectable language packs
- Suitable for large collections

#### Vision-Language Model OCR

- Uses multimodal AI models
- Better performance on difficult scans
- Improved handling of historical documents
- Better interpretation of complex layouts

### Translation

- Automatic source-language detection
- User-selectable target language (approximately 30 languages)
- Batch translation of multiple PDFs
- Preservation of document structure
- Local processing
- Translation dependent upon LLM capabilities (i.e. languages less commonly trained for LLMs will produce poorer results)

### AI-Assisted Summarization

- Books
- Journal articles
- Archival documents
- Research reports
- Historical sources

Outputs are generated in Markdown format and integrate easily with Obsidian, DEVONthink, and Zotero workflows.

### Local LLM Integration

- No API costs
- Complete privacy
- Offline capability
- Full model control
- Support for archival and sensitive materials

Current support:

- LM Studio or any other OpenAI compatible API

---

## Research Workflow

1. Add one or more PDFs.
2. Select desired operations:
   - OCR
   - Translation
   - Summarization
3. Click **Process Document(s)**.
4. Output files are generated automatically.

The toolkit automatically performs prerequisite steps when required.

---

## File Management

- Drag-and-drop file loading
- Add files through a file browser
- Multi-file selection
- Remove selected files
- Clear all files from the queue

---

## Output Formats

### OCR Output

```text
document_ocr.txt
```

### Translation Output

```text
document_en.txt
document_fr.txt
document_de.txt
```

### Summary Output

```text
document_summary.md
```

---

## Installation

### Requirements

- Python 3.10+
- LM Studio or Ollama
- Local language model
- Local multimodal model (for Vision OCR)

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Launch Application

```bash
python3 -m src.main
```

---

## Intended Audience

- Historians
- Digital humanists
- Archivists
- Genealogists
- Graduate students
- Researchers working with scanned documents


---

## Philosophy

Historical research should not require surrendering source material to external services.

The Historians Local LLM Toolkit is built around a local-first philosophy that prioritizes privacy, transparency, reproducibility, and researcher control.

---

## License

MIT License

---

## Author

Christopher Goodwin  
Department of History  
University of Florida
