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