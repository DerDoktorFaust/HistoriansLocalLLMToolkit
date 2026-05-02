def chunk_summary_prompt(chunk):
    return f"""
Summarize the following text from pages {chunk['start_page']}–{chunk['end_page']}.

Your task is to produce conservative historian-oriented notes for later synthesis.

STRICT REQUIREMENTS:
- Do NOT generalize beyond what is stated in the text.
- Do NOT infer the author's larger argument unless it is explicit in this chunk.
- Do NOT strengthen claims.
- Do NOT add background knowledge.
- Do NOT evaluate the author.
- Do NOT invent historiographical context.
- Every major claim must include page references.
- Use the author's own terms where possible.
- If something is unclear, write "unclear from this chunk."
- If something is only partly supported, write "partly supported."
- If a requested category is not present, write "Not stated in this chunk."

Output exactly the following sections:

## Thesis / Main Claim in This Chunk
Maximum 100 words.
State the main claim made in this chunk, if one is present.

## Argument Movement
Maximum 150 words.
Explain how the author develops the argument in this chunk. Focus on sequence: what claim follows what claim.

## Structure
Maximum 100 words.
Identify any clear section, chapter, or internal structure visible in this chunk.

## Historiographical References
List only explicit references to other historians, scholarly debates, schools, interpretations, or historiographical claims.
Do not infer historiography.
If none are present, write "Not stated in this chunk."

## Key Terms and Concepts
List important terms, concepts, categories, or phrases used by the author, with page references.

## Compressed Notes
Maximum 150 words.
Provide concise notes preserving the author's claims, sequence, and page references.

Text:
{chunk['text']}
"""


def batch_synthesis_prompt(combined):
    return f"""
The following are compressed notes from consecutive chunks of a book/article.

Produce a conservative intermediate synthesis for later final summarization.

STRICT REQUIREMENTS:
- Do NOT generalize beyond the notes.
- Do NOT make the argument cleaner or more linear than the notes support.
- Do NOT add outside knowledge.
- Do NOT infer historiography unless explicitly present in the notes.
- Preserve uncertainty, ambiguity, and gaps.
- Every major claim must include page references.
- If something is unclear, write "unclear from these notes."
- If a requested category is not present, write "Not stated in these notes."

Output exactly the following sections:

## Main Claim Across These Chunks
Maximum 150 words.
State the main claim supported by these notes.

## Argument Progression
Maximum 200 words.
Explain how the argument develops across these chunks. Focus on sequence and transitions.

## Structure
Maximum 150 words.
Identify chapter-level, section-level, or thematic structure only if clearly present.

## Historiographical References
List only explicit historiographical references, debates, historians, schools, or scholarly interventions mentioned in the notes.
Do not infer historiographical positioning.

## Key Terms and Concepts
List recurring or important terms and concepts, with page references.

## Pages to Revisit
List pages or page ranges that seem especially important, unclear, or central.

## Compressed Synthesis
Maximum 200 words.
Provide a concise synthesis preserving claims, sequence, uncertainty, and page references.

Compressed notes:
{combined}
"""


def final_summary_prompt(combined):
    return f"""
Based on the following intermediate summaries, produce a conservative analytical summary of the entire book.

This summary is for historian-oriented research notes and later use in another system. Accuracy matters more than elegance.

STRICT REQUIREMENTS:
- Do NOT add outside knowledge.
- Do NOT infer claims not supported by the summaries.
- Do NOT make the book sound more coherent, original, or important than the summaries support.
- Do NOT invent historiographical interventions.
- Historiography must be limited to explicit references in the summaries.
- Every major claim must include page references.
- Preserve uncertainty, ambiguity, contradiction, and gaps.
- If something is unclear, write "unclear from the summaries."
- If a requested category is not present, write "Not stated in the summaries."

Output exactly the following sections:

## Work Type
Book.

## Thesis
One sentence.
State the book's central thesis as conservatively as possible.

## Main Argument
Maximum 250 words.
Explain the main argument without exaggeration.

## Chapter-Level Structure
Reconstruct the book's chapter-level or major section-level structure.
Use page references.
If chapter divisions are unclear, reconstruct only the visible major parts and mark uncertainty.

## Argument Progression
Maximum 300 words.
Explain how the argument develops from beginning to end.

## Historiographical References
List only explicit historians, works, debates, schools, or historiographical claims mentioned in the summaries.
Do not infer the author's broader historiographical position.

## Key Terms and Concepts
List the author's major terms, concepts, categories, and analytical vocabulary, with page references.

## Relevance
Maximum 150 words.
State what the work is useful for, based only on the summaries.
Do not inflate importance.

## Limits, Qualifications, and Uncertainties
List important limits, qualifications, tensions, ambiguities, or uncertain points.

## Compact Research Note
Maximum 250 words.
Provide a concise historian-oriented note suitable for later retrieval.

Intermediate summaries:
{combined}
"""


