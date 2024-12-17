import unittest

from groq import Groq

from translation_tools.llama.translator import clean_json_string, retry_on_error
from translation_tools.llama.utils import GROQ_API_KEY, GroqTranslator, LoadBalancedTranslator


class TestLoadBalancedTranslator(unittest.TestCase):

    def setUp(self):
        self.translator = LoadBalancedTranslator([GroqTranslator])

    def test_translation(self):
        texts_to_translate = [
            "مرحبًا، كيف حالك؟",
            "كيف هو الطقس اليوم؟",
            "ما الجديد في العالم؟", 
            "ما هو فيلمك المفضل؟",
            "ما هي فوائد استخدام الذكاء الاصطناعي؟",
        ]

        target_languages = ["en", "de", "es"]

        for text in texts_to_translate:
            translations = self.translator.get_translations(text, src_lang="ar", tgt_langs=target_languages)

            self.assertTrue(all(lang in translations['translate'] for lang in target_languages))
            self.assertTrue(text in self.translator.buffer_text)
            self.assertLessEqual(len(self.translator.buffer_text), 3)

    def test_clean_json_string(self):
        json_string = '{"translate":{"fr":"D\\\'accord, quatrième."}}'
        
        expected_cleaned_string = '{"translate":{"fr":"D\'accord, quatrième."}}'
        
        cleaned_string = clean_json_string(json_string)
        self.assertEqual(cleaned_string, expected_cleaned_string)
    
    @retry_on_error()
    def get_translation(self):
        return '{"translate":{"fr":"D\\\'accord, quatrième."}}'

    def test_retry_on_error(self):
        expected_result = {
            "translate": {
                "fr": "D'accord, quatrième."
            }
        }
        result = self.get_translation()
        self.assertEqual(result, expected_result)


if __name__ == '__main__':
    unittest.main()