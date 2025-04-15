# Format-Math

This project processes math problems and their explanations by sending them to the Together AI API, 
verifying the answers using the math_verify library, and saving valid answers to a JSON file.

## Setup

1. Clone the repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Copy `.env` to `.env` and add your Together AI API key:
   ```
   TOGETHER_API_KEY=your_api_key_here
   ```
4. Create a `data` directory and add your JSON files with math problems
5. Create an `output` directory for the results

## Data Format

Input JSON files in the `data` directory should contain objects with:
- `question`: The math problem text
- `explanation`: The solution explanation

## Usage

Run the main script:

```
python main.py
```

The script will:
1. Read all JSON files from the `data` directory
2. Send each question and explanation to the Together AI API
3. Parse the response and verify the answer using math_verify
4. Save verified answers to `output/verified_answers.json`

## Output

The output file contains a list of verified answers, each with:
- Question: The original question
- Explanation: Chain-of-thought reasoning with boxed answer
- Answer: The extracted final answer
- Type: The extraction configuration used
- OriginalQuestion: The input question
- OriginalExplanation: The input explanation
