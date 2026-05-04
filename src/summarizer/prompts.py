def chunk_summary_prompt(chunk):
    return f"""
You are creating historian-oriented research notes from pages {chunk['start_page']}–{chunk['end_page']}.

Your task is not to produce a generic summary. Your task is to identify the author's claims, evidence, conceptual moves, tensions, and historiographical positioning as they appear in this chunk.

STRICT REQUIREMENTS:
- Do NOT add outside knowledge.
- Do NOT generalize beyond this chunk.
- Do NOT make the argument cleaner, broader, or more coherent than the text supports.
- Do NOT invent historiographical context.
- Do NOT evaluate whether the author is right.
- Every major claim must include page references.
- Use the author's own terms where possible.
- Avoid generic phrases such as "the text discusses" or "the article examines."
- Avoid vague phrases such as "complex interplay," "practical needs," "bureaucratic constraints," or "ideological tensions" unless you immediately specify the concrete process, actor, institution, document, or decision involved.
- If something is unclear, write "unclear from this chunk."
- If something is only partly supported, write "partly supported."
- If a requested category is not present, write "Not stated in this chunk."

Output exactly the following sections:

## Main Claim in This Chunk
Maximum 100 words.
State the strongest claim made in this chunk. Phrase it as an arguable historical claim, not as a topic.

## Evidence and Examples
List the most important evidence, examples, cases, documents, people, institutions, or statistics used in this chunk.
Include page references.

## Argument Movement
Maximum 150 words.
Explain how the author moves from one claim to the next. Preserve sequence and causality.

## Core Mechanism
Maximum 100 words.
Identify the process that explains how the argument works in this chunk.
Name the actors, institutions, rules, documents, or decisions involved when possible.
Examples: SS racial certification, Ansiedlungsschein screening, propaganda recruitment, settlement-office exceptions, wartime manpower reassignment, racial classification, gendered family labor.
If no mechanism is visible, write "Not stated in this chunk."

## Central Tensions
List 2–4 contradictions, frictions, or unstable categories visible in this chunk.
Write each as a tension between two specific forces, categories, expectations, or practices.
If none are visible, write "Not stated in this chunk."

## Historiographical References
List only explicit references to other historians, scholarly debates, schools, interpretations, or historiographical claims.
Do not infer historiography.
If none are present, write "Not stated in this chunk."

## Key Terms and Concepts
List important terms, concepts, categories, or phrases used by the author, with page references.

## Compressed Notes
Maximum 175 words.
Provide concise historian-oriented notes preserving claims, evidence, mechanism, tensions, and page references.

Text:
{chunk['text']}
"""


def batch_synthesis_prompt(combined):
    return f"""
The following are compressed notes from consecutive chunks of a book or article.

Produce an intermediate historian-oriented synthesis for later final summarization.

STRICT REQUIREMENTS:
- Do NOT add outside knowledge.
- Do NOT generalize beyond the notes.
- Do NOT make the argument cleaner or more linear than the notes support.
- Do NOT invent historiographical positioning.
- Preserve uncertainty, ambiguity, contradiction, and gaps.
- Every major claim must include page references.
- Avoid generic phrases such as "the author discusses" or "the text examines."
- Avoid vague phrases such as "complex interplay," "practical needs," "bureaucratic constraints," or "ideological tensions" unless you immediately specify the concrete process, actor, institution, document, or decision involved.
- Build the synthesis from the Core Mechanism and Central Tensions sections in the notes, not only from the Compressed Notes.
- If something is unclear, write "unclear from these notes."
- If a requested category is not present, write "Not stated in these notes."

Output exactly the following sections:

## Main Claim Across These Chunks
Maximum 150 words.
State the strongest claim supported by these notes as an arguable historical claim.

## Evidence Base
List the most important evidence, examples, cases, documents, people, institutions, or statistics across these chunks.
Include page references.

## Argument Progression
Maximum 200 words.
Explain how the argument develops across these chunks. Focus on sequence, causality, and transitions.

## Core Mechanism
Maximum 150 words.
Identify the main process or mechanism driving the argument across these chunks.
Name the actors, institutions, rules, documents, or decisions involved.

## Central Tensions
List 2–5 contradictions, frictions, unstable categories, or unresolved problems visible across these chunks.
Write each as a specific tension, not a vague theme.

## Historiographical References
List only explicit historiographical references, debates, historians, schools, or scholarly interventions mentioned in the notes.
Do not infer historiographical positioning.

## Key Terms and Concepts
List recurring or important terms and concepts, with page references.

## Pages to Revisit
List pages or page ranges that seem especially important, unclear, evidentiary, or conceptually central.

## Compressed Synthesis
Maximum 225 words.
Provide a concise synthesis preserving claims, evidence, mechanism, tensions, uncertainty, and page references.

Compressed notes:
{combined}
"""


