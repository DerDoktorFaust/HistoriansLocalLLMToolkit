def estimate_tokens(text):
    return int(len(text.split()) * 1.3)


def format_page_text(page):
    page_number = page["page_number"]
    text = page["text"].strip()

    return f"[PAGE {page_number}]\n{text}\n[/PAGE {page_number}]"


def chunk_pages(pages, max_tokens=2500):
    chunks = []
    current_text = []
    current_pages = []
    current_tokens = 0

    for page in pages:
        page_number = page["page_number"]
        page_text = format_page_text(page)
        tokens = estimate_tokens(page_text)

        if current_tokens + tokens > max_tokens and current_text:
            chunks.append({
                "text": "\n\n".join(current_text),
                "start_page": min(current_pages),
                "end_page": max(current_pages),
                "page_range": f"{min(current_pages)}-{max(current_pages)}",
                "pages": current_pages.copy()
            })

            current_text = []
            current_pages = []
            current_tokens = 0

        current_text.append(page_text)
        current_pages.append(page_number)
        current_tokens += tokens

    if current_text:
        chunks.append({
            "text": "\n\n".join(current_text),
            "start_page": min(current_pages),
            "end_page": max(current_pages),
            "page_range": f"{min(current_pages)}-{max(current_pages)}",
            "pages": current_pages.copy()
        })

    return chunks