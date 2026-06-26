# BanglaGamba Tokenizer Evaluation

**Date:** 2026-06-26 15:42:31


## Tokenizer Summary

| Tokenizer | Vocab Size | Type |
|---|---|---|
| BanglaGamba | 48,000 | Unigram (SP) |
| mBART-50 | 250,054 | Auto |
| NLLB-200 | 256,204 | Auto |
| BanglaBERT | 101,975 | Auto |
| GPT-2 | 50,257 | Auto |

## Curated Sentence Tests

### Fertility (tokens/word, lower = better)

| Category | BanglaBERT | BanglaGamba | GPT-2 | NLLB-200 | mBART-50 |
|---|---|---|---|---|---|
| bangla_formal | 1.953 | 1.256 | 13.442 | 1.581 | 1.465 |
| bangla_news | 2.152 | 1.152 | 14.636 | 2.061 | 1.848 |
| english | 1.102 | 1.245 | 1.184 | 1.367 | 1.347 |
| banglish | 1.171 | 2.286 | 2.143 | 1.714 | 1.657 |
| code_mixed | 1.440 | 1.300 | 6.340 | 1.340 | 1.380 |
| python_code | 3.138 | 3.310 | 2.586 | 2.897 | 3.069 |

### Compression (chars/token, higher = better)

| Category | BanglaBERT | BanglaGamba | GPT-2 | NLLB-200 | mBART-50 |
|---|---|---|---|---|---|
| bangla_formal | 3.42 | 5.31 | 0.50 | 4.22 | 4.56 |
| bangla_news | 3.30 | 6.16 | 0.48 | 3.44 | 3.84 |
| english | 5.61 | 4.97 | 5.22 | 4.52 | 4.59 |
| banglish | 4.76 | 2.44 | 2.60 | 3.25 | 3.36 |
| code_mixed | 3.50 | 3.88 | 0.79 | 3.76 | 3.65 |
| python_code | 2.34 | 2.22 | 2.84 | 2.54 | 2.39 |

### UNK Rate % (lower = better)

| Category | BanglaBERT | BanglaGamba | GPT-2 | NLLB-200 | mBART-50 |
|---|---|---|---|---|---|
| bangla_formal | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| bangla_news | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| english | 83.3333 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| banglish | 82.9268 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| code_mixed | 20.8333 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| python_code | 34.0659 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |

## Corpus Tests (sampled from cleaned data)

### Fertility (tokens/word, lower = better)

| Category | BanglaBERT | BanglaGamba | GPT-2 | NLLB-200 | mBART-50 |
|---|---|---|---|---|---|
| corpus_bangla | 2.000 | 1.356 | 12.934 | 2.113 | 2.083 |
| corpus_english | 1.206 | 1.458 | 1.342 | 1.471 | 1.465 |

### Compression (chars/token, higher = better)

| Category | BanglaBERT | BanglaGamba | GPT-2 | NLLB-200 | mBART-50 |
|---|---|---|---|---|---|
| corpus_bangla | 3.29 | 4.86 | 0.51 | 3.12 | 3.16 |
| corpus_english | 5.11 | 4.23 | 4.59 | 4.19 | 4.21 |

### UNK Rate % (lower = better)

| Category | BanglaBERT | BanglaGamba | GPT-2 | NLLB-200 | mBART-50 |
|---|---|---|---|---|---|
| corpus_bangla | 2.3137 | 2.1260 | 0.0000 | 0.5165 | 0.0007 |
| corpus_english | 81.2349 | 1.8284 | 0.0000 | 0.9303 | 0.0012 |

## Detailed Metrics

### bangla_formal

| Metric | BanglaBERT | BanglaGamba | GPT-2 | NLLB-200 | mBART-50 |
|---|---|---|---|---|---|
| fertility | 1.953 | 1.256 | 13.442 | 1.581 | 1.465 |
| compression | 3.42 | 5.31 | 0.5 | 4.22 | 4.56 |
| unk_rate_pct | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| avg_tokens_per_doc | 16.8 | 10.8 | 115.6 | 13.6 | 12.6 |
| docs_per_sec | 21204.8 | 5437.3 | 6210.1 | 23831.3 | 7628.8 |

### bangla_news

