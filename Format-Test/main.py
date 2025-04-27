import os
import json
import asyncio
import aiohttp
from typing import Union, List, Dict, Any
from copy import deepcopy
from dataclasses import dataclass
import re
from dotenv import load_dotenv
from math_verify import parse, verify
from math_verify.parser import LatexExtractionConfig, StringExtractionConfig, ExprExtractionConfig, MultiChoiceExtractionConfig
from tqdm import tqdm
from utils import read_data_file, format_prompt, ensure_math_delimiters

load_dotenv()

API_URL = os.getenv("API_URL")
API_KEY = os.getenv("API_KEY")
MODEL = os.getenv("MODEL_NAME")
DATA_FILE_PATH = "./data/THCS.json"
OUTPUT_FILE = "./output/THCS.json"
OUTPUT_FILE_UN = "./output/unverified_THCS.json"
BATCH_SIZE = 16
SAVE_EVERY_N_BATCHES = 64

cookies = json.loads(os.getenv("COOKIES"))

@dataclass
class LLMSamplingSettings:
    def __init__(self):
        self.temperature: float = 0.5
        self.top_k: int = None
        self.top_p: float = 0.95
        self.min_p: float = None
        self.n_predict: int = -1
        self.n_keep: int = 0
        self.stream: bool = False
        self.additional_stop_sequences: List[str] = None
        self.tfs_z: float = 1.0
        self.typical_p: float = 1.0
        self.repeat_penalty: float = None
        self.repeat_last_n: int = -1
        self.penalize_nl: bool = False
        self.presence_penalty: float = 0.0
        self.frequency_penalty: float = 0.0
        self.penalty_prompt: Union[None, str, List[int]] = None
        self.mirostat_mode: int = 0
        self.mirostat_tau: float = 5.0
        self.mirostat_eta: float = 0.1
        self.cache_prompt: bool = True
        self.seed: int = -1
        self.ignore_eos: bool = False
        self.samplers: List[str] = None

    def get_additional_stop_sequences(self) -> List[str]:
        if self.additional_stop_sequences is None:
            self.additional_stop_sequences = []
        return self.additional_stop_sequences

    def add_additional_stop_sequences(self, sequences: List[str]):
        if self.additional_stop_sequences is None:
            self.additional_stop_sequences = []
        self.additional_stop_sequences.extend(sequences)

    def is_streaming(self):
        return self.stream

    def as_dict(self) -> dict:
        """
        Convert the settings to a dictionary.

        Returns:
            dict: The dictionary representation of the settings.
        """
        return self.__dict__

class LLMServerProvider:
    def __init__(self, server_address: str):
        if not server_address:
            raise ValueError("Server address cannot be empty.")

        self.server_address = server_address
        self.server_chat_completion_endpoint = (
            self.server_address + "/v1/chat/completions"
        )

    def get_provider_default_settings(self) -> LLMSamplingSettings:
        return LLMSamplingSettings()

    async def create_chat_completion(
        self,
        session: aiohttp.ClientSession,
        messages: List[Dict[str, str]],
        settings: Dict[Any, Any],
        cookies: Dict[str, str] = None,
        API_KEY: str = None,
        MODEL: str = "gpt-3.5-turbo" ,
    ):
        headers = {"Content-Type": "application/json"}
        if API_KEY:
            headers["Authorization"] = f"Bearer {API_KEY}"

        data = deepcopy(settings)

        data["model"] = MODEL
            
        data["messages"] = messages

        data = self.prepare_generation_settings(data)
        response = await session.request(
            "POST", url=self.server_chat_completion_endpoint, headers=headers, json=data, cookies = cookies
        )
        return_data = await response.json()
        return return_data["choices"][0]["message"]["content"]

    def prepare_generation_settings(self, settings_dictionary: dict) -> dict:
        settings_dictionary["mirostat"] = settings_dictionary.pop("mirostat_mode", 0)
        if "additional_stop_sequences" in settings_dictionary:
            settings_dictionary["stop"] = settings_dictionary.pop("additional_stop_sequences")
        if "samplers" in settings_dictionary:
            del settings_dictionary["samplers"]
        return settings_dictionary

