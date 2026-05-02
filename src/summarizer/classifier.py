ARTICLE_PAGE_THRESHOLD = 40


def classify_document(total_pages):
    if total_pages <= ARTICLE_PAGE_THRESHOLD:
        return "article"

    return "book"