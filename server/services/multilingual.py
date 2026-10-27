"""Multilingual Alert Translation & Generation for CivicPulse (Telugu, Hindi, English).

Supports:
- Gemini LLM for dynamic context-aware translations when API is configured.
- High-fidelity offline dictionary & lexical translator covering Hyderabad municipal categories,
  action checklists, severity advisories, locality names, and common civic terms in Telugu (తెలుగు) and Hindi (हिंदी).
"""

import json
import logging
import os
import re
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Hyderabad Locality Name Translations
LOCALITY_TRANSLATIONS = {
    "gachibowli": {"te": "గచ్చిబౌలి", "hi": "गच्चीबाउली"},
    "madhapur": {"te": "మాదాపూర్", "hi": "माधापुर"},
    "kondapur": {"te": "కొండాపూర్", "hi": "कोंडापुर"},
    "kukatpally": {"te": "కూకట్‌పల్లి", "hi": "कुकटपल्ली"},
    "hitec city": {"te": "హైటెక్ సిటీ", "hi": "हाइटेक सिटी"},
    "banjara hills": {"te": "బంజారా హిల్స్", "hi": "बंजारा हिल्स"},
    "jubilee hills": {"te": "జూబ్లీ హిల్స్", "hi": "जुबली हिल्स"},
    "begumpet": {"te": "బేగంపేట్", "hi": "बेगमपेट"},
    "secunderabad": {"te": "సికింద్రాబాద్", "hi": "सिकंदराबाद"},
    "charminar": {"te": "చార్మినార్", "hi": "चारमीनार"},
    "ameerpet": {"te": "అమీర్‌పేట్", "hi": "अमीरपेट"},
    "dilsukhnagar": {"te": "దిల్‌సుఖ్‌నగర్", "hi": "दिलसुखनगर"},
    "miyapur": {"te": "మియాపూర్", "hi": "मियापुर"},
    "mehdipatnam": {"te": "మెహిదీపట్నం", "hi": "मेहंदीपटनम"},
    "lingampally": {"te": "లింగంపల్లి", "hi": "लिंगमपल्ली"},
    "manikonda": {"te": "మణికొండ", "hi": "मणिकोंडा"},
    "uppal": {"te": "ఉప్పల్", "hi": "उप्पल"},
    "lb nagar": {"te": "ఎల్బీ నగర్", "hi": "एल.बी. नगर"},
    "somajiguda": {"te": "సోమాజిగూడ", "hi": "सोमाजीगुडा"},
    "alwal": {"te": "అల్వాల్", "hi": "अलवाल"},
    "malkajgiri": {"te": "మల్కాజ్‌గిరి", "hi": "मल्काजगिरी"},
    "tarnaka": {"te": "తార్నాక", "hi": "तारनाका"},
    "koti": {"te": "కోటి", "hi": "कोटी"},
    "abids": {"te": "అబిడ్స్", "hi": "अबिड्स"},
    "nampally": {"te": "నాంపల్లి", "hi": "नामपल्ली"},
    "khairatabad": {"te": "ఖైరతాబాద్", "hi": "खैराताबाद"},
    "tolichowki": {"te": "టోలిచౌకి", "hi": "टोलीचौकी"},
    "chandrayangutta": {"te": "చాంద్రాయణగుట్ట", "hi": "चंद्रायनगुट्टा"},
    "falaknuma": {"te": "ఫలక్‌నుమా", "hi": "फलकनुमा"},
    "bowenpally": {"te": "బోయిన్‌పల్లి", "hi": "बोवेनपल्ली"},
    "bahadurpura": {"te": "బహదూర్‌పురా", "hi": "बहादुरपुरा"},
    "amberpet": {"te": "అంబర్‌పేట్", "hi": "अंबरपेट"},
    "hebbal": {"te": "హెబ్బాల్", "hi": "हेब्बल"},
    "dwarka": {"te": "ద్వారకా", "hi": "द्वारका"},
    "besant nagar": {"te": "బెసెంట్ నగర్", "hi": "बेसेंट नगर"},
}

