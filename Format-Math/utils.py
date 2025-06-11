import os
import json
import glob

def read_data_files(data_dir):
    """Read all JSON files from the data directory"""
    data = []
    json_files = glob.glob(os.path.join(data_dir, "*.json"))
    
    for file_path in json_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                file_data = json.load(f)
                if isinstance(file_data, list):
                    data.extend(file_data)
                else:
                    data.append(file_data)
        except Exception as e:
            print(f"Error reading file {file_path}: {str(e)}")
    
    return data

def read_data_file(file_path):
    """Read a single JSON file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error reading file {file_path}: {str(e)}")
        return None

def format_prompt(question, explanation):
    """Format the prompt for the LLM"""
    prompt = f"""**Instructions:**
- Preserve the original reasoning structure in the formatted output without alteration.
- If the final answer is textual and not directly convertible to an extraction target, reformat it as a multiple-choice question.
- Remove conclusion phrases (e.g., "Kết luận," "Vì vậy," "Do đó," "Vậy") at the start of sentences or paragraphs; merge multiple nearby conclusion phrases into a single concise statement.
- Format the explanation's final answer within the `\\boxed{{...}}` environment using one of these structures:
  - "Đáp án cuối cùng là \\boxed{{...}}", "Đáp án đúng là \\boxed{{...}}", or "Đáp án là \\boxed{{...}}".
- Keep all math expressions and equations in LaTeX, preserving original format with explicit `\\\\` for line breaks.

**Key Guidelines:**
- Retain multiple-choice options (A, B, C, D) in the question.
- Prioritize LaTeX formatting for answers (e.g., lists, fractions like `\\frac{{a}}{{b}}`), with extracted answers in `$...$` or `$$...$$`, except for multiple-choice questions which use plain text.
- Make sure punctuation and line breaks are complete.

**Formatting Guidelines:**
- In Vietnamese **comma (,)** as the decimal separator (e.g., 3,14).
- In Vietnamese **period (.)** as the thousands separator (e.g., 1.234,56).
- Do not use period (.) or comma (,) as a thousands separator.

**Evaluation Library Guidelines:**
- **Extraction Targets:**
  - **LatexExtractionConfig**: For LaTeX expressions (e.g., `\\sqrt{{2}}`), must be in a LaTeX environment.
  - **ExprExtractionConfig**: For plain mathematical expressions (e.g., `1/2`, '133,3').
  - **MultiChoiceExtractionConfig**: For multiple-choice answers (e.g., `A`, `B`, `C`, `D`).

**Dataset Settings:**
- Determine the gold answer format:
  - Simple numbers: Use `ExprExtractionConfig`.
  - LaTeX expressions: Use `LatexExtractionConfig`.
  - Floats: Match the specified precision.
  - Multiple-choice options (A, B, C, D): Use `MultiChoiceExtractionConfig`.

**Output Format:**
Return the result as a JSON object:

```json
{{
  "Explanation": "<Unchanged chain-of-thought reasoning with final answer in \\boxed{{}}>",
  "Answer": "<Extracted final answer>",
  "Type": "<Extraction config: LatexExtractionConfig, ExprExtractionConfig, or MultiChoiceExtractionConfig>"
}}
```

**Example Input:**
Question: Tính môđun của số phức $z$ thỏa mãn phương trình $z(1 - i) + 2i = 1$.

Explanation: Ta có: $z(1 - i) + 2i = 1$ $z(1 - i) = 1 - 2i$ $z = \\frac{{1 - 2i}}{{1 - i}}$ Nhân cả tử và mẫu với số phức liên hợp của mẫu là $1 + i$: $z = \\frac{{(1 - 2i)(1 + i)}}{{(1 - i)(1 + i)}} = \\frac{{1 + i - 2i - 2i^2}}{{1 - i^2}} = \\frac{{1 - i + 2}}{{1 - (-1)}} = \\frac{{3 - i}}{{2}} = \\frac{{3}}{{2}} - \\frac{{1}}{{2}}i$ Môđun của số phức $z$ là: $|z| = \\sqrt{{\\left(\\frac{{3}}{{2}}\\right)^2 + \\left(-\\frac{{1}}{{2}}\\right)^2}} = \\sqrt{{\\frac{{9}}{{4}} + \\frac{{1}}{{4}}}} = \\sqrt{{\\frac{{10}}{{4}}}} = \\frac{{\\sqrt{{10}}}}{{2}}$ Vậy $|z| = \\frac{{\\sqrt{{10}}}}{{2}}$.

**Expected Output:**

```json
{{
  "Explanation": "Ta có: $z(1 - i) + 2i = 1$ $z(1 - i) = 1 - 2i$ $z = \\frac{{1 - 2i}}{{1 - i}}$ Nhân cả tử và mẫu với số phức liên hợp của mẫu là $1 + i$: $z = \\frac{{(1 - 2i)(1 + i)}}{{(1 - i)(1 + i)}} = \\frac{{1 + i - 2i - 2i^2}}{{1 - i^2}} = \\frac{{1 - i + 2}}{{1 - (-1)}} = \\frac{{3 - i}}{{2}} = \\frac{{3}}{{2}} - \\frac{{1}}{{2}}i$ Môđun của số phức $z$ là: $|z| = \\sqrt{{\\left(\\frac{{3}}{{2}}\\right)^2 + \\left(-\\frac{{1}}{{2}}\\right)^2}} = \\sqrt{{\\frac{{9}}{{4}} + \\frac{{1}}{{4}}}} = \\sqrt{{\\frac{{10}}{{4}}}} = \\frac{{\\sqrt{{10}}}}{{2}}$. Đáp án đúng là \\boxed{{\\frac{{\\sqrt{{10}}}}{{2}}}}.",
  "Answer": "$\\frac{{\\sqrt{{10}}}}{{2}}$",
  "Type": "LatexExtractionConfig"
}}
```

**Input**

Question: {question}

Explanation: {explanation}
"""
    return prompt

def ensure_math_delimiters(answer):
    """Ensure the answer is surrounded by appropriate math delimiters"""
    if not answer:
        return answer

    # Return if already surrounded by math delimiters
    if answer.startswith(('$$', '$')) and answer.endswith(('$$', '$')):
        return answer

    # Indicators for LaTeX or units requiring math delimiters
    latex_indicators = ['\\', '\\frac', '\\sqrt', '\\sum', '\\int', '\\pi', '\\alpha', '\\beta']
    unit_indicators = ['m^3', 'm^2', 'm', 'km/h', 'km', 'h', 'kg', 'g', 't', 'm/s', 's', '%', 'đ']
    math_symbols = ['=', '>', '<']

    # Add $$ delimiters for LaTeX content
    if any(indicator in answer for indicator in latex_indicators):
        return f"$${answer}$$"

    # Add $ delimiters for units or math symbols
    if any(indicator in answer for indicator in unit_indicators + math_symbols):
        return f"${answer}$"

    return answer