def final_summary_prompt(combined):
    return f"""
Based on the following intermediate summaries, produce a historian-oriented analytical summary of the entire book.

This is not a generic summary. It should function as a research note that helps a historian understand the book's argument, evidence, mechanism, historiographical intervention, tensions, and limits.

STRICT REQUIREMENTS:
- Do NOT add outside knowledge.
- Do NOT infer claims not supported by the summaries.
- Do NOT make the book sound more coherent, original, or important than the summaries support.
- Do NOT invent historiographical interventions.
- Historiography must be limited to explicit references in the summaries.
- Every major claim must include page references.
- Preserve uncertainty, ambiguity, contradiction, and gaps.
- Avoid generic phrases such as "the book discusses" or "the author examines."
- Avoid vague phrases such as "complex interplay," "practical needs," "bureaucratic constraints," or "ideological tensions" unless you immediately specify the concrete process, actor, institution, document, or decision involved.
- Build the Main Argument from the Core Mechanism and Central Tensions sections in the summaries, not only from the Compressed Synthesis.
- Prefer concrete claims over abstract summary language.
- If something is unclear, write "unclear from the summaries."
- If a requested category is not present, write "Not stated in the summaries."

Output exactly the following sections:

## Work Type
Book.

## Thesis
One sentence.
State the book's central thesis as an arguable claim. Do not state merely the topic.

## Main Argument
Maximum 250 words.
Explain the main argument by showing how the mechanism produces the central tensions or outcomes.
Name the main actors, institutions, rules, documents, or decisions.
Avoid vague summary language.

## Historiographical Intervention
Maximum 200 words.
State what the book changes, revises, challenges, or adds to existing scholarship.
Use only explicit historiographical material from the summaries.
If the intervention is unclear, write "unclear from the summaries."

## Core Mechanism
Maximum 175 words.
Identify the main process by which the argument works.
Name concrete institutions, rules, documents, actors, procedures, or practices.

## Evidence Base
List the major types of evidence, cases, archives, documents, people, institutions, events, or examples used in the book.
Include page references.

## Structure of the Work
Reconstruct the book's chapter-level or major section-level structure.
Use page references.
If chapter divisions are unclear, reconstruct only the visible major parts and mark uncertainty.

## Argument Progression
Maximum 300 words.
Explain how the argument develops from beginning to end.
Emphasize turning points, contradictions, and changes over time.

## Central Tensions
List the major contradictions, frictions, unstable categories, or unresolved problems that drive the book.
Each bullet must name the two sides of the tension.

## Key Terms and Concepts
List the author's major terms, concepts, categories, and analytical vocabulary, with page references.

## Relevance
Maximum 150 words.
State what the work is useful for, based only on the summaries.
Do not inflate importance.

## Limits, Qualifications, and Uncertainties
List important limits, qualifications, ambiguities, unclear points, or places where the summaries do not provide enough support.

## Compact Research Note
Maximum 250 words.
Provide a concise historian-oriented note suitable for later retrieval.
It must include: thesis, mechanism, evidence base, central tension, and relevance.

Intermediate summaries:
{combined}
"""


