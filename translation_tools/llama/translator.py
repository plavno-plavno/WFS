import re
import time
import json

from typing import Any, Callable, Dict, List
from functools import wraps


LANGUAGE_EXAMPLES = {
    "af": "Die gesin is die grondslag.",
    "am": "ቤተሰቡ የማህበረሰብ መሠረት ነው.",
    "ar": "الأسرة أساس المجتمع.",
    "ast": "La familia ye la base.",
    "az": "Ailə cəmiyyətin təməlidir.",
    "ba": "Ғаилә — ул йәмғиәттең нигеҙе.",
    "be": "Сям'я — гэта аснова грамадства.",
    "bg": "Семейството е основата на обществото.",
    "bn": "পরিবার সমাজের ভিত্তি.",
    "br": "Ar familh ar reolenn.",
    "bs": "Porodica je temelj društva.",
    "ca": "La família és la base.",
    "ceb": "Ang pamilya mao ang pundasyon.",
    "cs": "Rodina je základem společnosti.",
    "cy": "Mae'r teulu'n sylfaen y gymdeithas.",
    "da": "Familien er grundlaget for samfundet.",
    "de": "Die Familie ist das Fundament.",
    "el": "Η οικογένεια είναι το θεμέλιο.",
    "en": "Family is the foundation of society.",
    "es": "La familia es la base.",
    "et": "Perekond on ühiskonna alus.",
    "fa": "خانواده اساس جامعه است.",
    "ff": "Iyali shine tushe na al'umma.",
    "fi": "Perhe on yhteiskunnan perusta.",
    "fr": "La famille est la base.",
    "fy": "De famylje is de basis.",
    "ga": "Is é an teaghlach bunús na sochaí.",
    "gd": "Tha an teaghlach na bhunait.",
    "gl": "A familia é a base.",
    "gu": "પરિવાર સમાજની મૂળભૂત છે.",
    "ha": "Iyali shine tushen al'umma.",
    "he": "המשפחה היא היסוד של החברה.",
    "hi": "परिवार समाज की नींव है.",
    "hr": "Porodica je temelj društva.",
    "ht": "Fanmi se fondasyon sosyete a.",
    "hu": "A család a társadalom alapja.",
    "hy": "Ընտանիքը հասարակության հիմքն է.",
    "id": "Keluarga adalah dasar masyarakat.",
    "ig": "Ezinụlọ bụ ntọala nke obodo.",
    "ilo": "Ti pamilya ket ti pundasyon.",
    "is": "Fjölskyldan er grunnurinn að samfélaginu.",
    "it": "La famiglia è la base.",
    "ja": "家族は社会の基盤です。",
    "jv": "Kulawarga iku dhasar masyarakat.",
    "ka": "ოჯახი საზოგადოების საფუძველია.",
    "kk": "Отбасы қоғамның негізі.",
    "km": "គ្រួសារនេះគឺជាគ្រឹះនៃសង្គម។",
    "kn": "ಕುಟುಂಬವು ಸಮಾಜದ ಮೂಲಭೂತವಾಗಿದೆ.",
    "ko": "가족이 사회의 기초입니다.",
    "lb": "D'Famill ass d'Basis.",
    "lg": "Ezinụlọ bu ntọala nke obodo.",
    "ln": "Libanda ezali motuka ya mboka.",
    "lo": "ຄອບຄົວແມ່ນພື້ນຖານຂອງສັງຄົມ.",
    "lt": "Šeima yra visuomenės pamatas.",
    "lv": "Ģimene ir sabiedrības pamats.",
    "mg": "Ny fianakaviana no fototry ny fiaraha-monina.",
    "mk": "Семейството е основа на општеството.",
    "ml": "കുടുംബം സമൂഹത്തിന്റെ അടിസ്ഥാനമാണ്.",
    "mn": "Гэр бүл нь нийгмийн үндэс.",
    "mr": "कुटुंब हे समाजाचे मूलभूत आहे.",
    "ms": "Keluarga adalah asas masyarakat.",
    "my": "မိသားစုသည် လူမှုရေး၏ အခြေခံအဆောက်အအုံဖြစ်သည်။",
    "ne": "परिवार समाजको आधार हो.",
    "nl": "De familie is de basis.",
    "no": "Familien er grunnlaget for samfunnet.",
    "ns": "Umndeni uyisisekelo senhlangano.",
    "oc": "La familha es la basa.",
    "or": "ପରିବାର ସମାଜର ଆଧାର ଅଟୁଁ.",
    "pa": "ਪਰਿਵਾਰ ਸਮਾਜ ਦਾ ਆਧਾਰ ਹੈ.",
    "pl": "Rodzina jest fundamentem społeczeństwa.",
    "ps": "کورنۍ د ټولنې بنسټ دی.",
    "pt": "A família é a base.",
    "ro": "Familia este fundamentul societății.",
    "ru": "Семья — это основа общества.",
    "sd": "خاندان معاشري جي بنياد آهي.",
    "si": "පවුල සමාජයේ මූලිකයයි.",
    "sk": "Rodina je základom spoločnosti.",
    "sl": "Družina je temelj družbe.",
    "so": "Qoyska waa aasaaska bulshada.",
    "sq": "Familja është themeli i shoqërisë.",
    "sr": "Porodica je temelj društva.",
    "ss": "Imindeni iyisisekelo somphakathi.",
    "su": "Kulawarga mangrupikeun dasar masarakat.",
    "sv": "Familjen är grunden för samhället.",
    "sw": "Familia ndiyo msingi wa jamii.",
    "ta": "குடும்பம் சமூகத்தின் அடித்தளம்.",
    "th": "ครอบครัวเป็นรากฐานของสังคม.",
    "tl": "Ang pamilya ang pundasyon ng lipunan.",
    "tn": "Lelapa ke motheo oa sechaba.",
    "tr": "Aile toplumun temelidir.",
    "uk": "Сім'я є основою суспільства.",
    "ur": "خاندان معاشرے کی بنیاد ہے۔",
    "uz": "Oila jamiyatning asosi.",
    "vi": "Gia đình là nền tảng xã hội.",
    "zh": "家庭是社会的基础。",
}

