# Local LLM Pipeline for Book and Article Analysis

## Purpose

Summarizing long-form texts with large language models presents two core problems:

1. Context limitations – Even with large context windows, models struggle to maintain coherence across entire books.
2. Privacy and copyright concerns – Uploading full texts to external APIs is often undesirable or legally questionable.

This project solves both by running entirely locally and using a hierarchical summarization pipeline that processes documents in structured stages.

---

## Key Features

- Fully local pipeline (no external API calls required)
- Supports both books and articles
- Page-referenced outputs for traceability
- Hierarchical summarization for long texts
- Built-in verification pass to reduce hallucination and overstatement
- Structured Markdown output with YAML front matter for reuse in research workflows

---

## How It Works

### 1. Input

- OCR’d PDF (text must be extractable)
- Works best with clean, structured PDFs

---

### 2. Extraction

- Uses PyMuPDF to extract text page by page
- Preserves page boundaries for citation

---

### 3. Chunking

- Splits text into manageable chunks
- Each chunk includes:
  - start_page
  - end_page
  - embedded page markers (`[PAGE X] ... [/PAGE X]`)
- Ensures all summaries can be traced back to the original text

---

### 4. Chunk-Level Summarization

Each chunk is processed by a local LLM with strict constraints:

- Conservative, text-faithful summaries
- Explicit page references
- No overgeneralization or inflated claims

Each chunk produces:
- Structured analytical summary
- Compressed notes (used for synthesis)

---

### 5. Hierarchical Synthesis

#### Articles

Chunks → Final Article Summary → Verification

#### Books

Chunks → Batch Summaries → Final Book Summary → Verification

---

### 6. Verification Pass

A second LLM pass evaluates the final summary for:

- Overstatements
- Unsupported claims
- Missing structure
- Invented historiography

This produces a verification report, not a rewrite.

---

### 7. Output

Markdown file containing:

- YAML front matter (metadata-ready)
- Final structured summary
- Verification report
- Intermediate batch summaries (books)
- All chunk summaries with page ranges

Example output:

```
output/book_summary.md
output/article_summary.md
```

---

## Project Structure

```
book-summarizer/
├── main.py
├── llm.py
├── summarizer.py
├── prompts.py
├── writer.py
├── extractor.py
├── chunker.py
├── classifier.py
├── config.yaml
├── config_loader.py
├── input/
├── output/
├── logs/
└── requirements.txt
```

---

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/book-summarizer.git
cd book-summarizer
```

### 2. Create environment

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

---

## Configuration

Before running the pipeline, you must create and edit `config.yaml`.

### Example `config.yaml`

```yaml
model_path: /path/to/your/local/model
```

This must point to a valid MLX-compatible model on your system.

If this file is missing or incorrect, the pipeline will fail.

---

## Local LLM Requirement (MLX)

This project requires a locally running LLM compatible with Apple MLX.

The pipeline does NOT use external APIs.

### Requirements

- Apple Silicon Mac (M-series recommended)
- MLX-compatible model (e.g. Gemma, Qwen)
- Model stored locally on your machine

### Important

- The model is loaded directly in Python (no server required)
- The model must fit in your available RAM
- Performance and output quality depend heavily on the model

---

## Usage

### Run the pipeline

```bash
python main.py yourfile.pdf
```

---

## Output Format

Each `.md` file includes:

### YAML Front Matter

```yaml
title: null
author: null
publication_year: null
publisher_or_journal: null
work_type: null
source_file: yourfile.pdf
model: your_model_path
model_provider: null
generated_at: timestamp
pipeline_version: "0.1"
```

### Structured Sections

- Final Summary
- Verification Report
- Intermediate Summaries
- Chunk Summaries (with page ranges)

---

## Design Philosophy

- Precision over fluency
- Traceability through page references
- Modular components
- Local-first processing
- Structured output for research workflows

---

## Limitations

- Requires OCR’d PDFs (no image-only scans)
- Page-based chunking ignores deeper document structure
- Quality depends on the underlying local model
- Not a substitute for close reading

---

## Use Case

Designed for researchers who need:

- Rapid orientation in long texts
- Structured summaries of arguments
- Traceable claims tied to page ranges
- Local processing of PDFs

---

## License

MIT
