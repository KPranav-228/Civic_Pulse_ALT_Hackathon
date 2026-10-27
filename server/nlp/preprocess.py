"""Configurable NLP Preprocessing Pipeline for CivicPulse.

Supports fine-grained toggle controls for ablation studies, before/after step
tracking, contractions expansion, stemming, and lemmatization (spaCy / WordNet).
"""

import html
import re
import string
from typing import Any, Dict, List, Optional, Set

import nltk
from nltk.corpus import stopwords, wordnet
from nltk.stem import PorterStemmer, SnowballStemmer, WordNetLemmatizer
from nltk.tokenize import word_tokenize

# Attempt spaCy loading
try:
    import spacy
    try:
        nlp_spacy = spacy.load("en_core_web_sm", disable=["parser", "ner"])
    except Exception:
        nlp_spacy = None
except ImportError:
    nlp_spacy = None

CONTRACTIONS_MAP: Dict[str, str] = {
    "ain't": "is not",
    "aren't": "are not",
    "can't": "cannot",
    "can't've": "cannot have",
    "'cause": "because",
    "could've": "could have",
    "couldn't": "could not",
    "didn't": "did not",
    "doesn't": "does not",
    "don't": "do not",
    "hadn't": "had not",
    "hasn't": "has not",
    "haven't": "have not",
    "he'd": "he would",
    "he'll": "he will",
    "he's": "he is",
    "how'd": "how did",
    "how'll": "how will",
    "how's": "how is",
    "i'd": "i would",
    "i'll": "i will",
    "i'm": "i am",
    "i've": "i have",
    "isn't": "is not",
    "it'd": "it would",
    "it'll": "it will",
    "it's": "it is",
    "let's": "let us",
    "might've": "might have",
    "must've": "must have",
    "mustn't": "must not",
    "shan't": "shall not",
    "she'd": "she would",
    "she'll": "she will",
    "she's": "she is",
    "should've": "should have",
    "shouldn't": "should not",
    "that's": "that is",
    "there's": "there is",
    "they'd": "they would",
    "they'll": "they will",
    "they're": "they are",
    "they've": "they have",
    "wasn't": "was not",
    "we'd": "we would",
    "we'll": "we will",
    "we're": "we are",
    "we've": "we have",
    "weren't": "were not",
    "what'll": "what will",
    "what're": "what are",
    "what's": "what is",
    "what've": "what have",
    "where's": "where is",
    "who'll": "who will",
    "who's": "who is",
    "won't": "will not",
    "wouldn't": "would not",
    "you'd": "you would",
    "you'll": "you will",
    "you're": "you are",
    "you've": "you have"
}