def parse_llm_response(response_text):
    """Extract JSON from the LLM response handling complex nested structures and LaTeX"""
    try:
        # First attempt: Clean up backslashes in LaTeX expressions
        if '```json' in response_text:
            # Extract content between ```json and ``` markers
            match = re.search(r'```json\s*([\s\S]*?)\s*```', response_text)
            if match:
                json_content = match.group(1)
                
                # IMPROVED APPROACH FOR HANDLING LATEX ESCAPES
                # Instead of trying to fix escapes, use a more direct method
                try:
                    # Try direct parsing first
                    result = json.loads(json_content)
                    print(f"Successfully parsed JSON directly from code block")
                    return result
                except json.JSONDecodeError:
                    # If that fails, try to parse using a lenient approach
                    try:
                        # Use a more robust approach - recreate the JSON
                        # Extract the key parts using regex
                        explanation_pattern = r'"Explanation"\s*:\s*"((?:[^"\\]|\\.)*)"'
                        answer_pattern = r'"Answer"\s*:\s*"((?:[^"\\]|\\.)*)"'
                        type_pattern = r'"Type"\s*:\s*"((?:[^"\\]|\\.)*)"'
                        
                        explanation_match = re.search(explanation_pattern, json_content)
                        answer_match = re.search(answer_pattern, json_content)
                        type_match = re.search(type_pattern, json_content)
                        
                        if explanation_match and answer_match and type_match:
                            # Create a new clean JSON object
                            cleaned_json = {
                                "Explanation": explanation_match.group(1),
                                "Answer": answer_match.group(1),
                                "Type": type_match.group(1)
                            }
                            print(f"Successfully parsed JSON using regex extraction from code block")
                            return cleaned_json
                    except Exception as e:
                        print(f"Regex extraction failed: {e}")
        
        # Second attempt: Try to extract JSON object using more robust pattern matching
        json_pattern = re.compile(r'\{\s*"Explanation"\s*:\s*"((?:[^"\\]|\\.)*)"\s*,\s*"Answer"\s*:\s*"((?:[^"\\]|\\.)*)"\s*,\s*"Type"\s*:\s*"((?:[^"\\]|\\.)*)"')
        match = json_pattern.search(response_text)
        if match:
            cleaned_json = {
                "Explanation": match.group(1),
                "Answer": match.group(2),
                "Type": match.group(3)
            }
            print(f"Successfully parsed JSON using comprehensive regex")
            return cleaned_json
            
        # Third attempt: Try to manually reconstruct the JSON from the markdown
        explanation_start = response_text.find('"Explanation"')
        answer_start = response_text.find('"Answer"')
        type_start = response_text.find('"Type"')
        
        if explanation_start >= 0 and answer_start >= 0 and type_start >= 0:
            # Extract content after "Explanation":
            exp_content_start = response_text.find(':', explanation_start) + 1
            exp_content_end = answer_start - 1 if answer_start < type_start else type_start - 1
            
            # Extract content after "Answer":
            ans_content_start = response_text.find(':', answer_start) + 1
            ans_content_end = type_start - 1 if type_start > answer_start else explanation_start - 1
            
            # Extract content after "Type":
            type_content_start = response_text.find(':', type_start) + 1
            type_content_end = explanation_start - 1 if explanation_start > type_start else answer_start - 1
            
            if exp_content_start >= 0 and ans_content_start >= 0 and type_content_start >= 0:
                # Clean the extracted content
                explanation = response_text[exp_content_start:exp_content_end].strip()
                if explanation.startswith('"') and explanation.endswith('"'):
                    explanation = explanation[1:-1]
                elif explanation.startswith('"') and explanation.endswith('",'):
                    explanation = explanation[1:-2]
                
                answer = response_text[ans_content_start:ans_content_end].strip()
                if answer.startswith('"') and answer.endswith('"'):
                    answer = answer[1:-1]
                elif answer.startswith('"') and answer.endswith('",'):
                    answer = answer[1:-2]
                
                type_val = response_text[type_content_start:type_content_end].strip()
                if type_val.startswith('"') and type_val.endswith('"'):
                    type_val = type_val[1:-1]
                elif type_val.startswith('"') and type_val.endswith('",'):
                    type_val = type_val[1:-2]
                
                # Create the reconstructed JSON
                reconstructed_json = {
                    "Explanation": explanation,
                    "Answer": answer,
                    "Type": type_val
                }
                print(f"Successfully parsed JSON using manual content extraction")
                return reconstructed_json
                
        # Fourth attempt: Use a very lenient method - look for specific field patterns
        explanation = ""
        answer = ""
        type_val = ""
        
        explanation_matches = re.findall(r'"Explanation"\s*:\s*"([^"]+)"', response_text)
        if explanation_matches:
            explanation = explanation_matches[0]
            
        answer_matches = re.findall(r'"Answer"\s*:\s*"([^"]+)"', response_text)
        if answer_matches:
            answer = answer_matches[0]
            
        type_matches = re.findall(r'"Type"\s*:\s*"([^"]+)"', response_text)
        if type_matches:
            type_val = type_matches[0]
            
        if explanation and answer and type_val:
            lenient_json = {
                "Explanation": explanation,
                "Answer": answer,
                "Type": type_val
            }
            print(f"Successfully parsed JSON using lenient field extraction")
            return lenient_json
                    
        # If we still can't parse, print detailed debug info
        print(f"Could not parse response. JSON decode error.")
        print(f"Response preview: {response_text[:200]}...")
        
        # Last resort - just extract the raw text for each field if they appear in plain text
        if "Explanation:" in response_text or "Answer:" in response_text:
            raw_explanation = ""
            raw_answer = ""
            raw_type = ""
            
            # For Explanation
            exp_match = re.search(r'Explanation:\s*(.*?)(?:\n|$)', response_text)
            if exp_match:
                raw_explanation = exp_match.group(1).strip()
                
            # For Answer
            ans_match = re.search(r'Answer:\s*(.*?)(?:\n|$)', response_text)
            if ans_match:
                raw_answer = ans_match.group(1).strip()
                
            # For Type - assume it's a standard type if not specified
            type_match = re.search(r'Type:\s*(.*?)(?:\n|$)', response_text)
            if type_match:
                raw_type = type_match.group(1).strip()
            else:
                raw_type = "StringExtractionConfig"  # Default
            
            if raw_explanation or raw_answer:
                emergency_response = {
                    "Explanation": raw_explanation,
                    "Answer": raw_answer,
                    "Type": raw_type
                }
                print(f"Created emergency JSON from raw text")
                return emergency_response
                
        return None
        
    except Exception as e:
        print(f"Error parsing JSON: {str(e)}")
        # Print full traceback for debugging
        import traceback
        traceback.print_exc()
        return None

