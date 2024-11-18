from typing import List, Dict
import json5

import os
import time
from typing import Dict, Callable, Any
import json


from cerebras.cloud.sdk import Cerebras
from functools import wraps

def timer_decorator(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        print(f"[DEBUG]: Execution time for {func.__name__}: {end_time - start_time:.2f} seconds")
        return result

    return wrapper

def retry_on_error(max_retries: int = 3, retry_delay: float = 0.25):
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            for attempt in range(max_retries):
                try:
                    result = func(*args, **kwargs)
                    try:
                        # Using json5 for more tolerant JSON parsing
                        parsed_result = json5.loads(result)
                        if isinstance(parsed_result, dict) and "translate" in parsed_result:
                            return parsed_result
                        else:
                            raise ValueError("Invalid response structure")
                    except json5.JSONDecodeError as e:
                        print(f"Attempt {attempt + 1}: JSON parsing error: {e}")
                        if attempt == max_retries - 1:
                            raise Exception("Failed to get valid translation after all attempts")
                except Exception as e:
                    print(f"Attempt {attempt + 1}: An error occurred: {e}")
                    if attempt == max_retries - 1:
                        raise Exception(f"Failed to get translation after {max_retries} attempts: {str(e)}")
                time.sleep(retry_delay)
            raise Exception("Unexpected error in translation process")
        return wrapper
    return decorator

class CerebrasTranslator:
    def __init__(self):
        self.client = Cerebras(
            # This is the default and can be omitted
            api_key="csk-wdpk43pkx2n439jc9c8pf9wy5vrhtje6c8pyfcyvy9x3jnhc"
        )
        self.buffer_text = ""
    @timer_decorator
    @retry_on_error(max_retries=3, retry_delay=0.25)
    def get_translation(self, text: str, src_lang: str = "ar", tgt_langs: List[str] = None) -> Dict[str, str]:
        if tgt_langs is None:
            tgt_langs = ["en", "fa", "ur", "ru", "no", "ar"]
            
        example_response = '''{
            "translate": {
                "en": "Why is fast inference important?",
                "fa": "چرا استنتاج سریع مهم است؟",
                "ur": "تیز استدلال کیوں اہم ہے؟",
                "ru": "Почему важен быстрый вывод?",
                "no": "Hvorfor er rask inferens viktig?",
                "ar": "لماذا الاستدلال السريع مهم؟"
            }
        }'''

        context = f"""Expert translator: Translate from {src_lang} to {', '.join(tgt_langs)}.
        Return strict JSON with ISO 2-letter language codes. Previous context: {self.buffer_text}

        Example:
        {example_response}

        Text: {text}"""

        completion = self.client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": context
                },
                {
                    "role": "user",
                    "content": text
                }
            ],
            model="llama3.1-8b",
        )

        # Update buffer with current text for context
        self.buffer_text = text

        return completion.choices[0].message.content
    




        # context = f"""You are an expert translator with deep knowledge of cultural context and linguistic nuances. 
        # Your task is to translate the following text from {src_lang} to the following languages: {', '.join(tgt_langs)}.

        # Important translation guidelines:
        # 1. Maintain literal translation where possible as the text might be part of a larger context
        # 2. Use the previous context ({self.buffer_text}) cautiously, only for general background information, not for direct translation
        # 3. Pay special attention to the original text structure and word order when possible
        # 4. Avoid over-interpretation or excessive localization
        # 5. Keep the translation as close to the source text as grammatically acceptable
        # 6. Consider that this might be a part of an ongoing conversation or larger text
        # 7. Use previous translations as reference for terminology consistency
        # 8. Preserve any special terms, numbers, or proper names exactly as they appear
        # 9. Do not attempt to anticipate or guess upcoming parts of the text
        # 10. Translate as closely to the original text as possible, even if it seems incomplete
        # 11. Return exactly the number of translation elements specified in tgt_langs plus src_lang

        # Important rules:
        # 1. Maintain the original meaning and tone
        # 2. Consider cultural context
        # 3. Keep any special terms or proper names unchanged
        # 4. Return only raw text without any markdown
        # 5. Provide translations in JSON format
        # 6. Do not add or omit any information not present in the original text
        # 7. Use the previous context very carefully, only for understanding, not for adding content

        # Previous context for better translation (if any): {self.buffer_text}
        
        # Example response:
        # {example_response}
        
        # Text to translate: {text}
        # """