IGNORE_PHRASES = [
    "subscribing to a channel",
    "Nancy Ajram's translation",
]

def timer_decorator(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        print(f"[DEBUG]: Execution time for {func.__name__}: {end_time - start_time:.2f} seconds")
        return result

    return wrapper


def clean_json_string(json_string: str) -> str:
    json_string = re.sub(r"\\'", "'", json_string)
    return json_string


def retry_on_error(max_retries: int = 4, retry_delay: float = 0.5):
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            for attempt in range(max_retries):
                try:
                    result = func(*args, **kwargs)
                    
                    if isinstance(result, str):
                        try:
                            cleaned_result = clean_json_string(result)
                            parsed_result = json.loads(cleaned_result)
                        except json.JSONDecodeError:
                            raise ValueError("Invalid JSON response")
                    else:
                        parsed_result = result

                    if isinstance(parsed_result, dict):
                        if "translate" in parsed_result:
                            return parsed_result
                        elif "error" in parsed_result:
                            raise ValueError(f"API error: {parsed_result['error']}")
                    
                    raise ValueError("Invalid response structure")

                except Exception as e:
                    print(f"Attempt {attempt + 1}: An error occurred: {e}")
                    print(result)
                    if attempt == max_retries - 1:
                        raise Exception(f"Failed to get translation after {max_retries} attempts: {str(e)}")
                time.sleep(retry_delay)
            
            raise Exception("Unexpected error in translation process")
        return wrapper
    return decorator


class LlamaTranslator:
    
    def __init__(
            self,
            client=None,
            buffer_text=None
        ):
        self.client = client
        self.own_buffer = buffer_text is None
        self.buffer_text = buffer_text if buffer_text else []
        
    def get_example_response(self, tgt_langs, language_examples=LANGUAGE_EXAMPLES):
        translations = {lang: language_examples.get(lang, "") for lang in tgt_langs}
        response = {
            "translate": translations
        }
        return json.dumps(response, ensure_ascii=False, indent=4)

    def split_into_chunks(self, array, chunk_size=30):
        return [array[i:i + chunk_size] for i in range(0, len(array), chunk_size)]

    @timer_decorator
    @retry_on_error(max_retries=4, retry_delay=0.50)
    def translate(self, text: str, src_lang: str = "ar", tgt_langs: List[str] = None, example_response={}) -> Dict[str, str]:
        context = f"""Expert translator: Translate from {src_lang} to {', '.join(tgt_langs)}.
        Important rules:
        1. Return strict JSON format with ISO 2-letter language codes
        2. Keep exact structure as in example
        3. Maintain original meaning without additions
        4. Include all specified target languages
        5. Use previous context only for reference: < {" ".join(self.buffer_text)} > 
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

        Additional rules:
            "Do not translate the word "God" as "diety" in English translations.",
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

        Example response (strictly follow this format):
        {example_response}
        Text to translate: {text}"""
        
        completion = self.client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": context
                },
                {
                    "role": "user",
                    "content": text
                }
            ],
            model=self.model,
            response_format={"type": "json_object"},
            temperature=0.2,
            top_p=0.1,
        )
        return completion.choices[0].message.content

    def get_translations(self, text: str, src_lang: str = "ar", tgt_langs: List[str] = None) -> Dict[str, str]:
        if tgt_langs is None:
            tgt_langs = ["ar", "en", "fa", "ru", "ur"]
        translations = {"translate": {}}
        tgt_lang_chunks = self.split_into_chunks(tgt_langs)
        for tgt_lang_chunk in tgt_lang_chunks:
            example_response = self.get_example_response(tgt_lang_chunk)
            chunk_translations = self.translate(text, src_lang, tgt_lang_chunk, example_response)
            translations["translate"].update(chunk_translations["translate"])
        if self.own_buffer:
            self.buffer_text.append(text)
            if len(self.buffer_text) > 3:
                self.buffer_text.pop(0)
        return translations
