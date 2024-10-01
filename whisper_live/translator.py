from hf_hub_ctranslate2 import MultiLingualTranslatorCT2fromHfHub


class MultiLingualTranslatorLive:
    def __init__(self, model_name_or_path, device, compute_type, tokenizer):
        self.model = MultiLingualTranslatorCT2fromHfHub(
            model_name_or_path=model_name_or_path,
            device=device,
            compute_type=compute_type,
            tokenizer=tokenizer
        )

    def translate(self, text, src_lang="en", tgt_langs=["fr", "de"]):
        len_tgt_langs = len(tgt_langs)
        outputs = self.model.generate(
            [text]*len_tgt_langs,
            src_lang=[src_lang]*len_tgt_langs,
            tgt_lang=tgt_langs
        )
        return {lang: output for lang, output in zip(tgt_langs, outputs)}