# Template Fallback Dictionaries
CATEGORY_TRANSLATIONS = {
    "road_closure": {
        "en": "Road Closure / Traffic Diversion",
        "te": "రోడ్డు మూసివేత / ట్రాఫిక్ మళ్లింపు",
        "hi": "सड़क बंदी / यातायात डायवर्जन"
    },
    "water_supply": {
        "en": "Water Supply Interruption",
        "te": "మంచినీటి సరఫరా అంతరాయం",
        "hi": "जलापूर्ति में रुकावट"
    },
    "power_cut": {
        "en": "Power Cut / Outage",
        "te": "విద్యుత్ సరఫరా కోత",
        "hi": "बिजली कटौती"
    },
    "severe_weather": {
        "en": "Severe Weather / Inundation Alert",
        "te": "తీవ్రమైన వాతావరణం / భారీ వర్షాల హెచ్చరిక",
        "hi": "खराब मौसम / जलजमाव की चेतावनी"
    },
    "public_service": {
        "en": "Public Service Notice",
        "te": "ప్రజా సేవల సమాచారం",
        "hi": "सार्वजनिक सेवा सूचना"
    },
    "other": {
        "en": "Civic Notice",
        "te": "పౌర సమాచారం",
        "hi": "नागरिक सूचना"
    }
}

SEVERITY_TRANSLATIONS = {
    "critical": {"en": "CRITICAL", "te": "అత్యవసరం", "hi": "अति गंभीर"},
    "warning": {"en": "WARNING", "te": "హెచ్చరిక", "hi": "चेतावनी"},
    "advisory": {"en": "ADVISORY", "te": "సలహా", "hi": "परामर्श"},
    "info": {"en": "INFO", "te": "సమాచారం", "hi": "सूचना"}
}

ACTION_TRANSLATIONS = {
    "water": {
        "te": [
            "ముందస్తుగా సరిపడా తాగునీటిని మరియు అవసరమైన నీటిని నిల్వ చేసుకోండి.",
            "నీటి ఒత్తిడి తగ్గితే నీటిని కాచి చల్లార్చి తాగండి.",
            "అత్యవసర నీటి ట్యాంకర్ కోసం జలమండలి హెల్ప్‌లైన్ (1916) సంప్రదించండి."
        ],
        "hi": [
            "पर्याप्त पीने का पानी और घरेलू उपयोग के लिए पानी पहले से जमा करके रखें।",
            "पानी का दबाव कम होने पर पानी को उबालकर ही पिएं।",
            "पानी के टैंकर के लिए जल बोर्ड हेल्पलाइन (1916) पर संपर्क करें।"
        ]
    },
    "power": {
        "te": [
            "అత్యవసర వైద్య పరికరాలు మరియు మొబైల్ ఫోన్లను ముందుగానే ఛార్జ్ చేసుకోండి.",
            "విద్యుత్ కోత సమయంలో సున్నితమైన ఎలక్ట్రానిక్ ఉపకరణాల ప్లగ్‌లను తీసివేయండి.",
            "విద్యుత్ పునరుద్ధరించబడినప్పుడు సర్జ్ ప్రొటెక్టర్లను ఉపయోగించండి."
        ],
        "hi": [
            "जरूरी मेडिकल उपकरण और संचार साधनों को पहले से चार्ज रखें।",
            "बिजली कटौती से पहले संवेदनशील इलेक्ट्रॉनिक उपकरणों को अनप्लग करें।",
            "बिजली बहाल होने पर सर्ज प्रोटेक्टर का उपयोग करें।"
        ]
    },
    "road": {
        "te": [
            "ప్రభావిత జంక్షన్ లేదా ఫ్లైఓవర్‌ను తప్పించి ప్రత్యామ్నాయ మార్గాన్ని ఎంచుకోండి.",
            "రద్దీ సమయాల్లో 20 నుండి 30 నిమిషాల ట్రాఫిక్ ఆలస్యాన్ని పరిగణనలోకి తీసుకోండి.",
            "ట్రాఫిక్ పోలీసుల సూచనలు మరియు మార్గదర్శకాలను పాటించండి."
        ],
        "hi": [
            "प्रभावित चौराहे या मार्ग से बचते हुए वैकल्पिक रास्ता चुनें।",
            "व्यस्त समय में 20-30 मिनट की देरी की संभावना मानकर चलें।",
            "ट्रैफिक पुलिस की सलाह और निर्देशों का पालन करें।"
        ]
    },
    "weather": {
        "te": [
            "ఇళ్లలోనే ఉండండి మరియు ఎత్తైన చెట్లు లేదా విద్యుత్ స్తంభాల కింద వాహనాలను పార్క్ చేయవద్దు.",
            "నీటితో నిండిన రోడ్లు మరియు రైల్వే అండర్‌పాస్‌ల వైపు వెళ్లవద్దు.",
            "విపత్తు నిర్వహణ బులెటిన్‌లను ఎప్పటికప్పుడు గమనించండి."
        ],
        "hi": [
            "घरों के अंदर रहें और ऊंचे पेड़ों या बिजली के खंभों के नीचे वाहन पार्क न करें।",
            "जलभराव वाली सड़कों और अंडरपास से यात्रा करने से बचें।",
            "आपदा प्रबंधन बुलेटिन और आपातकालीन नंबरों पर नजर रखें।"
        ]
    },
    "public": {
        "te": [
            "అధికారిక కార్యాలయ వేళలు మరియు అవసరమైన ధృవపత్రాలను ముందుగానే సరిచూసుకోండి.",
            "ఆన్‌లైన్ పోర్టల్ లేదా హెల్ప్‌లైన్ ద్వారా టోకెన్ లేదా సమాచారాన్ని ధృవీకరించుకోండి.",
            "పౌర సేవల హెల్ప్‌లైన్‌ను అవసరమైతే సంప్రదించండి."
        ],
        "hi": [
            "आधिकारिक कार्य समय और आवश्यक दस्तावेजों की पहले से जांच कर लें।",
            "ऑनलाइन पोर्टल या हेल्पलाइन द्वारा स्थिति की पुष्टि करें।",
            "नागरिक सेवा सहायता केंद्र से जानकारी प्राप्त करें।"
        ]
    }
}


