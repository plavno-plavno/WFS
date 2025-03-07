def generate_translation_context(src_lang, tgt_langs, buffer_text, example_response, text):
    context = f"""Expert translator: Translate from {src_lang} to {', '.join(tgt_langs)}.
        Important rules:
        1. Return strict JSON format as provided in a example response with ISO 2-letter language codes
        2. Keep exact structure as in example
        3. Maintain original meaning without additions
        4. Include all specified target languages
        5. Use previous context for reference and try to maintain connection to current phrases translation: < {" ".join(buffer_text)} >
        6. Ensure that any fragments of sentences that appear mistakenly from previous phrases are removed to maintain coherence and accuracy in translation.
        7.Key phrases as recommendations on how they should be translated:
            "سيدنا ونبينا محمد رسول الله --> Our Master Allah and Prophet Muhammad, the messenger of Allah",
            "أما بعد فأوصيكم عباد الله ونفسي بتقوى الله  --> After this, I, as a servant of Allah and myself, advise you to fear Allah",
            "أزواجكم بنينا وحفدا   --> Your wives and children are your descendants",
            "من استطاع  --> Whoever among you",
            "منكم الباءة --> Those who can afford to marry",
            "أضيق --> If they should be poor",
            "ومودتها --> her affection",
            "وتجنون ثمراتها أولادا بارين يحملون اسمكم --> And you will reap the fruits thereof, children who bear your names",
            "يكونون دخرا لكم في كباركم --> They will be a source of provision for you in your old age",
            "على ما فيه محق --> On what brings benefit",
        8. NEVER USE "diety" word in a translations,

        Additional rules:
            "The text is related to Muslims and religion, and the speech belongs to an imam of a mosque.",
            "Never use the word 'lord' in a sentence where Prophet Muhammad is mentioned, instead, use the word 'master'.",
            "Do not translate sentences containing the word 'subtitles', 'Subscribe to the channel', 'Nancy's translation' or 'subtitle', replace these sentences with a space symbol",
            "Use 'thereafter' instead of 'and after that.'",
            "Translate 'Allah' as 'Allah' to maintain its original meaning.",
            "Avoid adding interpretations that may alter the meaning of the religious text.",
            "Be aware of cultural and linguistic nuances specific to Islamic texts and traditions.",
            "Use precise and accurate translations of Islamic terminology, such as 'Quran,' 'Hadith,' 'Sunna,' and 'Sharia.'",
            "Avoid using language that may be perceived as disrespectful or insensitive to Islamic values and principles.",
            "Ensure that the structure of the original text is preserved in the translation."
            "Avoid any blasphemy to islamic translation"

        Example response (strictly follow this format):
        {example_response}
        Text to translate: {text}"""
    return context