# Documentation Crawler and Converter v.0.2

This tool crawls a documentation website and converts the pages into a single Markdown document. It intelligently removes common sections that appear across multiple pages to avoid duplication, including them once at the beginning of the document.

## Features

- Crawls documentation websites and combines pages into a single Markdown file.
- Removes common sections that appear across many pages, including them once at the beginning.
- Customizable threshold for similarity.
- Configurable selectors to remove specific elements from pages.
- Supports robots.txt compliance with an option to ignore it.

## Usage

```bash
python crawler_cli.py BASE_URL STARTING_POINT [OPTIONS]
```

### Arguments

- `BASE_URL`: The base URL of the documentation site (e.g., https://example.com).
- `STARTING_POINT`: The starting path of the documentation (e.g., /docs/).

### Optional Arguments

- `-o, --output OUTPUT`: Output filename (default: documentation.md).
- `--no-robots`: Ignore robots.txt rules.
- `--delay DELAY`: Delay between requests in seconds (default: 1.0).
- `--delay-range DELAY_RANGE`: Range for random delay variation (default: 0.5).
- `--remove-selectors SELECTOR [SELECTOR ...]`: Additional CSS selectors to remove from pages.
- `--similarity-threshold SIMILARITY_THRESHOLD`: Similarity threshold for section comparison (default: 0.8).
- `--allowed-paths PATH [PATH ...]`: List of URL paths to include during crawling.

### Examples

#### Basic Usage
```bash
python crawler_cli.py https://example.com /docs/ -o output.md
```

#### Adjusting Thresholds
```bash
python crawler_cli.py https://example.com /docs/ -o output.md \
    --similarity-threshold 0.7 \
    --delay-range 0.3
```

#### Specifying Extra Selectors to Remove
```bash
python crawler_cli.py https://example.com /docs/ -o output.md \
    --remove-selectors ".sidebar" ".ad-banner"
```

#### Limiting to Specific Paths
```bash
python crawler_cli.py https://example.com / -o output.md \
    --allowed-paths "/docs/" "/api/"
```

### Dependencies

- Python 3.6 or higher
- BeautifulSoup4
- datasketch
- requests
- markdownify

Install dependencies using:
```bash
pip install -r requirements.txt
```

## License

This project is licensed under the LGPLv3.
