import logging
import time
from typing import Dict, List
from functools import wraps
import ctranslate2
import transformers
from sentencepiece import SentencePieceProcessor

language_abbr = ["hi", "en", "ar", "de", "fr", "sw"]


def timer_decorator(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        print(f"[DEBUG]: Execution time for {func.__name__}: {end_time - start_time:.2f} seconds")
        return result

    return wrapper


class MultiLingualTranslatorLive:
    def __init__(
            self,
            model_path="madlad400-3b",
            compute_type="int8_float16",
            device="cuda"
    ):
        """
        Initializes the AlternativeTranslator with a custom model and tokenizer.

        Args:
            model_path (str): Path or identifier of the CTranslate2 model.
            tokenizer_path (str): Path or identifier of the tokenizer in Hugging Face format.
            compute_type (str): The compute type for the model (e.g., "auto" for best performance).
        """
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)

        self.translator = ctranslate2.Translator(model_path, compute_type=compute_type, device=device)
        self.tokenizer2 = transformers.AutoTokenizer.from_pretrained(model_path)
        self.tokenizer = SentencePieceProcessor()
        self.tokenizer.load(f"{model_path}/sentencepiece.model")
        self.logger.info("AlternativeTranslator has been initialized successfully.")

    @timer_decorator
    def get_translation(self, text: str, src_lang: str = "en", tgt_langs: List[str] = None) -> Dict[str, str]:
        if tgt_langs is None:
            tgt_langs = language_abbr

        # Exclude source language from target languages
        tgt_langs = [lang for lang in tgt_langs if lang != src_lang]

        if not tgt_langs:
            self.logger.warning("No target languages specified after filtering out the source language.")
            return {src_lang: text}

        translations = {src_lang: text}
        translation_tasks = []
        translation_tasks2 = []
        language_map = []

        # Prepare translation tasks for each target language
        for lang in tgt_langs:
            prefix = f"<2{lang}> "
            input_text = prefix + text
            input_tokens = self.tokenizer.encode(input_text, out_type=str)
            input_tokens2 = self.tokenizer2.convert_ids_to_tokens(self.tokenizer2.encode(input_text))

            translation_tasks.append(input_tokens)
            translation_tasks2.append(input_tokens2)

            language_map.append(lang)  # Keep track of which language each task corresponds to
        try:
            # Perform batch translation

            results2 = self.translator.translate_batch(translation_tasks2,
                                                      batch_type="tokens",
                                                      max_batch_size=1024,
                                                      beam_size=1,
                                                      no_repeat_ngram_size=1,
                                                      repetition_penalty=2,
                                                      )

         #   results = self.translator.translate_batch(translation_tasks,
         #                                             batch_type="tokens",
         #                                             max_batch_size=1024,
         #                                             beam_size=1,
         #                                             no_repeat_ngram_size=1,
         #                                             repetition_penalty=2,
         #                                             )

            # Process results and assign translations
          # for lang, result in zip(language_map, results):

           #     output_tokens = result.hypotheses[0]
                #translations[lang]  = self.tokenizer.decode(output_tokens),

            for lang, result2 in zip(language_map, results2):
                output_tokens2 = result2.hypotheses[0]
                translations[lang]=  self.tokenizer2.decode(self.tokenizer2.convert_tokens_to_ids(output_tokens2))

            return translations

        except Exception as e:
            self.logger.error(f"Translation generation failed with error: {e}")
            return {src_lang: text}  # Return original text in case of error


        except Exception as e:
            self.logger.error(f"Translation generation failed with error: {e}")
            return {src_lang: text}  # Return original text in case of error
