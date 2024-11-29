from typing import List, Dict
import time
from typing import Dict, Callable, Any
import json


from cerebras.cloud.sdk import Cerebras
from functools import wraps

LANGUAGE_EXAMPLES = {
    "af": "Waarom is vinnige afleiding belangrik?",
    "am": "ለምንድን ፈጣን ግምገማ አስፈላጊ ነው?",
    "ar": "لماذا الاستدلال السريع مهم؟",
    "ast": "¿Por qué ye importante la inferencia rápida?",
    "az": "Niyə sürətli nəticə çıxarmaq vacibdir?",
    "ba": "Тиҙ һөҙөмтә сығарыу ни өсөн мөһим?",
    "be": "Чаму хуткае вывад важны?",
    "bg": "Защо бързото извличане е важно?",
    "bn": "দ্রুত অনুমান কেন গুরুত্বপূর্ণ?",
    "br": "Perak eo pouezus an dedenn buan?",
    "bs": "Zašto je brzo zaključivanje važno?",
    "ca": "Per què és important la inferència ràpida?",
    "ceb": "Ngano nga importante ang paspas nga inference?",
    "cs": "Proč je rychlá inference důležitá?",
    "cy": "Pam mae deallusrwydd cyflym yn bwysig?",
    "da": "Hvorfor er hurtig inferens vigtig?",
    "de": "Warum ist schnelles Schließen wichtig?",
    "el": "Γιατί είναι σημαντική η γρήγορη εξαγωγή συμπερασμάτων;",
    "en": "Why is fast inference important?",
    "es": "¿Por qué es importante la inferencia rápida?",
    "et": "Miks on kiire järeldamine oluline?",
    "fa": "چرا استنتاج سریع مهم است؟",
    "ff": "Holno inaama enndoo ko ɓe njiyataa?",
    "fi": "Miksi nopea päättely on tärkeää?",
    "fr": "Pourquoi l'inférence rapide est-elle importante?",
    "fy": "Wêrom is snelle ynferinsje wichtich?",
    "ga": "Cén fáth a bhfuil tátal tapaidh tábhachtach?",
    "gd": "Carson a tha co-dhùnadh luath cudromach?",
    "gl": "Por que é importante a inferencia rápida?",
    "gu": "ઝડપી અનુમાન શા માટે મહત્વપૂર્ણ છે?",
    "ha": "Me yasa saurin fahimta yake da mahimmanci?",
    "he": "למה הסקת מסקנות מהירה חשובה?",
    "hi": "तेज़ निष्कर्षण क्यों महत्वपूर्ण है?",
    "hr": "Zašto je brzo zaključivanje važno?",
    "ht": "Poukisa inferans rapid enpòtan?",
    "hu": "Miért fontos a gyors következtetés?",
    "hy": "Ինչու՞ է արագ եզրակացությունը կարևոր:",
    "id": "Mengapa inferensi cepat penting?",
    "ig": "Gịnị mere ngwa ngwa inference ji dị mkpa?",
    "ilo": "Apay a nasayaat ti mabilis a panangibaga?",
    "is": "Hvers vegna er hröð ályktun mikilvæg?",
    "it": "Perché è importante l'inferenza rapida?",
    "ja": "なぜ迅速な推論が重要なのですか?",
    "jv": "Napa inferensi cepet penting?",
    "ka": "რატომ არის სწრაფი დასკვნა მნიშვნელოვანი?",
    "kk": "Неліктен жылдам қорытынды маңызды?",
    "km": "ហេតុអ្វីបានជាការបញ្ចេញមតិសំខាន់?",
    "kn": "ವೇಗದ ನಿರ್ಗಮನವು ಏಕೆ ಮುಖ್ಯ?",
    "ko": "왜 빠른 추론이 중요한가요?",
    "lb": "Firwat ass séier Ofleedung wichteg?",
    "lg": "Lwaki okukakasa amangu kyetaagisa?",
    "ln": "Mpo na nini kososola noki ezali na ntina?",
    "lo": "ທໍາໄມການສະຫລຸບສອນຈຶ່ງສໍາຄັນ?",
    "lt": "Kodėl greitas išvados yra svarbios?",
    "lv": "Kāpēc ātra secināšana ir svarīga?",
    "mg": "Nahoana ny famaranana haingana no zava-dehibe?",
    "mk": "Зошто е важно брзото заклучување?",
    "ml": "എന്തുകൊണ്ട് വേഗത്തിലുള്ള നിഗമനം പ്രധാനമാണ്?",
    "mn": "Яагаад хурдан дүгнэлт чухал вэ?",
    "mr": "जलद निष्कर्ष का महत्त्वाचे आहे?",
    "ms": "Mengapa inferens cepat penting?",
    "my": "အမြန်ဆုံးအကြံပေးချက်အရေးပါသည်မဟုတ်လား?",
    "ne": "छिटो निष्कर्ष किन महत्वपूर्ण छ?",
    "nl": "Waarom is snelle inferentie belangrijk?",
    "no": "Hvorfor er rask inferens viktig?",
    "ns": "Waarom is vinnige afleiding belangrik?",
    "oc": "Perqué es important l'inferéncia rapida?",
    "or": "ତ୍ୱରିତ ଅନୁମାନ କାହିଁକି ଗୁରୁତ୍ୱପୂର୍ଣ୍ଣ?",
    "pa": "ਤੇਜ਼ ਤਰਕ ਕਿਉਂ ਮਹੱਤਵਪੂਰਨ ਹੈ?",
    "pl": "Dlaczego szybkie wnioskowanie jest ważne?",
    "ps": "ولې چټک استدلال مهم دی؟",
    "pt": "Por que a inferência rápida é importante?",
    "ro": "De ce este importantă inferența rapidă?",
    "ru": "Почему важен быстрый вывод?",
    "sd": "تيز نتيجو ڇو اهم آهي؟",
    "si": "ඉක්මන් නිගමනය මීට වැදගත් කෙසේද?",
    "sk": "Prečo je rýchla inferencia dôležitá?",
    "sl": "Zakaj je hitra inferenca pomembna?",
    "so": "Waa maxay sababta ay muhiim u tahay in si dhakhso leh loo fahmo?",
    "sq": "Pse është e rëndësishme inferenca e shpejtë?",
    "sr": "Zašto je brzo zaključivanje važno?",
    "ss": "Kungani ukuhunyushwa okusheshayo kubalulekile?",
    "su": "Naha inferensi gancang penting?",
    "sv": "Varför är snabb inferens viktig?",
    "sw": "Kwa nini utambuzi wa haraka ni muhimu?",
    "th": "ทำไมการอนุมานที่รวดเร็วถึงสำคัญ?",
    "tl": "Bakit mahalaga ang mabilis na inferensya?",
    "tn": "Ke eng fa kgopolo e e potlakileng e le botlhokwa?",
    "tr": "Neden hızlı çıkarım önemlidir?",
    "uk": "Чому важливий швидкий висновок?",
    "ur": "تیز استدلال کیوں اہم ہے؟",
    "uz": "Nega tezkor xulosa muhim?",
    "vi": "Tại sao suy luận nhanh lại quan trọng?",
    "wo": "Lu taxaw la ni ñu war a xam li muy wax?",
    "xh": "Kutheni ingqiqo ekhawulezayo ibalulekile?",
    "yi": "פארוואס איז שנעלער אויסלייג וויכטיק?",
    "yo": "Kilode ti iyara inference ṣe pataki?",
    "zh": "为什么快速推理很重要？",
    "zu": "Kungani ukuqonda okusheshayo kubalulekile?"
}

