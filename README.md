# Documentation Crawler and Converter v.0.3

This tool crawls a documentation website and converts the pages into a single Markdown document. It intelligently removes common sections that appear across multiple pages to avoid duplication, including them once at the end of the document.

## Features

- Crawls documentation websites and combines pages into a single Markdown file.
- Removes common sections that appear across many pages, including them once at the beginning.
- Customizable threshold for similarity.
- Configurable selectors to remove specific elements from pages.
- Supports robots.txt compliance with an option to ignore it.

## Installation

### Prerequisites

- **Python 3.6 or higher** is required.
- (Optional) It is recommended to use a virtual environment to avoid dependency conflicts with other projects.

### 1. Installing the Package with `pip`

If you have already cloned the repository or downloaded the source code, you can install the package using `pip`:

```bash
pip install .
```

This will install the package in your current Python environment.

### 2. Installing in Editable Mode

If you are a developer or want to modify the source code and see your changes reflected immediately, you can install the package in **editable** mode. This allows you to edit the source files and test the changes without needing to reinstall the package:

```bash
pip install -e .
```

### 3. Using a Virtual Environment (Recommended)

It is recommended to use a virtual environment to isolate the package and its dependencies. Follow these steps to set up a virtual environment and install the package:

1. **Create a virtual environment** (e.g., named `venv`):

   ```bash
   python -m venv venv
   ```

2. **Activate the virtual environment**:

   - On **macOS/Linux**:
     ```bash
     source venv/bin/activate
     ```

   - On **Windows**:
     ```bash
     .\venv\Scripts\activate
     ```

3. **Install the package** inside the virtual environment:

   ```bash
   pip install .
   ```

   This ensures that all dependencies are installed within the virtual environment.

### 4. Installing from PyPI

Once the package is published on PyPI, you can install it directly using:

```bash
pip install libcrawler
```

### 5. Upgrading the Package

To upgrade the package to the latest version, use:

```bash
pip install --upgrade libcrawler
```

This will upgrade the package to the newest version available.

### 6. Verifying the Installation

You can verify that the package has been installed correctly by running:

```bash
pip show libcrawler
```

This will display information about the installed package, including the version, location, and dependencies.

## Usage

```bash
crawl-docs BASE_URL STARTING_POINT [OPTIONS]
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
- `--headers-file FILE`: Path to a JSON file containing optional headers. Only one of `--headers-file` or `--headers-json` can be used.
- `--headers-json JSON` (JSON string): Optional headers as JSON

### Examples

#### Basic Usage
```bash
crawl-docs https://example.com /docs/ -o output.md
```

#### Adjusting Thresholds
```bash
crawl-docs https://example.com /docs/ -o output.md \
    --similarity-threshold 0.7 \
    --delay-range 0.3
```

#### Specifying Extra Selectors to Remove
```bash
crawl-docs https://example.com /docs/ -o output.md \
    --remove-selectors ".sidebar" ".ad-banner"
```

#### Limiting to Specific Paths
```bash
crawl-docs https://example.com / -o output.md \
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
