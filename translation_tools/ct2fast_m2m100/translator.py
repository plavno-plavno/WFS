from typing import Dict

import torch
from hf_hub_ctranslate2 import MultiLingualTranslatorCT2fromHfHub
from transformers import AutoTokenizer

import time
from functools import wraps

def timer_decorator(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        print(f"{func.__name__} took {end_time - start_time:.2f} seconds")
        return result
    return wrapper


class MultiLingualTranslatorLive:
    def __init__(
            self,
            model_name_or_path="michaelfeil/ct2fast-m2m100_1.2B",
            device='cuda',
            compute_type= "int8_float16",
            tokenizer=AutoTokenizer.from_pretrained(f"facebook/m2m100_418M")
    ):
        self.model = MultiLingualTranslatorCT2fromHfHub(
            model_name_or_path=model_name_or_path,
            device=device,
            compute_type=compute_type,
            tokenizer=tokenizer
        )

    @timer_decorator
    def get_translation(self, text, src_lang="ru", tgt_langs=["ru","de","en"]) -> Dict:
        len_tgt_langs = len(tgt_langs)
        outputs = self.model.generate(
            [text] * len_tgt_langs,
            src_lang=[src_lang] * len_tgt_langs,
            tgt_lang=tgt_langs
        )
        return {lang: output for lang, output in zip(["rus", "deu","eng"], outputs)}
