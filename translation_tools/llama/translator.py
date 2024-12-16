from typing import List, Dict
import time
from typing import Dict, Callable, Any
import json


from cerebras.cloud.sdk import Cerebras
from functools import wraps

LANGUAGE_EXAMPLES = {
    "af": "Die profeet Mohammed (vrede sy met hom) het gesê dat die gesin die grondslag van die samelewing is, en ons moet saamwerk om 'n omgewing vol liefde en respek te bou.",
    "am": "አብይ ሞሐምድ (ምስጋና ይደርስበት) ቤተሰቡ የማህበረሰብ መሠረት ነው እና እኛም በፍቅር እና በእምነት የተሞላ አካባቢ ለማቅረብ መስራት እንደሚገባ እንደምንም እንዲህ እንላለን።",
    "ar": "قال النبي محمد صلى الله عليه وسلم إن الأسرة هي أساس المجتمع، ويجب علينا أن نعمل معًا لبناء بيئة مليئة بالحب والاحترام.",
    "ast": "El profeta Muhammad (la paz sea con él) dijo que la familia ye la base de la sociedad, y tenemos que trabayu xuntos pa construir un entornu lleno de amor y respetu.",
    "az": "Peyğəmbər Məhəmməd (ona Allahın salamı olsun) dedi ki, ailə cəmiyyətin təməlidir və biz birlikdə sevgi və hörmət dolu bir mühit yaratmaq üçün çalışmalıyıq.",
    "ba": "Пәйғәмбәр Мөхәммәд (аңа Аллаһтың рәхмәте булһын) әйткән: ғаилә — ул йәмғиәттең нигеҙе, һәм беҙ бергәләп мәхәббәт һәм ихтирам менән тулы мөхит булдырырға тейешбеҙ.",
    "be": "Прафет Мухамед (мір яму) сказаў, што сям'я — гэта аснова грамадства, і мы павінны працаваць разам, каб стварыць асяроддзе, напоўненае любоўю і павагай.",
    "bg": "Пророкът Мохамед (мир на него) каза, че семейството е основата на обществото и ние трябва да работим заедно, за да изградим среда, изпълнена с любов и уважение.",
    "bn": "নবী মুহাম্মদ (শান্তি তার উপর বর্ষিত হোক) বলেছেন যে পরিবার সমাজের ভিত্তি, এবং আমাদের একসাথে কাজ করতে হবে একটি প্রেম ও সম্মানের পরিবেশ গড়ে তোলার জন্য.",
    "br": "Ar profed Mohamed (peoc'h war e) a lâras ez eo ar familh ar reolenn eus ar gumuniezh, ha ret eo deomp labourat asambles evit krouiñ un endro leun a karantez ha a bleg.",
    "bs": "Poslanik Muhammed (neka je mir s njim) je rekao da je porodica temelj društva i da moramo raditi zajedno na izgradnji okruženja ispunjenog ljubavlju i poštovanjem.",
    "ca": "El profeta Muhammad (pau sobre ell) va dir que la família és la base de la societat, i hem de treballar junts per construir un entorn ple d'amor i respecte.",
    "ceb": "Ang propeta Muhammad (kalinaw sa iya) miingon nga ang pamilya mao ang pundasyon sa katilingban, ug kinahanglan magtinabangay kita aron makahimo og usa ka palibot nga puno sa gugma ug pagtahod.",
    "cs": "Prorok Muhammad (pokoj s ním) řekl, že rodina je základem společnosti a my musíme společně pracovat na vytvoření prostředí plného lásky a úcty.",
    "cy": "Dywedodd y proffwyd Muhammad (heddwch arno) fod y teulu yn sylfaen y gymdeithas, a rhaid i ni weithio gyda'n gilydd i greu amgylchedd llawn cariad a pharch.",
    "da": "Profeten Muhammad (fred være med ham) sagde, at familien er grundlaget for samfundet, og vi må arbejde sammen for at skabe et miljø fyldt med kærlighed og respekt.",
    "de": "Der Prophet Muhammad (Frieden sei mit ihm) sagte, dass die Familie das Fundament der Gesellschaft ist, und wir müssen zusammenarbeiten, um eine Umgebung voller Liebe und Respekt zu schaffen.",
    "el": "Ο προφήτης Μωάμεθ (ειρήνη σε αυτόν) είπε ότι η οικογένεια είναι το θεμέλιο της κοινωνίας και πρέπει να συνεργαστούμε για να δημιουργήσουμε ένα περιβάλλον γεμάτο αγάπη και σεβασμό.",
    "en": "The Prophet Muhammad (peace be upon him) said that the family is the foundation of society, and we must work together to build an environment filled with love and respect.",
    "es": "El profeta Muhammad (la paz sea con él) dijo que la familia es la base de la sociedad, y debemos trabajar juntos para construir un entorno lleno de amor y respeto.",
    "et": "Prohvet Muhammad (rahul olgu temaga) ütles, et perekond on ühiskonna alus ning me peame koos töötama armastuse ja austuse täis keskkonna loomise nimel.",
    "fa": "پیامبر محمد (ص) فرمود که خانواده اساس جامعه است و ما باید با هم کار کنیم تا محیطی پر از عشق و احترام بسازیم.",
    "ff": "Annabi Muhammad (sala Allah a alayhi wa sallam) ya ce iyali shine tushe na al'umma, kuma ya kamata mu yi aiki tare don gina muhalli mai cike da kauna da girmamawa.",
    "fi": "Professori Muhammad (rauha hänelle) sanoi, että perhe on yhteiskunnan perusta, ja meidän on työskenneltävä yhdessä luodaksemme ympäristö, joka on täynnä rakkautta ja kunnioitusta.",
    "fr": "Le prophète Muhammad (paix soit sur lui) a dit que la famille est la base de la société et que nous devons travailler ensemble pour créer un environnement rempli d'amour et de respect.",
    "fy": "De profeet Mohammed (frede sy mei him) sei dat de famylje de basis fan 'e maatskippij is, en wy moatte gearwurkje om in omjouwing fol leafde en respekt te bouwen.",
    "ga": "Dúirt an conair Muhammad (síocháin air) gurb é an teaghlach bunús na sochaí, agus caithfimid oibriú le chéile chun timpeallacht atá lán de ghrá agus meas a thógáil.",
    "gd": "Thuirt an fhrèam Muhammad (sìth air) gu bheil an teaghlach na bhunait don chomann, agus feumaidh sinn obrachadh còmhla gus àrainneachd làn gaoil agus urram a thogail.",
    "gl": "O profeta Muhammad (paz con el) dixo que a familia é a base da sociedade e que debemos traballar xuntos para construir un ambiente cheo de amor e respecto.",
    "gu": "પ્રોફેટ મોહમ્મદ (તે પર શાંતિ હોય) એ કહ્યું કે પરિવાર સમાજની મૂળભૂત છે અને અમારે પ્રેમ અને આદરથી ભરેલું વાતાવરણ બનાવવા માટે એકસાથે કામ કરવું જોઈએ.",
    "ha": "Annabi Muhammad (salallahu alayhi wa sallam) ya ce iyali shine tushen al'umma, kuma ya kamata mu yi aiki tare don gina muhalli mai cike da kauna da girmamawa.",
    "he": "הנביא מוחמד (שלום עליו) אמר שהמשפחה היא היסוד של החברה, ואנחנו חייבים לעבוד יחד כדי לבנות סביבה מלאה באהבה וכבוד.",
    "hi": "नबी मुहम्मद (उन पर शांति हो) ने कहा कि परिवार समाज की नींव है, और हमें एक साथ काम करना चाहिए ताकि एक ऐसा वातावरण बनाया जा सके जो प्यार और सम्मान से भरा हो।",
    "hr": "Poslanik Muhammed (neka je mir s njim) rekao je da je porodica temelj društva i da moramo raditi zajedno na izgradnji okruženja ispunjenog ljubavlju i poštovanjem.",
    "ht": "Pwofèt Muhammad (lapè sou li) te di ke fanmi se fondasyon sosyete a, e nou dwe travay ansanm pou bati yon anviwònman ki chaje ak lanmou ak respè.",
    "hu": "Mohamed próféta (béke legyen vele) azt mondta, hogy a család a társadalom alapja, és együtt kell dolgoznunk egy szeretettel és tisztelettel teli környezet megteremtéséért.",
    "hy": "Մուհամեդ մարգարեն (խաղաղություն նրա վրա) ասաց, որ ընտանիքը հասարակության հիմքն է, և մենք պետք է միասին աշխատենք սիրով և հարգանքով լի միջավայր ստեղծելու համար.",
    "id": "Nabi Muhammad (semoga damai bersamanya) berkata bahwa keluarga adalah dasar masyarakat, dan kita harus bekerja sama untuk membangun lingkungan yang penuh cinta dan rasa hormat.",
    "ig": "Ndị mmụọ Muhammad (ụmụnna ya) kwuru na ezinụlọ bụ ntọala nke obodo, anyị kwesịrị ịrụkọ ọrụ ọnụ iji wuo gburugburu jupụtara na ịhụnanya na nsọpụrụ.",
    "ilo": "Ti propeta Muhammad (pakaasi kadagiti) kinuna na ti pamilya ket ti pundasyon ti sosiedad, ken kasapulan tayo a mangtrabaho a kasangay tapno makaaramid ti maysa a lugar a napno ti ayat ken panangipateg.",
    "is": "Spámaðurinn Muhammad (friður sé yfir honum) sagði að fjölskyldan væri grunnurinn að samfélaginu og við verðum að vinna saman að því að byggja umhverfi sem er fullt af kærleika og virðingu.",
    "it": "Il profeta Muhammad (pace su di lui) ha detto che la famiglia è la base della società e dobbiamo lavorare insieme per costruire un ambiente pieno di amore e rispetto.",
    "ja": "預言者ムハンマド（彼に平和あれ）は、家族が社会の基盤であり、私たちは愛と敬意に満ちた環境を築くために共に働かなければならないと言いました。",
    "jv": "Nabi Muhammad (damai ing dhèwèké) ngandika manawa kulawarga iku dhasar masyarakat, lan kita kudu kerja bareng kanggo mbangun lingkungan sing kebak katresnan lan rasa hormat.",
    "ka": "ნაბი მუჰამედმა (მშვენიერი იყოს მისი სახელი) თქვა, რომ ოჯახი არის საზოგადოების საფუძველი და ჩვენ უნდა ვიმუშაოთ ერთად, რომ შევქმნათ გარემო, სავსე სიყვარულით და პატივისცემით.",
    "kk": "Пайғамбар Мұхаммед (оған Алланың сәлемі болсын) отбасы қоғамның негізі екенін айтты, және біз бірге жұмыс істеп, махаббат пен құрметке толы орта құруымыз керек.",
    "km": "ព្រះពុទ្ធសាស្ត្រ មូហាម៉ែត (សុខសាន្តលើគាត់) បាននិយាយថា គ្រួសារនេះគឺជាគ្រឹះនៃសង្គម ហើយយើងត្រូវតែធ្វើការជាមួយគ្នាដើម្បីបង្កើតបរិយាកាសដែលពោរពេញដោយសេចក្តីស្រឡាញ់ និងការគោរព។",
    "kn": "ನಬಿ ಮುಹಮ್ಮದ್ (ಅವರ ಮೇಲೆ ಶಾಂತಿ ಇರಲಿ) ಕುಟುಂಬವು ಸಮಾಜದ ಮೂಲಭೂತವಾಗಿದೆ ಎಂದು ಹೇಳಿದರು, ಮತ್ತು ನಾವು ಪ್ರೀತಿಯ ಮತ್ತು ಗೌರವದಿಂದ ತುಂಬಿದ ಪರಿಸರವನ್ನು ನಿರ್ಮಿಸಲು ಒಟ್ಟಾಗಿ ಕೆಲಸ ಮಾಡಬೇಕು.",
    "ko": "예언자 무함마드(그에게 평화가 있기를)는 가족이 사회의 기초이며, 우리는 사랑과 존경으로 가득 찬 환경을 만들기 위해 함께 일해야 한다고 말했습니다.",
    "lb": "De Prophet Muhammad (fridden ass him) huet gesot, datt d'Famill d'Basis vun der Gesellschaft ass, an mir mussen zesummen schaffen fir eng Ëmfeld ze bauen, déi voller Léift a Respekt ass.",
    "lg": "Nabbi Muhammad (amawulire) yagambye nti, ab’ezi b’okuva mu muryango b’amaanyi g’omu nsi, era tugenda kukola wamu okutandika obulamu obulamu bw’amaanyi n’okuwandiika obulamu bwokuwandiika obulamu bw’amaanyi.",
    "ln": "Nabi Muhammad (nzo na ye) alingi ete libanda ezali motuka ya mboka, mpe tozali na bokonzi ya kokota na yango mpo na kolonga libanda ya bolingo mpe esengo.",
    "lo": "ພຣະເຈົ້າມູຮາມດ (ສຸກສະດີສູງ) ກ່າວວ່າ ຄອບຄົວແມ່ນພື້ນຖານຂອງສັງຄົມ ແລະພວກເຮົາຈະຕ້ອງເຮັດວຽກກັນເພື່ອສ້າງສະຖານທີ່ມີຄວາມຮັກແລະການນັບຖື.",
    "lt": "Pranašas Muhammad (taika su juo) sakė, kad šeima yra visuomenės pamatas, ir mes turime dirbti kartu, kad sukurtume aplinką, kupiną meilės ir pagarbos.",
    "lv": "Pravietis Muhameds (miers ar viņu) teica, ka ģimene ir sabiedrības pamats, un mums jādara kopā, lai izveidotu vidi, kas pilna ar mīlestību un cieņu.",
    "mg": "Ny mpaminany Muhammad (fihavanana aminy) dia nilaza fa ny fianakaviana no fototry ny fiaraha-monina, ary tokony hiara-hiasa isika hanangana tontolo feno fitiavana sy fanajana.",
    "mk": "Пророкот Мухамед (мир со него) рече дека семејството е основа на општеството и ние мора да работиме заедно за да изградиме средина исполнета со љубов и почит.",
    "ml": "പ്രവാചകൻ മുഹമ്മദ് (അവനോട് സമാധാനം ഉണ്ടാവട്ടെ) കുടുംബം സമൂഹത്തിന്റെ അടിസ്ഥാനമാണ്, എന്നും നമ്മൾ സ്നേഹവും ആദരവും നിറഞ്ഞ ഒരു അന്തരീക്ഷം സൃഷ്ടിക്കാൻ ഒരുമിച്ച് പ്രവർത്തിക്കണം.",
    "mn": "Пайгамбар Мухаммад (түүнд амар амгалан байг) гэр бүл нь нийгмийн үндэс гэж хэлсэн бөгөөд бид хайр, хүндэтгэлээр дүүрэн орчныг бий болгохын тулд хамтран ажиллах ёстой.",
    "mr": "पैगंबर मुहम्मद (त्याला शांती लाभो) ने सांगितले की कुटुंब हे समाजाचे मूलभूत आहे आणि आपल्याला प्रेम आणि आदराने भरलेले वातावरण निर्माण करण्यासाठी एकत्र काम करणे आवश्यक आहे.",
    "ms": "Nabi Muhammad (damai ke atasnya) berkata bahawa keluarga adalah asas masyarakat, dan kita mesti bekerja bersama untuk membina persekitaran yang penuh kasih sayang dan hormat.",
    "my": "နာမည်ကြီး မူဟာမက် (သူ့အပေါ် ငြိမ်းချမ်းမှုရှိပါစေ) သည် မိသားစုသည် လူမှုရေး၏ အခြေခံအဆောက်အအုံဖြစ်ပြီး ကျွန်ုပ်တို့သည် အချစ်နှင့် သာယာမှုဖြင့် ပြည့်နှက်သော ပတ်ဝန်းကျင်တစ်ခုကို တည်ဆောက်ရန် ညီညီဝါးဝါး လုပ်ဆောင်ရမည်ဟု ပြောခဲ့သည်။",
    "ne": "नबी मुहम्मद (उनीमाथि शान्ति होस्) ले भनेका छन् कि परिवार समाजको आधार हो, र हामीले प्रेम र सम्मानले भरिएको वातावरण बनाउन सँगै काम गर्नुपर्छ।",
    "nl": "De profeet Mohammed (vrede zij met hem) zei dat de familie de basis van de samenleving is, en we moeten samenwerken om een omgeving te creëren die vol liefde en respect is.",
    "no": "Profeten Muhammad (fred være med ham) sa at familien er grunnlaget for samfunnet, og vi må samarbeide for å bygge et miljø fylt med kjærlighet og respekt.",
    "ns": "Umpostela u Muhammad (ukuthula kube naye) uthanda ukuthi umndeni uyisisekelo senhlangano, futhi kufanele sisebenze ndawonye ukuze sakhe indawo egcwele uthando nokuhlonipha.",
    "oc": "Lo profèta Muhammad (paix sus) diguèt que la familha es la basa de la societat, e que devèm trabalhar ensems per bastir un environament ple d'amor e de respècte.",
    "or": "ପ୍ରବେଶକାରୀ ମୁହମ୍ମଦ (ତାଙ୍କ ଉପରେ ସାନ୍ତି) କହିଛନ୍ତି ଯେ ପରିବାର ସମାଜର ଆଧାର, ଏବଂ ଆମେ ସେହି ଆଧାରରେ ପ୍ରେମ ଓ ସମ୍ମାନର ସହିତ ଭରିଥିବା ପରିବେଶ ତିଆରି କରିବାକୁ ମିଶି କାମ କରିବା ଦରକାର।",
    "pa": "ਨਬੀ ਮੁਹੰਮਦ (ਉਸ ਉੱਤੇ ਸ਼ਾਂਤੀ ਹੋਵੇ) ਨੇ ਕਿਹਾ ਕਿ ਪਰਿਵਾਰ ਸਮਾਜ ਦਾ ਆਧਾਰ ਹੈ ਅਤੇ ਸਾਨੂੰ ਪਿਆਰ ਅਤੇ ਆਦਰ ਨਾਲ ਭਰਪੂਰ ਵਾਤਾਵਰਣ ਬਣਾਉਣ ਲਈ ਇਕੱਠੇ ਕੰਮ ਕਰਨ ਦੀ ਲੋੜ ਹੈ।",
    "pl": "Prorok Muhammad (pokój z nim) powiedział, że rodzina jest fundamentem społeczeństwa, a my musimy współpracować, aby stworzyć środowisko pełne miłości i szacunku.",
    "ps": "پیغمبر محمد (په هغه سلام وي) وویل چې کورنۍ د ټولنې بنسټ دی او موږ باید سره کار وکړو ترڅو د مینې او درنښت څخه ډک چاپیریال جوړ کړو.",
    "pt": "O profeta Muhammad (que a paz esteja com ele) disse que a família é a base da sociedade, e devemos trabalhar juntos para construir um ambiente cheio de amor e respeito.",
    "ro": "Profetul Muhammad (pacea fie asupra lui) a spus că familia este fundamentul societății și trebuie să lucrăm împreună pentru a construi un mediu plin de dragoste și respect.",
    "ru": "Пророк Мухаммед (мир ему) сказал, что семья — это основа общества, и мы должны работать вместе, чтобы создать среду, наполненную любовью и уважением.",
    "sd": "نبي محمد (ان تي سلام هجي) چوي ٿو ته خاندان معاشري جي بنياد آهي، ۽ اسان کي هڪ محبت ۽ احترام سان ڀرپور ماحول ٺاهڻ لاءِ گڏجي ڪم ڪرڻ گهرجي.",
    "si": "ප්‍රවීණ මහාමාර්ගය (ඔහුට සාමයක් වේවා) පවසයි, පවුල සමාජයේ මූලිකයයි, අපි එකට කටයුතු කළ යුතුය, ආදරය සහ ගෞරවය සමඟ පිරුණු පරිසරයක් නිර්මාණය කිරීමට.",
    "sk": "Prorok Muhammad (mier s ním) povedal, že rodina je základom spoločnosti a musíme spolupracovať na vytvorení prostredia plného lásky a úcty.",
    "sl": "Prerok Muhammad (mir z njim) je dejal, da je družina temelj družbe, in morali bi delati skupaj, da ustvarimo okolje, polno ljubezni in spoštovanja.",
    "so": "Nabiga Muhammad (nabad galo) wuxuu yidhi qoyska waa aasaaska bulshada, waana in aan wada shaqeyno si aan u dhisno deegaan buuxda jacayl iyo ixtiraam.",
    "sq": "Profeti Muhammad (paqe mbi të) tha se familja është themeli i shoqërisë dhe ne duhet të punojmë së bashku për të ndërtuar një mjedis të mbushur me dashuri dhe respekt.",
    "sr": "Poslanik Muhammed (neka je mir s njim) rekao je da je porodica temelj društva i da moramo raditi zajedno na izgradnji okruženja ispunjenog ljubavlju i poštovanjem.",
    "ss": "Umphrofethi uMuhammad (ukuthula kube naye) uthe imindeni iyisisekelo somphakathi, futhi kufanele sisebenze ndawonye ukuze sakhe indawo egcwele uthando nokuhlonipha.",
    "su": "Nabi Muhammad (damai kanggo anjeunna) nyarios yén kulawarga mangrupikeun dasar masarakat, sareng urang kedah damel bareng pikeun ngawangun lingkungan anu pinuh ku cinta sareng hormat.",
    "sv": "Profeten Muhammad (fred vara med honom) sa att familjen är grunden för samhället, och vi måste arbeta tillsammans för att skapa en miljö fylld av kärlek och respekt.",
    "sw": "Nabii Muhammad (amani iwe juu yake) alisema kwamba familia ndiyo msingi wa jamii, na tunapaswa kufanya kazi pamoja kujenga mazingira yaliyojaa upendo na heshima.",
    "ta": "நபி முஹம்மது (அவருக்கு அமைதியோடு) குடும்பம் சமூகத்தின் அடித்தளம் என்று கூறினார், நாம் அன்பு மற்றும் மரியாதையால் நிரம்பிய சூழலை உருவாக்க ஒன்றிணைந்து பணியாற்ற வேண்டும்.",
    "th": "ศาสดามูฮัมหมัด (สันติสุขจงมีแด่เขา) กล่าวว่า ครอบครัวเป็นรากฐานของสังคม และเราต้องทำงานร่วมกันเพื่อสร้างสภาพแวดล้อมที่เต็มไปด้วยความรักและความเคารพ.",
    "tl": "Sinabi ng propetang Muhammad (kapayapaan ay sumakanya) na ang pamilya ang pundasyon ng lipunan, at kailangan nating magtulungan upang makabuo ng isang kapaligiran na puno ng pag-ibig at respeto.",
    "tn": "Nabi Muhammad (amandla kuye) o ile a re lelapa ke motheo oa sechaba, 'me re lokela ho sebetsa hammoho ho aha tikoloho e tletseng lerato le tlhompho.",
    "tr": "Peygamber Muhammed (ona selam olsun) ailelerin toplumun temeli olduğunu söyledi ve birlikte sevgi ve saygı dolu bir ortam inşa etmek için çalışmalıyız.",
    "uk": "Пророк Мухаммед (мир йому) сказав, що сім'я є основою суспільства, і ми повинні працювати разом, щоб створити середовище, наповнене любов'ю і повагою.",
    "ur": "نبی محمد (اس پر سلام ہو) نے فرمایا کہ خاندان معاشرے کی بنیاد ہے اور ہمیں ایک محبت اور احترام سے بھرپور ماحول بنانے کے لیے مل کر کام کرنا چاہیے۔",
    "uz": "Payg'ambar Muhammad (ul zotga tinchlik bo'lsin) aytdi: oilaning jamiyatning asosi ekanligini, biz esa birga ishlashimiz kerak, sevgi va hurmatga to'la muhit yaratish uchun.",
    "vi": "Tiên tri Muhammad (bình an trên ngài) đã nói rằng gia đình là nền tảng của xã hội, và chúng ta phải làm việc cùng nhau để xây dựng một môi trường đầy tình yêu và sự tôn trọng.",
    "zh": '先知穆罕默德（愿主福安之）说，家庭是社会的基础，我们必须共同努力，打造一个充满爱与尊重的环境。',
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

def retry_on_error(max_retries: int = 4, retry_delay: float = 0.5):
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
    @retry_on_error(max_retries=4, retry_delay=0.0)
    def translate(self, text: str, src_lang: str = "ar", tgt_langs: List[str] = None, example_response={}) -> Dict[str, str]:
        context = f"""Expert translator: Translate from {src_lang} to {', '.join(tgt_langs)}.
        Important rules:
        1. Return strict JSON format with ISO 2-letter language codes
        2. Keep exact structure as in example
        3. Maintain original meaning without additions
        4. Include all specified target languages
        5. Use previous context only for reference: {" ".join(self.buffer_text)}

        6.Key phrases as recommendations on how they should be translated:
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
        print(f"BUFFER: {self.buffer_text}")
        return translations
