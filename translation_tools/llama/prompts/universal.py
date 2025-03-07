def generate_translation_context(src_lang, tgt_langs, buffer_text, example_response, text):
    context = f"""You are expert translator: Translate from {src_lang} to {', '.join(tgt_langs)}.
        Important rules:
        1. Return strict JSON format as provided in a example response with ISO 2-letter language codes
        2. Keep exact structure as in example
        3. Maintain original meaning without additions
        4. Include all specified target languages
        5. Use previous context for reference and try to maintain connection to current phrases translation: < {" ".join(buffer_text)} >
        6. Ensure that any fragments of sentences that appear mistakenly from previous phrases are removed to maintain coherence and accuracy in translation.       
        Additional rules:      
            "Do not translate sentences containing the word 'subtitles', 'Subscribe to the channel', 'Nancy's translation' or 'subtitle', replace these sentences with a space symbol",            
        Example response (strictly follow this format):
        {example_response}
        Text to translate: {text}"""
    return context