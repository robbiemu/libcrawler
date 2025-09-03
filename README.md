# Documentation Crawler and Converter v1.0.3

This tool crawls a documentation website and converts the pages into a single Markdown document. It intelligently removes common sections that appear across multiple pages to avoid duplication, including them once at the end of the document.

**Version 1.0.0** introduces significant improvements, including support for JavaScript-rendered pages using Playwright and a fully asynchronous implementation.

## Features

- **JavaScript Rendering**: Utilizes Playwright to accurately render pages that rely on JavaScript, ensuring complete and up-to-date content capture.
- Crawls documentation websites and combines pages into a single Markdown file.
- Removes common sections that appear across many pages, including them once at the end of the document.
- Customizable threshold for similarity to control deduplication sensitivity.
- Configurable selectors to remove specific elements from pages.
- Supports robots.txt compliance with an option to ignore it.
  ## **NEW in v1.0.0**:
  - Javascript rendering, waiting for page to stabilize before scraping.
  - Asynchronous Operation: Fully asynchronous methods enhance performance and scalability during the crawling process.

## Installation

### Prerequisites

- **Python 3.7 or higher** is required.
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

### 4. Installing Playwright Browsers

After installing the package, you need to install the necessary Playwright browser binaries:

```bash
playwright install
```

This command downloads the required browser binaries (Chromium, Firefox, and WebKit) used by Playwright for rendering pages.

### 5. Installing from PyPI

Once the package is published on PyPI, you can install it directly using:

```bash
pip install libcrawler
```

### 6. Upgrading the Package

To upgrade the package to the latest version, use:

```bash
pip install --upgrade libcrawler
```

This will upgrade the package to the newest version available.

### 7. Verifying the Installation

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

- `BASE_URL`: The base URL of the documentation site (e.g., _https://example.com_).
- `STARTING_POINT`: The starting path of the documentation (e.g., /docs/).

### Optional Arguments

- `-o, --output OUTPUT`: Output filename (default: documentation.md).
- `--no-robots`: Ignore robots.txt rules.
- `--delay DELAY`: Delay between requests in seconds (default: 1.0).
- `--delay-range DELAY_RANGE`: Range for random delay variation (default: 0.5).
- `--remove-selectors SELECTOR [SELECTOR ...]`: Additional CSS selectors to remove from pages.
- `--similarity-threshold SIMILARITY_THRESHOLD`: Similarity threshold for section comparison (default: 0.8).
- `--allowed-paths PATH [PATH ...]`: List of URL paths to include during crawling.
- `--ignore-paths PATH [PATH ...]`: List of URL paths to skip during crawling, either before or after fetching content.
- `--user-agent USER_AGENT`: Specify a custom User-Agent string (which will be harmonized with any additional headers).
- `--headers-file FILE`: Path to a JSON file containing optional headers. Only one of `--headers-file` or `--headers-json` can be used.
- `--headers-json JSON` (JSON string): Optional headers as JSON.

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

#### Skipping URLs with Ignore Paths

```bash
crawl-docs https://example.com /docs/ -o output.md \
    --ignore-paths "/old/" "/legacy/"
```

## Dependencies

- **Python 3.7 or higher**
- [BeautifulSoup4](https://www.crummy.com/software/BeautifulSoup/bs4/doc/) for HTML parsing.
- [markdownify](https://github.com/matthewwithanm/python-markdownify) for converting HTML to Markdown.
- [Playwright](https://playwright.dev/python/docs/intro) for headless browser automation and JavaScript rendering.
- [aiofiles](https://github.com/Tinche/aiofiles) for asynchronous file operations.
- Additional dependencies are listed in `requirements.txt`.

### Installing Dependencies

After setting up your environment, install all required dependencies using:

```bash
pip install -r requirements.txt
```

**Note**: Ensure you have installed the Playwright browsers by running `playwright install` as mentioned in the Installation section.

## License

This project is licensed under the LGPLv3. See the [LICENSE]\(LICENSE) file for details.

## Contributing

Contributions are welcome! Please follow these steps to contribute:

1. **Fork the repository** on GitHub.
2. **Clone your fork** to your local machine:
   ```bash
   git clone https://github.com/your-username/libcrawler.git
   ```
3. **Create a new branch** for your feature or bugfix:
   ```bash
   git checkout -b feature-name
   ```
4. **Make your changes** and **commit** them with clear messages:
   ```bash
   git commit -m "Add feature X"
   ```
5. **Push** your changes to your fork:
   ```bash
   git push origin feature-name
   ```
6. **Open a Pull Request** on the original repository describing your changes.

Please ensure your code adheres to the project's coding standards and includes appropriate tests.

## Acknowledgements

- [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/bs4/doc/) for HTML parsing.
- [Playwright](https://playwright.dev/) for headless browser automation.
- [Markdownify](https://github.com/matthewwithanm/python-markdownify) for converting HTML to Markdown.
- [aiofiles](https://github.com/Tinche/aiofiles) for asynchronous file operations.
