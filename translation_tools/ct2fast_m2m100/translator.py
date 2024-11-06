import logging
from typing import Dict, List
from hf_hub_ctranslate2 import MultiLingualTranslatorCT2fromHfHub
from transformers import AutoTokenizer

import time
from functools import wraps


language_abbr = ["hi", "ar", "de", "fr", "sw"]

def timer_decorator(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        return result
    return wrapper


class MultiLingualTranslatorLive:
    def __init__(
        self,
        model_name_or_path="michaelfeil/ct2fast-m2m100_1.2B",
        device='cuda',
        compute_type= "int8_float16",
        tokenizer=AutoTokenizer.from_pretrained(f"facebook/m2m100_1.2B")
    ):
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        
        self.model = MultiLingualTranslatorCT2fromHfHub(
            model_name_or_path=model_name_or_path,
            device=device,
            compute_type=compute_type,
            tokenizer=tokenizer
        )
        self.logger.info("MultiLingualTranslatorLive class has been initialized successfully.")

    @timer_decorator
    def get_translation(self, text: str, src_lang: str = "en", tgt_langs: List[str] = None) -> Dict[str, str]:
        if tgt_langs is None:
            tgt_langs = language_abbr

        # Exclude source language from target languages
        tgt_langs = [lang for lang in tgt_langs if lang != src_lang and lang != 'en']

        if not tgt_langs:
            print("[WARNING]: No target languages specified after filtering out the source language.")
            return {src_lang: text}

        try:
            # Generate translations for each target language
            outputs = self.model.generate(
                [text] * len(tgt_langs),
                src_lang=[src_lang] * len(tgt_langs),
                tgt_lang=tgt_langs
            )

            src_word_count = len(text.split())
            translations = {src_lang: text}
            for lang, output in zip(tgt_langs, outputs):
                tgt_word_count = len(output.split())
                if tgt_word_count > src_word_count * 3:
                    retry_output = self.model.generate([text], src_lang=[src_lang], tgt_lang=[lang])[0]
                    translations[lang] = retry_output
                else:
                    translations[lang] = output
            return translations

        except Exception as e:
            print(f"[ERROR]: Translation generation failed with error: {e}")
            return {src_lang: text}  # Return original text in case of error