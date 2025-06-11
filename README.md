# ViMATH-VERIFY

## Installation Instructions

**ViMATH-VERIFY** is a customized extension of [Math-Verify](https://github.com/huggingface/Math-Verify), tailored specifically for evaluating Vietnamese mathematical reasoning benchmarks.

*Recommendation: Use Linux to run Math-Verify*

### Step 1: Clone the Repository

```bash
git clone https://github.com/QuangDiy/ViMATH-Verify
cd ViMATH-Verify
```

### Step 2: Create Virtual Environment

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Step 3: Navigate to Math-Verify Directory and Install as Editable Package

You must change directory to Math-Verify first to install the package:

```bash
cd Math-Verify
pip install -e .
cd .. 
```

---

## Usage

### Formatting Math Data

You can format data using the Format-Math tool:

```bash
python Format-Math/main.py
```

**Requirements:** 
- Place your input data in `Format-Math/data/`
- Output will be saved to `Format-Math/output/`

**TO DO**
{
"Explanation": "ĐK: x ≠ -1, x ≠ 2. Ta có: $\\frac{1}{x+1} - \\frac{5}{x-2} = \\frac{15}{(x+1)(2-x)}$ $\\Leftrightarrow 2 - x + 5(x + 1) = 15$ $\\Leftrightarrow 4x = 8$ $\\Leftrightarrow x = 2$ (loại do vi phạm điều kiện). Đáp án cuối cùng là \boxed{\\text{Phương trình vô nghiệm}}.",
"Answer": "Phương trình vô nghiệm",
"Type": "MultiChoiceExtractionConfig",
"Question": "Giải phương trình:\n$\\frac{1}{x+1} - \\frac{5}{x-2} = \\frac{15}{(x+1)(2-x)}$",
"Original_Explanation": "$\\frac{1}{x+1} - \\frac{5}{x-2} = \\frac{15}{(x+1)(2-x)}, ĐK: x \\neq -1, x \\neq 2$\n$\\Leftrightarrow 2 - x + 5(x + 1) = 15$\n$\\Leftarrow 4x = 8$\n$\\Leftarrow x = 2 (loại)$\nVậy phương trình vô nghiệm",
"Grade": 8.0,
"Source": "8.2_math_data-gk2_8.2_8.2",
"Difficulty Level": "L3",
"Response Type": "Other",
"Math Type": "Algebra",
"Answer Type": "Text",
"Categories": "1.B - Equations and systems of equations"
},

Chuẩn hóa dữ liệu các trường hợp latex \frac thành \\frac (\boxed) etc. 