import unittest

from translation_tools.llama.utils import LoadBalancedTranslator


class TestLoadBalancedTranslator(unittest.TestCase):

    def setUp(self):
        self.translator = LoadBalancedTranslator()

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

if __name__ == '__main__':
    unittest.main()