| Metric | BanglaBERT | BanglaGamba | GPT-2 | NLLB-200 | mBART-50 |
|---|---|---|---|---|---|
| fertility | 2.152 | 1.152 | 14.636 | 2.061 | 1.848 |
| compression | 3.3 | 6.16 | 0.48 | 3.44 | 3.84 |
| unk_rate_pct | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| avg_tokens_per_doc | 14.2 | 7.6 | 96.6 | 13.6 | 12.2 |
| docs_per_sec | 31968.8 | 17389.3 | 21845.3 | 33447.4 | 19490.3 |

### english

| Metric | BanglaBERT | BanglaGamba | GPT-2 | NLLB-200 | mBART-50 |
|---|---|---|---|---|---|
| fertility | 1.102 | 1.245 | 1.184 | 1.367 | 1.347 |
| compression | 5.61 | 4.97 | 5.22 | 4.52 | 4.59 |
| unk_rate_pct | 83.3333 | 0.0 | 0.0 | 0.0 | 0.0 |
| avg_tokens_per_doc | 10.8 | 12.2 | 11.6 | 13.4 | 13.2 |
| docs_per_sec | 33989.5 | 21465.2 | 33394.1 | 28036.8 | 14198.7 |

### banglish

| Metric | BanglaBERT | BanglaGamba | GPT-2 | NLLB-200 | mBART-50 |
|---|---|---|---|---|---|
| fertility | 1.171 | 2.286 | 2.143 | 1.714 | 1.657 |
| compression | 4.76 | 2.44 | 2.6 | 3.25 | 3.36 |
| unk_rate_pct | 82.9268 | 0.0 | 0.0 | 0.0 | 0.0 |
| avg_tokens_per_doc | 8.2 | 16.0 | 15.0 | 12.0 | 11.6 |
| docs_per_sec | 45590.3 | 38130.0 | 45689.6 | 41943.0 | 27095.0 |

### code_mixed

| Metric | BanglaBERT | BanglaGamba | GPT-2 | NLLB-200 | mBART-50 |
|---|---|---|---|---|---|
| fertility | 1.44 | 1.3 | 6.34 | 1.34 | 1.38 |
| compression | 3.5 | 3.88 | 0.79 | 3.76 | 3.65 |
| unk_rate_pct | 20.8333 | 0.0 | 0.0 | 0.0 | 0.0 |
| avg_tokens_per_doc | 14.4 | 13.0 | 63.4 | 13.4 | 13.8 |
| docs_per_sec | 32066.5 | 25890.8 | 25606.3 | 32922.3 | 21936.7 |

### python_code

| Metric | BanglaBERT | BanglaGamba | GPT-2 | NLLB-200 | mBART-50 |
|---|---|---|---|---|---|
| fertility | 3.138 | 3.31 | 2.586 | 2.897 | 3.069 |
| compression | 2.34 | 2.22 | 2.84 | 2.54 | 2.39 |
| unk_rate_pct | 34.0659 | 0.0 | 0.0 | 0.0 | 0.0 |
| avg_tokens_per_doc | 18.2 | 19.2 | 15.0 | 16.8 | 17.8 |
| docs_per_sec | 39869.8 | 37449.1 | 37854.7 | 41445.7 | 31300.8 |

### corpus_bangla

| Metric | BanglaBERT | BanglaGamba | GPT-2 | NLLB-200 | mBART-50 |
|---|---|---|---|---|---|
| fertility | 2.0 | 1.356 | 12.934 | 2.113 | 2.083 |
| compression | 3.29 | 4.86 | 0.51 | 3.12 | 3.16 |
| unk_rate_pct | 2.3137 | 2.126 | 0.0 | 0.5165 | 0.0007 |
| avg_tokens_per_doc | 659.8 | 447.4 | 4267.4 | 697.3 | 687.2 |
| docs_per_sec | 1305.0 | 1216.2 | 653.3 | 1621.4 | 1351.7 |

### corpus_english

| Metric | BanglaBERT | BanglaGamba | GPT-2 | NLLB-200 | mBART-50 |
|---|---|---|---|---|---|
| fertility | 1.206 | 1.458 | 1.342 | 1.471 | 1.465 |
| compression | 5.11 | 4.23 | 4.59 | 4.19 | 4.21 |
| unk_rate_pct | 81.2349 | 1.8284 | 0.0 | 0.9303 | 0.0012 |
| avg_tokens_per_doc | 903.7 | 1091.9 | 1005.4 | 1101.7 | 1097.6 |
| docs_per_sec | 826.6 | 1049.1 | 857.7 | 928.3 | 693.8 |