def _extract_locality_trans(text: str, target_lang: str) -> Optional[str]:
    """Find any Hyderabad locality in the text and return its translated name."""
    text_lower = text.lower()
    for loc_key, trans_map in LOCALITY_TRANSLATIONS.items():
        if loc_key in text_lower:
            return trans_map.get(target_lang)
    return None


def translate_alert_offline(
    title: str,
    category: str,
    severity: str,
    impact: Optional[str],
    actions: List[str],
    target_lang: str = "te"
) -> Dict[str, Any]:
    """Translate alert structured contents using deterministic high-fidelity templates."""
    target_lang = target_lang.lower()
    if target_lang not in {"te", "hi"}:
        return {
            "title": title,
            "category_name": category.replace("_", " ").title(),
            "severity_label": severity.upper(),
            "expected_impact": impact,
            "recommended_actions": actions,
            "language": "en"
        }

    cat_name = CATEGORY_TRANSLATIONS.get(category, {}).get(target_lang, category)
    sev_name = SEVERITY_TRANSLATIONS.get(severity, {}).get(target_lang, severity)

    # Detect locality if mentioned in title or impact
    combined_text = f"{title} {impact or ''}"
    loc_trans = _extract_locality_trans(combined_text, target_lang)

    # Produce natural fluent headline in target language
    title_lower = title.lower()
    if target_lang == "te":
        loc_prefix = f"{loc_trans} పరిధిలో " if loc_trans else ""
        if "water" in category or "pipeline" in title_lower or "reservoir" in title_lower:
            if "rupture" in title_lower or "leak" in title_lower:
                translated_title = f"{loc_prefix}పైప్‌లైన్ లీకేజీ మరమ్మతులు: మంచినీటి సరఫరా అంతరాయం"
            elif "shutdown" in title_lower or "24-hour" in title_lower:
                translated_title = f"{loc_prefix}తాగునీటి సరఫరా నిలిపివేత హెచ్చరిక"
            elif "contaminat" in title_lower or "boil" in title_lower:
                translated_title = f"{loc_prefix}నీటి కాలుష్యం గుర్తింపు: కాచి చల్లార్చిన నీటిని తాగండి"
            else:
                translated_title = f"{loc_prefix}మంచినీటి సరఫరా అంతరాయం హెచ్చరిక"
            translated_impact = f"{loc_prefix}తాగునీటి సరఫరా నిలిచిపోవచ్చు లేదా ఒత్తిడి తగ్గుతుంది. పౌరులు అవసరమైన నీటిని నిల్వ చేసుకోవాలని సూచన."

        elif "power" in category or "electricity" in title_lower or "load shedding" in title_lower:
            if "rotational" in title_lower or "load shedding" in title_lower:
                translated_title = f"{loc_prefix}విద్యుత్ డిమాండ్ రద్దీ: 2 గంటల రొటేషనల్ విద్యుత్ కోత"
            else:
                translated_title = f"{loc_prefix}లైన్ల నిర్వహణ పనుల కారణంగా విద్యుత్ సరఫరా కోత"
            translated_impact = f"{loc_prefix}నిర్వహణ పనుల సమయంలో విద్యుత్ సరఫరా ఉండదు. గృహోపకరణాలు మరియు వైద్య పరికరాలను ముందస్తుగా సిద్ధం చేసుకోండి."

        elif "road" in category or "traffic" in title_lower or "culvert" in title_lower or "sinkhole" in title_lower:
            if "sinkhole" in title_lower:
                translated_title = f"{loc_prefix}రోడ్డు కుంగిపోవడం వలన ట్రాఫిక్ మళ్లింపు మరియు బారికేడ్లు"
            elif "culvert" in title_lower or "flyover" in title_lower:
                translated_title = f"{loc_prefix}వంతెన మరమ్మతుల కారణంగా రోడ్డు మూసివేత మరియు ట్రాఫిక్ మళ్లింపు"
            elif "one-way" in title_lower or "gas pipeline" in title_lower:
                translated_title = f"{loc_prefix}పైప్‌లైన్ పనుల కారణంగా వన్-వే ట్రాఫిక్ నిబంధన"
            else:
                translated_title = f"{loc_prefix}రోడ్డు మూసివేత మరియు ట్రాఫిక్ మళ్లింపు హెచ్చరిక"
            translated_impact = f"{loc_prefix}ఈ మార్గంలో రాకపోకలు నిలిపివేయబడ్డాయి. వాహనదారులు ప్రత్యామ్నాయ మార్గాల్లో ప్రయాణించగలరు."

        elif "weather" in category or "flood" in title_lower or "rain" in title_lower:
            translated_title = f"{loc_prefix}భారీ వర్షాలు మరియు ముంపు హెచ్చరిక"
            translated_impact = f"{loc_prefix}భారీ వర్షాల కారణంగా రోడ్లపై నీరు చేరే ప్రమాదం ఉంది. అత్యవసరమైతే తప్ప బయటకు రావద్దు."

        elif "public_service" in category or "bus" in title_lower or "tax" in title_lower:
            if "tax" in title_lower:
                translated_title = f"{loc_prefix}మున్సిపల్ ఆస్తి పన్ను వసూలు ప్రత్యేక శిబిరం"
            elif "bus" in title_lower:
                translated_title = f"{loc_prefix}ఆర్టీసీ బస్సు రూట్ తాత్కాలిక మార్పు"
            else:
                translated_title = f"{loc_prefix}ప్రజా సేవల ముఖ్యమైన సమాచారం"
            translated_impact = f"{loc_prefix}పౌరుల సౌలభ్యం కొరకు మున్సిపల్ సేవలు అందించబడుతున్నాయి. వివరాలు గమనించగలరు."

        else:
            translated_title = f"{loc_prefix}{cat_name} హెచ్చరిక"
            translated_impact = f"{loc_prefix}ప్రభావిత ప్రాంతంలో మున్సిపల్ పనులు జరుగుతున్నాయి. పౌరులు సహకరించగలరు."

    else:  # Hindi (hi)
        loc_prefix = f"{loc_trans} क्षेत्र में " if loc_trans else ""
        if "water" in category or "pipeline" in title_lower or "reservoir" in title_lower:
            if "rupture" in title_lower or "leak" in title_lower:
                translated_title = f"{loc_prefix}पाइपलाइन लीकेज मरम्मत: जलापूर्ति में रुकावट"
            elif "shutdown" in title_lower or "24-hour" in title_lower:
                translated_title = f"{loc_prefix}24 घंटे की जलापूर्ति बंदी सूचना"
            elif "contaminat" in title_lower or "boil" in title_lower:
                translated_title = f"{loc_prefix}जल प्रदूषण चेतावनी: उबला हुआ पानी ही पिएं"
            else:
                translated_title = f"{loc_prefix}जलापूर्ति में रुकावट की सूचना"
            translated_impact = f"{loc_prefix}पानी की आपूर्ति बाधित रहेगी। नागरिक पर्याप्त पानी पहले से जमा कर लें।"

        elif "power" in category or "electricity" in title_lower or "load shedding" in title_lower:
            if "rotational" in title_lower or "load shedding" in title_lower:
                translated_title = f"{loc_prefix}अधिक मांग के कारण 2 घंटे की क्रमिक बिजली कटौती"
            else:
                translated_title = f"{loc_prefix}आवश्यक रखरखाव के कारण बिजली कटौती"
            translated_impact = f"{loc_prefix}बिजली आपूर्ति बंद रहेगी। संवेदनशील उपकरण व मोबाइल पहले से चार्ज रखें।"

        elif "road" in category or "traffic" in title_lower or "culvert" in title_lower or "sinkhole" in title_lower:
            if "sinkhole" in title_lower:
                translated_title = f"{loc_prefix}सड़क धंसने के कारण यातायात डायवर्जन एवं बैरिकेड्स"
            elif "culvert" in title_lower or "flyover" in title_lower:
                translated_title = f"{loc_prefix}पुल मरम्मत के कारण सड़क बंदी एवं मार्ग परिवर्तन"
            elif "one-way" in title_lower or "gas pipeline" in title_lower:
                translated_title = f"{loc_prefix}पाइपलाइन कार्य के कारण एकतरफा यातायात लागू"
            else:
                translated_title = f"{loc_prefix}सड़क बंदी एवं यातायात डायवर्जन की चेतावनी"
            translated_impact = f"{loc_prefix}इस मार्ग पर यातायात प्रभावित रहेगा। यात्री वैकल्पिक रास्तों का उपयोग करें।"

        elif "weather" in category or "flood" in title_lower or "rain" in title_lower:
            translated_title = f"{loc_prefix}भारी बारिश एवं जलभराव की चेतावनी"
            translated_impact = f"{loc_prefix}सड़कों पर जलभराव की संभावना है। बहुत जरूरी न होने पर यात्रा से बचें।"

        elif "public_service" in category or "bus" in title_lower or "tax" in title_lower:
            if "tax" in title_lower:
                translated_title = f"{loc_prefix}नगर निगम संपत्ति कर विशेष शिविर"
            elif "bus" in title_lower:
                translated_title = f"{loc_prefix}सार्वजनिक बस मार्ग में अस्थायी बदलाव"
            else:
                translated_title = f"{loc_prefix}सार्वजनिक सेवा महत्वपूर्ण सूचना"
            translated_impact = f"{loc_prefix}नागरिक सुविधा हेतु यह सेवा उपलब्ध कराई गई है। समय पर लाभ उठाएं।"

        else:
            translated_title = f"{loc_prefix}{cat_name} सूचना"
            translated_impact = f"{loc_prefix}क्षेत्र में संबंधित कार्य प्रगति पर है। नागरिक सहयोग करें।"

    # Choose actions translation
    action_key = (
        "water" if "water" in category
        else "power" if "power" in category
        else "road" if "road" in category
        else "weather" if "weather" in category
        else "public"
    )
    translated_actions = ACTION_TRANSLATIONS.get(action_key, {}).get(target_lang, actions)

    return {
        "title": translated_title,
        "category_name": cat_name,
        "severity_label": sev_name,
        "expected_impact": translated_impact,
        "recommended_actions": translated_actions,
        "language": target_lang
    }