def timer_decorator(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        print(f"[DEBUG]: Execution time for {func.__name__}: {end_time - start_time:.2f} seconds")
        return result

    return wrapper

def retry_on_error(max_retries: int = 4, retry_delay: float = 0.00):
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            for attempt in range(max_retries):
                try:
                    result = func(*args, **kwargs)
                    
                    if isinstance(result, str):
                        try:
                            parsed_result = json.loads(result)
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
                    if attempt == max_retries - 1:
                        raise Exception(f"Failed to get translation after {max_retries} attempts: {str(e)}")
                time.sleep(retry_delay)
            
            raise Exception("Unexpected error in translation process")
        return wrapper
    return decorator


class CerebrasTranslator:
    def __init__(self):
        self.client = Cerebras(api_key="csk-wdpk43pkx2n439jc9c8pf9wy5vrhtje6c8pyfcyvy9x3jnhc")
        self.buffer_text = []

    def get_example_response(self, tgt_langs, language_examples=LANGUAGE_EXAMPLES):
        translations = {lang: language_examples.get(lang, "") for lang in tgt_langs}
        response = {
            "translate": translations
        }
        return json.dumps(response, ensure_ascii=False, indent=4)

    def split_into_chunks(self, array, chunk_size=5):
        return [array[i:i + chunk_size] for i in range(0, len(array), chunk_size)]

    @timer_decorator
    @retry_on_error(max_retries=4, retry_delay=0.0)
    def translate(self, text: str, src_lang: str = "ar", tgt_langs: List[str] = None, example_response = {}) -> Dict[str, str]:
        context = f"""Expert translator: Translate from {src_lang} to {', '.join(tgt_langs)}.

        Important rules:
        1. Return strict JSON format with ISO 2-letter language codes
        2. Keep exact structure as in example
        3. Maintain original meaning without additions
        4. Include all specified target languages
        5. Use previous context only for reference: {" ".join(self.buffer_text)}

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
            model="llama3.1-70b",
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
            
        self.buffer_text.append(text)
        if len(self.buffer_text) > 3:
           self.buffer_text.pop(0)

        return translations