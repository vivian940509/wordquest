# Vocabulary Sources

`toeic_5000_zh.csv` is generated from two MIT-licensed sources:

- `ringooai/open-vocabularies` TOEIC Traditional Chinese CSV, used first for TOEIC-focused vocabulary.
- `dong706/ECDICT-english-words`, used to fill the remaining high-frequency English words with Chinese translations.

The app loads the compact generated CSV at runtime. Large source dictionaries are not required for normal app startup.