def verification_prompt(final_summary, combined):
    return f"""
Evaluate the final book summary against the intermediate summaries.

Your task is not to rewrite the summary. Your task is to identify reliability problems and analytical weaknesses.

STRICT REQUIREMENTS:
- Be conservative.
- Do NOT add outside knowledge.
- Do NOT suggest additions unless they are supported by the intermediate summaries.
- Focus especially on hallucination, overstatement, unsupported historiography, weak mechanism, missing tensions, missing page references, and vague prose.
- Flag vague phrases such as "complex interplay," "practical needs," "bureaucratic constraints," or "ideological tensions" if they are not immediately made concrete.

Check for:
- Claims not supported by the intermediate summaries
- Overstated thesis
- Overstated originality or relevance
- Invented or inferred historiography
- Incorrect or too-neat structure
- Missing major argument steps
- Missing evidence
- Missing mechanism
- Missing central tensions
- Missing page references
- Claims that need hedging
- Places where uncertainty should be preserved
- Generic prose that weakens the analytical usefulness of the summary

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

## Analytical Weaknesses
For each issue:
- Problem:
- Why it weakens the summary:
- Suggested correction:

## Vague or Generic Language
List phrases that should be replaced with more concrete analytical language.

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
Based on the following chunk summaries, produce a historian-oriented analytical summary of the article.

This is not a generic summary. It should function as a research note that helps a historian understand the article's argument, evidence, mechanism, historiographical intervention, tensions, and limits.

STRICT REQUIREMENTS:
- Do NOT add outside knowledge.
- Do NOT infer claims not supported by the chunk summaries.
- Do NOT make the article sound broader, more original, or more definitive than the summaries support.
- Do NOT invent historiographical interventions.
- Historiography must be limited to explicit references in the summaries.
- Every major claim must include page references.
- Preserve uncertainty, ambiguity, contradiction, and gaps.
- Avoid generic phrases such as "the article discusses" or "the author examines."
- Avoid vague phrases such as "complex interplay," "practical needs," "bureaucratic constraints," or "ideological tensions" unless you immediately specify the concrete process, actor, institution, document, or decision involved.
- Build the Main Argument from the Core Mechanism and Central Tensions sections in the chunk summaries, not only from the Compressed Notes.
- Prefer concrete claims over abstract summary language.
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
State the article's central thesis as an arguable claim. Do not state merely the topic.

## Main Argument
Maximum 250 words.
Explain the main argument by showing how the mechanism produces the central tensions or outcomes.
Name the main actors, institutions, rules, documents, or decisions.
Avoid vague summary language.

## Historiographical Intervention
Maximum 200 words.
State what the article changes, revises, challenges, or adds to existing scholarship.
Use only explicit historiographical material from the summaries.
If the intervention is unclear, write "unclear from the summaries."

## Core Mechanism
Maximum 175 words.
Identify the main process by which the argument works.
Name concrete institutions, rules, documents, actors, procedures, or practices.

## Evidence Base
List the major types of evidence, cases, archives, documents, people, institutions, events, or examples used in the article.
Include page references.

## Article Structure
Maximum 250 words.
Reconstruct the article's major sections or stages of argument.
Use page references.
If structure is unclear, mark uncertainty.

## Argument Progression
Maximum 250 words.
Explain how the article develops its argument from beginning to end.
Emphasize turning points, contradictions, and changes over time.

## Central Tensions
List the major contradictions, frictions, unstable categories, or unresolved problems that drive the article.
Each bullet must name the two sides of the tension.

## Key Terms and Concepts
List the author's major terms, concepts, categories, and analytical vocabulary, with page references.

## Relevance
Maximum 150 words.
State what the article is useful for, based only on the summaries.
Do not inflate importance.

## Limits, Qualifications, and Uncertainties
List important limits, qualifications, ambiguities, unclear points, or places where the summaries do not provide enough support.

## Compact Research Note
Maximum 225 words.
Provide a concise historian-oriented note suitable for later retrieval.
It must include: thesis, mechanism, evidence base, central tension, and relevance.

Chunk summaries:
{combined}
"""


def article_verification_prompt(final_summary, combined):
    return f"""
Evaluate the article summary against the chunk summaries.

Your task is not to rewrite the summary. Your task is to identify reliability problems and analytical weaknesses.

STRICT REQUIREMENTS:
- Be conservative.
- Do NOT add outside knowledge.
- Do NOT suggest additions unless they are supported by the chunk summaries.
- Focus especially on hallucination, overstatement, unsupported historiography, weak mechanism, missing tensions, missing page references, and vague prose.
- Flag vague phrases such as "complex interplay," "practical needs," "bureaucratic constraints," or "ideological tensions" if they are not immediately made concrete.

Check for:
- Claims not supported by the chunk summaries
- Overstated thesis
- Overstated originality or relevance
- Invented or inferred historiography
- Incorrect or too-neat article structure
- Missing major argument steps
- Missing evidence
- Missing mechanism
- Missing central tensions
- Missing page references
- Claims that need hedging
- Places where uncertainty should be preserved
- Generic prose that weakens the analytical usefulness of the summary

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

## Analytical Weaknesses
For each issue:
- Problem:
- Why it weakens the summary:
- Suggested correction:

## Vague or Generic Language
List phrases that should be replaced with more concrete analytical language.

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


def simple_chunk_summary_prompt(chunk):
    return f"""
You are creating a simple narrative history summary from pages {chunk['start_page']}–{chunk['end_page']}.

Your task is to summarize what happens in this chunk: events, people, institutions, decisions, causes, consequences, chronology, and changes over time.

