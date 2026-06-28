# 🏓🐧 China Pinginsider

Chinese table tennis news, translated and analysed.

## Local Preview

```bash
./serve.sh
# Opens at http://localhost:8080
# Ctrl+C to stop
```

## Project Structure

```
chinapinginsider/
├── website/          # Static site
│   ├── index.html    # Homepage
│   ├── about.html    # About page
│   ├── css/style.css # Styles
│   └── articles/     # Translated articles (EN/FR/XHS)
├── scrapers/         # Python scraper pipeline
│   ├── sina.py       # Sina Sports scraper
│   ├── tencent.py    # Tencent News scraper
│   ├── correlator.py # Deduplication engine
│   └── orchestrator.py # Pipeline runner
└── serve.sh          # Local preview server
```

## Workflow

1. Scrape Chinese sources → raw JSON in `inbox/`
2. Analyse with DeepSeek Flash → article drafts
3. Build article HTML (EN/FR/XHS)
4. Hovi validates locally
5. Push to GitHub
