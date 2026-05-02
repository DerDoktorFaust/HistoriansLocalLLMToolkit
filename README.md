# Local LLM Toolkit for Historical Text Analysis

## Overview
This project is a local large language model (LLM) toolkit designed for historians to process and analyze textual sources without reliance on external APIs. It provides an integrated workflow for summarizing books and articles, performing OCR on scanned PDFs, and translating historical texts, all within a local environment.

## Core Features
- **Summarization**  
  Automatically generates structured summaries of books and articles, preserving argumentation, key themes, and page-level references.

- **OCR (Optical Character Recognition)**  
  Extracts text from scanned or image-based PDFs using local vision-language models, with an emphasis on accurate transcription of historical documents.

- **Translation**  
  Translates texts (e.g., German to English) while maintaining historical terminology and structure.

## Technical Implementation
- Written in **Python**
- Uses **local LLMs** (via MLX or LM Studio)
- Modular architecture:
  - `main.py` – entry point
  - `extractor.py` – PDF handling
  - `chunker.py` – text segmentation
  - `llm.py` – model interaction
  - `summarizer.py` – prompt logic and summarization
  - `writer.py` – structured output generation
- Outputs results as structured **Markdown files**

## Usage
Run from the terminal:

```bash
python3 main.py path/to/document.pdf
```

The script will:

1. Determine document type (article or book)
2. Extract or OCR text as needed
3. Process the text with a local model
4. Output a structured Markdown summary

Requirements

* Python 3.10+
* Local LLM setup (MLX or LM Studio)
* Required Python packages (see requirements.txt)

Purpose

This toolkit is designed as a digital humanities tool for scholarly text analysis, enabling historians to efficiently process large corpora of primary and secondary sources while maintaining control over data and computational workflows.