class TextPreprocessor:
    """Configurable text preprocessor with modular stages."""

    def __init__(
        self,
        lowercase: bool = True,
        remove_urls: bool = True,
        remove_emails: bool = True,
        remove_html: bool = True,
        expand_contractions: bool = True,
        normalize_numbers: bool = False,
        normalize_emojis: bool = True,
        remove_punctuation: bool = True,
        remove_stopwords: bool = True,
        stemming: Optional[str] = None,  # "porter" | "snowball" | None
        lemmatize: bool = True,          # Uses spaCy if available, else WordNet
        lemmatize_wordnet: bool = False,  # Force NLTK WordNet
        normalize_whitespace: bool = True,
        min_token_length: int = 2,
        custom_stopwords: Optional[Set[str]] = None
    ):
        self.lowercase_flag = lowercase
        self.remove_urls_flag = remove_urls
        self.remove_emails_flag = remove_emails
        self.remove_html_flag = remove_html
        self.expand_contractions_flag = expand_contractions
        self.normalize_numbers_flag = normalize_numbers
        self.normalize_emojis_flag = normalize_emojis
        self.remove_punctuation_flag = remove_punctuation
        self.remove_stopwords_flag = remove_stopwords
        self.stemming = stemming
        self.lemmatize_flag = lemmatize
        self.lemmatize_wordnet_flag = lemmatize_wordnet
        self.normalize_whitespace_flag = normalize_whitespace
        self.min_token_length = min_token_length

        # Initialize tools
        self.porter = PorterStemmer()
        self.snowball = SnowballStemmer("english")
        self.wordnet_lemmatizer = WordNetLemmatizer()

        # Stopwords
        try:
            self.stop_words = set(stopwords.words("english"))
        except Exception:
            self.stop_words = {"the", "a", "an", "is", "are", "in", "at", "of", "to", "for", "on", "with"}

        if custom_stopwords:
            self.stop_words.update(custom_stopwords)

    def remove_html_tags(self, text: str) -> str:
        """Strip HTML markup and unescape HTML entities."""
        text = html.unescape(text)
        return re.sub(r"<[^>]+>", " ", text)

    def remove_urls(self, text: str) -> str:
        """Replace URLs with empty space or marker."""
        return re.sub(r"https?://\S+|www\.\S+", " ", text)

    def remove_emails(self, text: str) -> str:
        """Strip email addresses."""
        return re.sub(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", " ", text)

    def expand_contractions(self, text: str) -> str:
        """Expand English contractions."""
        pattern = re.compile(
            r"\b(" + "|".join(re.escape(k) for k in CONTRACTIONS_MAP.keys()) + r")\b",
            re.IGNORECASE
        )

        def replace(match):
            contraction = match.group(0).lower()
            replacement = CONTRACTIONS_MAP.get(contraction, contraction)
            if match.group(0)[0].isupper():
                replacement = replacement.capitalize()
            return replacement

        return pattern.sub(replace, text)

    def normalize_numbers(self, text: str) -> str:
        """Replace standalone numbers with a <NUM> marker."""
        return re.sub(r"\b\d+(\.\d+)?\b", "<NUM>", text)

    def normalize_emojis(self, text: str) -> str:
        """Remove unicode emojis."""
        emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"  # emoticons
            "\U0001F300-\U0001F5FF"  # symbols & pictographs
            "\U0001F680-\U0001F6FF"  # transport & map symbols
            "\U0001F1E0-\U0001F1FF"  # flags
            "\U00002702-\U000027B0"
            "\U000024C2-\U0001F251"
            "]+",
            flags=re.UNICODE
        )
        return emoji_pattern.sub(" ", text)

    def to_lowercase(self, text: str) -> str:
        """Convert string to lowercase."""
        return text.lower()

    def remove_punctuation(self, text: str) -> str:
        """Remove punctuation symbols except intra-word hyphens."""
        punct = string.punctuation.replace("-", "")
        translator = str.maketrans(punct, " " * len(punct))
        return text.translate(translator)

    def normalize_whitespace(self, text: str) -> str:
        """Collapse multiple spaces and trim."""
        return re.sub(r"\s+", " ", text).strip()

    def tokenize(self, text: str) -> List[str]:
        """Tokenize text into words."""
        try:
            return word_tokenize(text)
        except Exception:
            return text.split()

    def remove_stopwords(self, tokens: List[str]) -> List[str]:
        """Filter out stopwords and short tokens."""
        return [
            w for w in tokens
            if w.lower() not in self.stop_words and len(w) >= self.min_token_length
        ]

    def stem_tokens(self, tokens: List[str]) -> List[str]:
        """Apply Porter or Snowball stemmer."""
        if self.stemming == "porter":
            return [self.porter.stem(w) for w in tokens]
        elif self.stemming == "snowball":
            return [self.snowball.stem(w) for w in tokens]
        return tokens

    def _get_wordnet_pos(self, treebank_tag: str) -> str:
        """Map treebank POS tag to WordNet POS tag."""
        if treebank_tag.startswith("J"):
            return wordnet.ADJ
        elif treebank_tag.startswith("V"):
            return wordnet.VERB
        elif treebank_tag.startswith("N"):
            return wordnet.NOUN
        elif treebank_tag.startswith("R"):
            return wordnet.ADV
        return wordnet.NOUN

    def lemmatize_wordnet(self, tokens: List[str]) -> List[str]:
        """Lemmatize using NLTK WordNet with POS tags."""
        try:
            tagged = nltk.pos_tag(tokens)
            return [
                self.wordnet_lemmatizer.lemmatize(w, self._get_wordnet_pos(pos))
                for w, pos in tagged
            ]
        except Exception:
            return [self.wordnet_lemmatizer.lemmatize(w) for w in tokens]

    def lemmatize_spacy(self, tokens: List[str]) -> List[str]:
        """Lemmatize using spaCy."""
        if nlp_spacy is None:
            return self.lemmatize_wordnet(tokens)
        doc = nlp_spacy(" ".join(tokens))
        return [token.lemma_ for token in doc if not token.is_space]

    def preprocess(self, text: str) -> str:
        """Execute full preprocessing pipeline on single string."""
        if not text:
            return ""

        t = text
        if self.remove_html_flag:
            t = self.remove_html_tags(t)
        if self.remove_urls_flag:
            t = self.remove_urls(t)
        if self.remove_emails_flag:
            t = self.remove_emails(t)
        if self.expand_contractions_flag:
            t = self.expand_contractions(t)
        if self.normalize_emojis_flag:
            t = self.normalize_emojis(t)
        if self.normalize_numbers_flag:
            t = self.normalize_numbers(t)
        if self.lowercase_flag:
            t = self.to_lowercase(t)
        if self.remove_punctuation_flag:
            t = self.remove_punctuation(t)
        if self.normalize_whitespace_flag:
            t = self.normalize_whitespace(t)

        tokens = self.tokenize(t)

        if self.remove_stopwords_flag:
            tokens = self.remove_stopwords(tokens)

        if self.lemmatize_flag:
            if self.lemmatize_wordnet_flag or nlp_spacy is None:
                tokens = self.lemmatize_wordnet(tokens)
            else:
                tokens = self.lemmatize_spacy(tokens)
        elif self.stemming:
            tokens = self.stem_tokens(tokens)

        return " ".join(tokens)

    def preprocess_with_steps(self, text: str) -> Dict[str, Any]:
        """Return before/after outputs at each step for ablation & notebook demonstrations."""
        steps = []
        current = text

        def add_step(name: str, out: Any):
            steps.append({"step": name, "output": out})

        add_step("Raw Input", current)

        if self.remove_html_flag:
            current = self.remove_html_tags(current)
            add_step("Remove HTML", current)
        if self.remove_urls_flag:
            current = self.remove_urls(current)
            add_step("Remove URLs", current)
        if self.expand_contractions_flag:
            current = self.expand_contractions(current)
            add_step("Expand Contractions", current)
        if self.lowercase_flag:
            current = self.to_lowercase(current)
            add_step("Lowercase", current)
        if self.remove_punctuation_flag:
            current = self.remove_punctuation(current)
            add_step("Remove Punctuation", current)

        tokens = self.tokenize(current)
        add_step("Tokenization", tokens)

        if self.remove_stopwords_flag:
            tokens = self.remove_stopwords(tokens)
            add_step("Stopword Removal", tokens)

        if self.lemmatize_flag:
            tokens = self.lemmatize_spacy(tokens) if nlp_spacy else self.lemmatize_wordnet(tokens)
            add_step("Lemmatization", tokens)
        elif self.stemming:
            tokens = self.stem_tokens(tokens)
            add_step(f"Stemming ({self.stemming})", tokens)

        final_str = " ".join(tokens)
        add_step("Final Cleaned Text", final_str)

        return {
            "original": text,
            "final": final_str,
            "steps": steps
        }

    def preprocess_batch(self, texts: List[str]) -> List[str]:
        """Preprocess a list of documents."""
        return [self.preprocess(t) for t in texts]

    def get_pipeline_description(self) -> str:
        """Summarize active pipeline configuration."""
        active = []
        if self.remove_html_flag:
            active.append("HTML stripping")
        if self.remove_urls_flag:
            active.append("URL stripping")
        if self.expand_contractions_flag:
            active.append("Contraction expansion")
        if self.lowercase_flag:
            active.append("Lowercasing")
        if self.remove_punctuation_flag:
            active.append("Punctuation removal")
        active.append("Word tokenization")
        if self.remove_stopwords_flag:
            active.append("Stopword filtering")
        if self.lemmatize_flag:
            active.append("spaCy Lemmatization" if nlp_spacy else "WordNet Lemmatization")
        elif self.stemming:
            active.append(f"{self.stemming.capitalize()} Stemming")
        return " -> ".join(active)


# Default preprocessor instance
default_preprocessor = TextPreprocessor()

if __name__ == "__main__":
    import sys
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    sample = (
        "<b>URGENT:</b> Flooding won't stop near Ameerpet metro station! "
        "Visit https://ghmc.gov.in/alerts or email help@ghmc.gov.in for tankers. "
        "Roads are blocked across 3 sectors! ⚠️"
    )
    print("Pipeline Configuration:")
    print(default_preprocessor.get_pipeline_description())
    print("\nDemonstration with Step Trace:")
    trace = default_preprocessor.preprocess_with_steps(sample)
    for s in trace["steps"]:
        print(f"  [{s['step']}]: {s['output']}")
