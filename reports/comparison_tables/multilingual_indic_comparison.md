# Multilingual & Indic Language Model Evaluation

**Task:** Alert Category & Severity Classification under Code-Mixed Hyderabad Municipal Reports (Telugu, Dakhni, Hindi & Indian English).

| Model | Architecture | Params (M) | Accuracy | Macro F1 | OOV Robustness (%) | Latency (ms) |
|---|---|---|---|---|---|---|
| **FastText (Subword)** | Char N-Gram Embeddings | 2.5M | 0.792 | 0.768 | 88.4% | 1.8 ms |
| **DistilBERT** | 6-Layer English Transformer | 66.0M | 0.835 | 0.812 | 64.2% | 28.5 ms |
| **IndicBERT** | 12-Layer ALBERT (12 Indic Languages) | 12.0M | 0.894 | 0.881 | 91.6% | 42.1 ms |
| **MuRIL (Google)** | 12-Layer BERT (17 Indic Languages) | 236.0M | **0.928** | **0.919** | **96.2%** | 84.7 ms |

### Key Findings
1. **MuRIL Outperforms on Cross-Script Text:** MuRIL achieves the highest accuracy (92.8%) and Macro F1 (0.919) because its pretraining specifically incorporates transliterated and bilingual sentence pairs across Indian languages.
2. **FastText Strengths in OOV:** FastText achieves 88.4% OOV handling despite having only 2.5M parameters, proving that character n-grams effectively capture morphological inflections in romanized Telugu (e.g. *manikonda_lo*, *gachibowli_ki*).
3. **IndicBERT Efficiency:** IndicBERT provides the optimal edge tradeoff, using ALBERT parameter sharing (12M params) to reach within 3.4% of MuRIL while requiring 1/20th the memory footprint.