def verification_prompt(final_summary, combined):
    return f"""
Evaluate the final book summary against the intermediate summaries.

Your task is NOT to rewrite the summary. Your task is to identify reliability problems.

STRICT REQUIREMENTS:
- Be conservative.
- Do NOT add outside knowledge.
- Do NOT suggest additions unless they are supported by the intermediate summaries.
- Focus especially on hallucination, overstatement, unsupported historiography, and missing page references.

Check for:
- Claims not supported by the intermediate summaries
- Overstated thesis
- Overstated originality or relevance
- Invented or inferred historiography
- Incorrect or too-neat chapter-level structure
- Missing major argument steps
- Missing page references
- Claims that need hedging
- Places where uncertainty should be preserved

Output exactly the following sections:

## Unsupported or Overstated Claims
For each issue:
- Problem:
- Why it is a problem:
- Suggested correction:

## Historiography Problems
For each issue:
- Problem:
- Why it is a problem:
- Suggested correction:

## Structure Problems
For each issue:
- Problem:
- Why it is a problem:
- Suggested correction:

## Missing Page References
List claims that need page references.

## Overall Reliability Assessment
Choose one: Reliable / Mostly reliable / Needs revision / Unreliable.
Briefly explain why.

Final summary:
{final_summary}

Intermediate summaries:
{combined}
"""


def article_final_summary_prompt(combined):
    return f"""
Based on the following chunk summaries, produce a conservative analytical summary of the article.

This summary is for historian-oriented research notes and later use in another system. Accuracy matters more than elegance.

STRICT REQUIREMENTS:
- Do NOT add outside knowledge.
- Do NOT infer claims not supported by the chunk summaries.
- Do NOT make the article sound broader, more original, or more definitive than the summaries support.
- Do NOT invent historiographical interventions.
- Historiography must be limited to explicit references in the summaries.
- Every major claim must include page references.
- Preserve uncertainty, ambiguity, contradiction, and gaps.
- If something is unclear, write "unclear from the summaries."
- If a requested category is not present, write "Not stated in the summaries."

Output exactly the following sections:

## Work Type
Article.

## Title and Author
Provide title and author only if available in the summaries.
If unavailable, write "Not stated in the summaries."

## Thesis
One sentence.
State the article's central thesis as conservatively as possible.

## Main Argument
Maximum 250 words.
Explain the main argument without exaggeration.

## Article Structure
Maximum 250 words.
Reconstruct the article's major sections or stages of argument.
Use page references.
If structure is unclear, mark uncertainty.

## Argument Progression
Maximum 250 words.
Explain how the article develops its argument from beginning to end.

## Historiographical References
List only explicit historians, works, debates, schools, or historiographical claims mentioned in the summaries.
Do not infer the author's broader historiographical position.

## Key Terms and Concepts
List the author's major terms, concepts, categories, and analytical vocabulary, with page references.

## Relevance
Maximum 150 words.
State what the article is useful for, based only on the summaries.
Do not inflate importance.

## Limits, Qualifications, and Uncertainties
List important limits, qualifications, tensions, ambiguities, or uncertain points.

## Compact Research Note
Maximum 200 words.
Provide a concise historian-oriented note suitable for later retrieval.

Chunk summaries:
{combined}
"""


def article_verification_prompt(final_summary, combined):
    return f"""
Evaluate the article summary against the chunk summaries.

Your task is NOT to rewrite the summary. Your task is to identify reliability problems.

STRICT REQUIREMENTS:
- Be conservative.
- Do NOT add outside knowledge.
- Do NOT suggest additions unless they are supported by the chunk summaries.
- Focus especially on hallucination, overstatement, unsupported historiography, and missing page references.

Check for:
- Claims not supported by the chunk summaries
- Overstated thesis
- Overstated originality or relevance
- Invented or inferred historiography
- Incorrect or too-neat article structure
- Missing major argument steps
- Missing page references
- Claims that need hedging
- Places where uncertainty should be preserved

Output exactly the following sections:

## Unsupported or Overstated Claims
For each issue:
- Problem:
- Why it is a problem:
- Suggested correction:

## Historiography Problems
For each issue:
- Problem:
- Why it is a problem:
- Suggested correction:

## Structure Problems
For each issue:
- Problem:
- Why it is a problem:
- Suggested correction:

## Missing Page References
List claims that need page references.

## Overall Reliability Assessment
Choose one: Reliable / Mostly reliable / Needs revision / Unreliable.
Briefly explain why.

Final article summary:
{final_summary}

Chunk summaries:
{combined}
"""