def format_boxed(response_text: str) -> str:
    if "boxed" in response_text:
        response_text = re.sub(
            r"(\\boxed\{)\s*([^}]+?)\s*(\})",  
            r"\1 \2 \3",                       
            response_text
        )
    
    return response_text
        
def verify_answer(response_json):
    """Verify the answer using math_verify, trying all extraction configs if the initial one fails"""
    if not response_json:
        return False, None
    
    try:
        answer = response_json.get("Answer")
        explanation = response_json.get("Explanation")
        answer_type = response_json.get("Type")
        
        if not (answer and explanation and answer_type):
            return False, None
            
        answer = ensure_math_delimiters(answer)
        
        if answer_type == "LatexExtractionConfig":
            config = [LatexExtractionConfig(), ExprExtractionConfig()]
        elif answer_type == "ExprExtractionConfig":
            config = [ExprExtractionConfig()]
        elif answer_type == "StringExtractionConfig":
            config = [StringExtractionConfig()]
        elif answer_type == "MultiChoiceExtractionConfig":
            config = [MultiChoiceExtractionConfig()]
        else:
            config = [LatexExtractionConfig(), ExprExtractionConfig()]
        
        gold = parse(answer, extraction_config=config)
        parsed_explanation = parse(explanation, extraction_config=config)
        
        if verify(gold, parsed_explanation):
            return True, answer_type
        
        config_types = [
            ("LatexExtractionConfig", [LatexExtractionConfig(), ExprExtractionConfig()]),
            ("ExprExtractionConfig", [ExprExtractionConfig()]),
            ("StringExtractionConfig", [StringExtractionConfig()]),
            ("MultiChoiceExtractionConfig", [MultiChoiceExtractionConfig()])
        ]
        
        for type_name, config in config_types:
            if type_name == answer_type:
                continue 
                
            try:
                gold = parse(format_boxed(answer), extraction_config=config)
                parsed_explanation = parse(format_boxed(explanation), extraction_config=config)
                
                if verify(gold, parsed_explanation):
                    print(f"Verification succeeded with alternative type: {type_name}")
                    return True, type_name
            except Exception as e:
                print(f"Failed with {type_name}: {str(e)}")
                continue
        
        return False, None
    except Exception as e:
        print(f"Error during verification: {str(e)}")
        return False, None

