import os
from typing import Any, Dict, List
from translation_tools.llama.translator import LlamaTranslator
from cerebras.cloud.sdk import Cerebras

class CerebrasTranslator(LlamaTranslator):
    def __init__(self, client=None, buffer_text=None):
        super().__init__(client, buffer_text)
        self.model = "llama3.3-70b"
        self.buffer_text = buffer_text

class LoadBalancedTranslator:
    def __init__(self, translators: List[Any] = None):
        CEREBRAS_API_KEY = os.getenv("CEREBRAS_API_KEY", "")
        self.counter = 0
        self.buffer_text = []
        if translators:
            self.translators = [translator(buffer_text=self.buffer_text) for translator in translators]
        else:
            self.translators = [
                CerebrasTranslator(client=Cerebras(api_key = CEREBRAS_API_KEY),
                                   buffer_text=self.buffer_text),
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
