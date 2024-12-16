import json
from typing import Any, Dict, List
from translation_tools.llama.translator import LlamaTranslator
from cerebras.cloud.sdk import Cerebras
from groq import Groq

PRIMARY_API_KEY = "csk-wdpk43pkx2n439jc9c8pf9wy5vrhtje6c8pyfcyvy9x3jnhc"
SECONDARY_API_KEY = "csk-k65j52np4nptm6hh4vdpy8x593jm6mtdedhpep4pjrwd2ner"

GROQ_API_KEY = "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"


class CerebrasTranslator(LlamaTranslator):
    def __init__(self, client=None, buffer_text=None):
        super().__init__(client if client else Cerebras(api_key=PRIMARY_API_KEY), buffer_text)
        self.model = "llama3.3-70b"


class GroqTranslator(LlamaTranslator):
    def __init__(self, client=None, buffer_text=None):
        super().__init__(client if client else Groq(api_key=GROQ_API_KEY), buffer_text)
        self.model = "llama3-groq-70b-8192-tool-use-preview"


class LoadBalancedTranslator:
    def __init__(self, translators: List[Any] = None):
        self.counter = 0
        self.buffer_text = []
        if translators:
            self.translators = [translator(buffer_text=self.buffer_text) for translator in translators]
        else:
            self.translators = [
                CerebrasTranslator(client=Cerebras(api_key = PRIMARY_API_KEY),
                                   buffer_text=self.buffer_text),
                CerebrasTranslator(client=Cerebras(api_key = SECONDARY_API_KEY),
                                   buffer_text=self.buffer_text)
            ]

    def get_translations(self, text: str, src_lang: str = "ar", tgt_langs: List[str] = None) -> Dict[str, str]:
        translator_index = self.counter % len(self.translators)
        translator = self.translators[translator_index]
        translations = translator.get_translations(text, src_lang, tgt_langs)

        self.buffer_text.append(text)
        if len(self.buffer_text) > 3:
            self.buffer_text.pop(0)

        self.counter += 1
        return translations