def translate_alert(
    title: str,
    category: str,
    severity: str,
    impact: Optional[str],
    actions: List[str],
    target_lang: str = "en"
) -> Dict[str, Any]:
    """Translate alert contents using Gemini LLM if available, else offline dictionary."""
    target_lang = (target_lang or "en").lower()
    if target_lang == "en":
        return {
            "title": title,
            "category_name": category.replace("_", " ").title(),
            "severity_label": severity.upper(),
            "expected_impact": impact,
            "recommended_actions": actions,
            "language": "en"
        }

    # Attempt Gemini LLM Translation
    api_key = os.getenv("GEMINI_API_KEY")
    if api_key and api_key != "your_gemini_api_key_here":
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel("gemini-1.5-flash")

            lang_label = "Telugu (తెలుగు)" if target_lang == "te" else "Hindi (हिंदी)"
            prompt = (
                f"You are a municipal alert translator for Hyderabad. Translate this civic notification into natural {lang_label}.\n"
                f"Title: {title}\n"
                f"Impact: {impact}\n"
                f"Actions: {json.dumps(actions)}\n\n"
                f"Return JSON strictly with format:\n"
                f"{{\n"
                f'  "title": "translated title",\n'
                f'  "expected_impact": "translated impact",\n'
                f'  "recommended_actions": ["action1", "action2"]\n'
                f"}}"
            )
            response = model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
            parsed = json.loads(response.text.strip())
            parsed["category_name"] = CATEGORY_TRANSLATIONS.get(category, {}).get(target_lang, category)
            parsed["severity_label"] = SEVERITY_TRANSLATIONS.get(severity, {}).get(target_lang, severity)
            parsed["language"] = target_lang
            return parsed
        except Exception as e:
            logger.warning(f"Gemini translation failed ({e}). Falling back to template dictionary.")

    # Fallback to high-quality template translations
    return translate_alert_offline(title, category, severity, impact, actions, target_lang)
