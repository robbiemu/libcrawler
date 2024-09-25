# Documentation Crawler and Converter

This tool crawls a documentation website and converts the pages into a single Markdown document. It intelligently removes common sections that appear across multiple pages to avoid duplication, including them once at the beginning of the document.

## Features

- **Crawls documentation websites** and combines pages into a single Markdown file.
- **Removes common sections** that appear across many pages, including them once at the beginning.
- **Customizable thresholds** for section similarity and commonality.
- **Configurable selectors** to remove specific elements from pages.
- **Supports robots.txt compliance** with an option to ignore it.

## Usage

```bash
python crawler_cli.py BASE_URL STARTING_POINT [OPTIONS]
```

- `BASE_URL`: The base URL of the documentation site (e.g., `https://example.com`).
- `STARTING_POINT`: The starting path of the documentation (e.g., `/docs/`).

### Optional Arguments

- `-o`, `--output OUTPUT`: Output filename (default: `documentation.md`).
- `--no-robots`: Ignore `robots.txt` rules.
- `--delay DELAY`: Delay between requests in seconds (default: `1.0`).
- `--delay-range DELAY_RANGE`: Range for random delay variation (default: `0.5`).
- `--remove-selectors SELECTOR [SELECTOR ...]`: Additional CSS selectors to remove from pages.
- `--similarity-threshold SIMILARITY_THRESHOLD`: Similarity threshold for section comparison (default: `0.8`).
- `--common-section-threshold COMMON_SECTION_THRESHOLD`: Threshold for considering a section common (default: `0.5`).
- `--user-agent USER_AGENT`: User agent string to use for crawling (default: `"*"`).
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
    --common-section-threshold 0.4
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

#### Setting a Custom User Agent

```bash
python crawler_cli.py https://example.com /docs/ -o output.md \
    --user-agent "MyCrawler/1.0"
```

## How It Works

The crawler performs the following steps:

1. **Crawling Pages:** Starting from the `STARTING_POINT`, it follows links within the `BASE_URL` domain, optionally limited to `allowed_paths`.
2. **Removing Unwanted Elements:** It removes specified elements from each page, including headers, footers, and any additional selectors provided.
3. **Identifying Common Sections:**
   - Uses MinHashing and Locality Sensitive Hashing (LSH) to detect similar sections across pages.
   - Sections that appear in a proportion of pages greater than or equal to `common_section_threshold` are considered common.
4. **Collecting Common Sections:**
   - Collects one copy of each common section.
   - Removes common sections from individual pages.
5. **Generating the Markdown Document:**
   - Includes the common sections once at the beginning of the output file.
   - Appends the unique content from each page.

## Dependencies

- **Python 3.6 or higher**
- **BeautifulSoup4**
- **datasketch**
- **requests**
- **markdownify**

Install dependencies using:

```bash
pip install -r requirements.txt
```

## License

This project is licensed under the [LGPLv3](LICENSE).