This is NOT an analytical research-note mode. Do not focus on historiography, scholarly intervention, argument mechanics, or methodological critique unless the text itself makes them necessary for understanding the narrative.

STRICT REQUIREMENTS:
- Do NOT add outside knowledge.
- Do NOT infer events or causes not supported by this chunk.
- Preserve chronology when possible.
- Include page references for major events, people, institutions, claims, and turning points.
- Use plain, direct language.
- If the chunk is mostly conceptual rather than narrative, summarize the concepts only as much as needed to understand the historical story being told.
- If something is unclear, write "unclear from this chunk."
- If a requested category is not present, write "Not stated in this chunk."

Output exactly the following sections:

## What Happens in This Chunk
Maximum 200 words.
Summarize the historical narrative in this chunk in chronological order where possible.

## Main People, Groups, and Institutions
List the important people, groups, states, agencies, organizations, or institutions in this chunk.
For each one, state what they do or why they matter. Include page references.

## Key Events and Developments
List the major events, decisions, policies, conflicts, changes, or turning points. Include page references.

## Causes and Consequences
List clear cause-and-effect relationships stated or strongly supported by the chunk. Include page references.

## Important Terms
List important terms, categories, places, laws, policies, or concepts needed to follow the narrative. Include brief definitions and page references.

## Narrative Notes
Maximum 200 words.
Provide compact notes preserving the sequence of events, main actors, causes, consequences, and page references.

Text:
{chunk['text']}
"""


def simple_final_summary_prompt(combined):
    return f"""
Based on the following chunk narrative notes, produce a simple narrative summary of the text.

This summary is meant to help a reader understand the history being told: what happened, who mattered, how events unfolded, what changed, and why it mattered within the text.

This is NOT a historian-oriented analytical summary. Do not foreground historiography, scholarly intervention, theoretical framing, or critique unless they are necessary to understand the narrative.

STRICT REQUIREMENTS:
- Do NOT add outside knowledge.
- Do NOT infer events, causes, or consequences not supported by the notes.
- Preserve chronology wherever possible.
- Include page references for major events, people, institutions, developments, and turning points.
- Do not make the narrative cleaner or more complete than the notes support.
- Use plain, direct language.
- If something is unclear, write "unclear from the notes."
- If a requested category is not present, write "Not stated in the notes."

Output exactly the following sections:

## Overview
Maximum 250 words.
Give a clear overview of the history narrated in the text.

## Chronological Narrative
Provide a fuller summary of the events, developments, and changes described, in the order they unfold.
Use page references throughout.

## Main People, Groups, and Institutions
List the important actors in the text.
For each one, explain what they do in the narrative and why they matter. Include page references.

## Key Events and Developments
List the most important events, decisions, policies, conflicts, changes, and turning points. Include page references.

## Causes and Consequences
List the major cause-and-effect relationships in the text. Include page references.

## Important Terms and Places
List important terms, categories, laws, policies, places, or concepts needed to understand the narrative. Include brief explanations and page references.

## What to Remember
Maximum 150 words.
State the most important takeaway from the historical narrative.

Chunk narrative notes:
{combined}
"""


def simple_verification_prompt(final_summary, combined):
    return f"""
Evaluate the simple narrative summary against the chunk narrative notes.

Your task is not to rewrite the summary. Your task is to identify reliability problems.

STRICT REQUIREMENTS:
- Be conservative.
- Do NOT add outside knowledge.
- Do NOT suggest additions unless they are supported by the notes.
- Focus on hallucinated events, unsupported causality, wrong chronology, missing major actors, missing major events, missing page references, and vague summary language.

Check for:
- Events not supported by the notes
- People, groups, or institutions not supported by the notes
- Causes or consequences not supported by the notes
- Chronology that is wrong or too neat
- Missing major events or turning points
- Missing page references
- Claims that need hedging
- Places where uncertainty should be preserved

Output exactly the following sections:

## Unsupported or Overstated Narrative Claims
For each issue:
- Problem:
- Why it is a problem:
- Suggested correction:

## Chronology Problems
For each issue:
- Problem:
- Why it is a problem:
- Suggested correction:

## Missing Major Actors or Events
For each issue:
- Problem:
- Why it matters:
- Suggested correction:

## Unsupported Causality
For each issue:
- Problem:
- Why it is a problem:
- Suggested correction:

## Missing Page References
List claims that need page references.

## Overall Reliability Assessment
Choose one: Reliable / Mostly reliable / Needs revision / Unreliable.
Briefly explain why.

Simple narrative summary:
{final_summary}

Chunk narrative notes:
{combined}
"""

