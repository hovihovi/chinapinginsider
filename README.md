# 🏓 China Pinginsider

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
├── docs/          # Static site
│   ├── index.html    # Homepage
│   ├── about.html    # About page
│   ├── css/style.css # Styles
│   └── articles/     # Translated articles (EN/FR)
└── serve.sh          # Local preview server
```

## Workflow

1. Identify noteworthy stories from Chinese media
2. Analyse with DeepSeek Flash → article drafts
3. Build article HTML (EN/FR)
4. Validate locally
5. Push to GitHub
