import logging

from typing import Dict, List
from utils.decorators import timer_decorator
import ctranslate2
import transformers

# List of supported languages
LANGUAGE_ABBREVIATIONS = ["hi", "en", "ar", "de", "fr", "sw"]


class MultiLingualTranslatorLive:
    def __init__(self, model_path="madlad400-3b", compute_type="int8_float16", device="cuda"):
        """
        Initializes the MultiLingualTranslatorLive with a model and tokenizer.

        Args:
            model_path (str): Path or identifier of the CTranslate2 model.
            compute_type (str): The compute type for the model (e.g., "int8_float16").
            device (str): The compute device to use (e.g., "cuda" or "cpu").
        """
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)

        self.translator = ctranslate2.Translator(model_path, compute_type=compute_type, device=device)
        self.tokenizer = transformers.AutoTokenizer.from_pretrained(model_path)
        self.logger.info("MultiLingualTranslatorLive has been initialized successfully.")

    @timer_decorator
    def get_translations(self, text: str, src_lang: str = "en", tgt_langs: List[str] = None) -> Dict[str, str]:
        """
        Translates the given text from the source language to multiple target languages.

        Args:
            text (str): The text to translate.
            src_lang (str): Source language code (default is "en").
            tgt_langs (List[str]): List of target language codes. If None, all supported languages are used.

        Returns:
            Dict[str, str]: A dictionary with translations keyed by language code.
        """
        if tgt_langs is None:
            tgt_langs = LANGUAGE_ABBREVIATIONS

        # Exclude the source language from target languages
        tgt_langs = [lang for lang in tgt_langs if lang != src_lang]

        if not tgt_langs:
            self.logger.warning("No target languages specified after filtering out the source language.")
            return {src_lang: text}

        translations = {src_lang: text}
        translation_tasks = []
        language_map = []

        # Prepare translation tasks for each target language
        for lang in tgt_langs:
            prefix = f"<2{lang}> "
            input_text = prefix + text
            input_tokens = self.tokenizer.convert_ids_to_tokens(self.tokenizer.encode(input_text))
            translation_tasks.append(input_tokens)
            language_map.append(lang)

        try:
            # Perform batch translation
            results = self.translator.translate_batch(
                translation_tasks,
                batch_type="tokens",
                max_batch_size=1024,
                beam_size=1,
                no_repeat_ngram_size=1,
                repetition_penalty=2,
            )

            # Decode the results into translations
            for lang, result in zip(language_map, results):
                output_tokens = result.hypotheses[0]
                translations[lang] = self.tokenizer.decode(self.tokenizer.convert_tokens_to_ids(output_tokens))

            return {"translate": translations}

        except Exception as e:
            self.logger.error(f"Translation generation failed with error: {e}")
            return {src_lang: text}  # Return the original text in case of error
