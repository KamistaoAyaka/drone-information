try:
    import argostranslate.translate
    LOCAL_TRANSLATION_AVAILABLE = True
except ImportError:
    LOCAL_TRANSLATION_AVAILABLE = False

def translate_text(text, from_lang='en', to_lang='zh'):
    if not LOCAL_TRANSLATION_AVAILABLE:
        return text
    
    try:
        result = argostranslate.translate.translate(text, from_lang, to_lang)
        return result if result else text
    except Exception as e:
        print(f"Translation error: {e}")
        return text

def translate_batch(texts, from_lang='en', to_lang='zh'):
    return [translate_text(t, from_lang, to_lang) for t in texts]
