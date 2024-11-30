from typing import Dict, List
from translation_tools.cerebras.translator import CerebrasTranslator
from translation_tools.groq.translator import GroqTranslator


class LoadBalancedTranslator:
    def __init__(self):
        self.cerebras_translator = CerebrasTranslator()
        self.groq_translator = GroqTranslator()
        self.use_cerebras = True

    def get_translations(self, text: str, src_lang: str = "ar", tgt_langs: List[str] = None) -> Dict[str, str]:
        if self.use_cerebras:
            translations = self.cerebras_translator.get_translations(text, src_lang, tgt_langs)
        else:
            translations = self.groq_translator.get_translations(text, src_lang, tgt_langs)

        self.use_cerebras = not self.use_cerebras
        return translations