async def process_batch(batch_data, verified_answers, unverified_answers):
    batch = []
    for item in batch_data:
        question = item.get("Question", item.get("Question", "ERROR"))
        explanation = item.get("Explanation", item.get("Explanation", "ERROR"))
        
        if not (question and explanation):
            continue
        
        prompt = format_prompt(question, explanation)
        batch.append({"role": "user", "content": prompt})

    if not batch:
        return

    async with aiohttp.ClientSession() as session:
        responses = await asyncio.gather(
            *[inference_engine.create_chat_completion(session, [msg], LLMSamplingSettings().as_dict(), cookies=cookies, MODEL=MODEL, API_KEY=API_KEY) for msg in batch], 
            return_exceptions=True
        )
    
    for response_text, item in zip(responses, batch_data):
        if isinstance(response_text, Exception) or not response_text:
            continue
        
        response_json = parse_llm_response(response_text)
        if not response_json:
            continue
        
        is_verified, verified_type = verify_answer(response_json)
       
        response_json["Question"] = item.get("Question_refine", item.get("Question"))
        response_json["Original_Explanation"] = item.get("Explanation_refine", item.get("Explanation"))
        response_json["Grade"] = item.get("Grade", "")
        response_json["Source"] = item.get("Source", "")
        response_json["Grade"] = item.get("Grade", "")
        response_json["Difficulty Level"] = item.get("Difficulty Level", "")
        response_json["Source"] = item.get("Source", "")
        response_json["Response Type"] = item.get("Response Type", "")
        response_json["Math Type"] = item.get("Math Type", "")
        response_json["Answer Type"] = item.get("Answer Type", "")
        response_json["Categories"] = item.get("Categories", "")
        
        if is_verified:
            if verified_type and verified_type != response_json.get("Type"):
                response_json["Original_Type"] = response_json.get("Type")
                response_json["Type"] = verified_type
            verified_answers.append(response_json)
        else:
            unverified_answers.append(response_json)

def save_results(verified_answers, unverified_answers):
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(verified_answers, f, ensure_ascii=False, indent=2)
    with open(OUTPUT_FILE_UN, 'w', encoding='utf-8') as f:
        json.dump(unverified_answers, f, ensure_ascii=False, indent=2)

    print(f"Saved {len(verified_answers)} verified answers and {len(unverified_answers)} unverified answers")

async def main():

    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    
    data_files = read_data_file(DATA_FILE_PATH)
    if not data_files:
        print("No data to process")
        return
    
    verified_answers = []
    unverified_answers = []
    total_batches = (len(data_files) + BATCH_SIZE - 1) // BATCH_SIZE
    
    for i in tqdm(range(0, len(data_files), BATCH_SIZE), desc="Processing batches", unit="batch"):
        batch_data = data_files[i:i + BATCH_SIZE]
        await process_batch(batch_data, verified_answers, unverified_answers)
        
        if (i // BATCH_SIZE + 1) % SAVE_EVERY_N_BATCHES == 0 or (i + BATCH_SIZE) >= len(data_files):
            save_results(verified_answers, unverified_answers)
    
    print(f"Processing complete. Final save:")
    save_results(verified_answers, unverified_answers)

if __name__ == "__main__":
    inference_engine = LLMServerProvider(server_address=API_URL)
    asyncio.run(main())