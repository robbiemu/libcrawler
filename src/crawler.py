# crawler.py

"""
Crawl a webpage that represents API or library documentation and convert the whole chain of pages into a single large markdown document.
Pages that are not part of the library documentation are excluded.
"""

from bs4 import BeautifulSoup
from datasketch import MinHash, MinHashLSH
import logging
from markdownify import markdownify as md
import random
import requests
import time
from urllib.parse import urljoin, urlparse, urldefrag
from urllib.robotparser import RobotFileParser


# Configure logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


class PageNode:
    """Represents a page in the documentation tree."""

    def __init__(self, url):
        self.url = url
        self.content = ''
        self.children = []
        self.sections = []  # List of section elements

    def __repr__(self):
        from pprint import pformat
        return pformat(vars(self), indent=4, width=1)


def fetch_content(url):
    """Fetches HTML content from a URL, following redirects."""
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.text, response.url  # Return the final redirected URL
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch {url}: {e}")
        return None, None


def get_links(html, current_url, allowed_paths=None):
    """Extracts documentation links from HTML content."""
    soup = BeautifulSoup(html, 'html.parser')
    anchors = soup.find_all('a', href=True)
    current_netloc = urlparse(current_url).netloc
    links = set()

    # Normalize allowed paths (remove trailing slashes)
    if allowed_paths:
        allowed_paths = [path.rstrip('/') for path in allowed_paths]

    for a in anchors:
        href = a['href']
        full_url = urljoin(current_url, href)
        full_url, _ = urldefrag(full_url)
        parsed_url = urlparse(full_url)

        if parsed_url.netloc != current_netloc:
            continue

        # Normalize parsed_url.path (remove trailing slash)
        normalized_path = parsed_url.path.rstrip('/')

        # If allowed_paths is specified, only include paths that start with allowed_paths
        if allowed_paths:
            if not any(normalized_path.startswith(path) for path in allowed_paths):
                continue

        links.add(full_url)

    return links


def is_allowed_by_robots(url, user_agent='*', robots_parser=None):
    """Checks if the URL is allowed according to robots.txt."""
    if robots_parser is None:
        return True
    parsed_url = urlparse(url)
    path = parsed_url.path
    return robots_parser.can_fetch(user_agent, path)


def load_robots_txt(base_url):
    """Loads and parses the robots.txt file for the base URL."""
    parsed_base_url = urlparse(base_url)
    robots_url = f"{parsed_base_url.scheme}://{parsed_base_url.netloc}/robots.txt"
    robots_parser = RobotFileParser()
    robots_parser.set_url(robots_url)
    try:
        robots_parser.read()
    except Exception as e:
        logger.error(f"Failed to read robots.txt from {robots_url}: {e}")
        robots_parser = None
    return robots_parser


def remove_common_elements(soup, extra_selectors=None):
    """Removes specified common elements."""
    if extra_selectors is not None:
        selectors = extra_selectors  # Use only extra_selectors
    else:
        selectors = ['header', 'footer', 'nav', '.nav', '.navbar', '.footer']

    for selector in selectors:
        for element in soup.select(selector):
            element.decompose()
    return soup


def get_shingles(text, k=5):
    """Generates k-shingles from text."""
    words = text.split()
    shingles = set()
    for i in range(len(words) - k + 1):
        shingle = ' '.join(words[i:i + k])
        shingles.add(shingle)
    return shingles


def build_tree(start_url, base_url, user_agent='*', handle_robots_txt=True,
               delay=1, delay_range=0.5, extra_remove_selectors=None,
               similarity_threshold=0.8, common_section_threshold=0.5,
               allowed_paths=None):
    visited_links = set()
    root = PageNode(start_url)
    node_lookup = {start_url: root}
    queue = [root]

    robots_parser = load_robots_txt(base_url) if handle_robots_txt else None

    # LSH Index for sections
    lsh = MinHashLSH(threshold=similarity_threshold, num_perm=128)
    section_minhashes = {}  # Map section id to MinHash
    section_occurrences = {}  # Count how many times a section appears

    # Unique identifier for sections
    section_id_counter = 0

    page_nodes = []  # List to keep track of all page nodes

    while queue:
        current_node = queue.pop(0)
        current_link = current_node.url
        current_link, _ = urldefrag(current_link)
        if current_link in visited_links:
            continue
        visited_links.add(current_link)

        if handle_robots_txt and robots_parser:
            if not is_allowed_by_robots(current_link, user_agent, robots_parser):
                logger.info(f"Disallowed by robots.txt: {current_link}")
                continue

        logger.info(f'Processing {current_link}')
        page_content, page_url = fetch_content(current_link)
        if not page_content:
            continue  # Skip if content couldn't be fetched

        soup = BeautifulSoup(page_content, 'html.parser')
        soup = remove_common_elements(soup, extra_remove_selectors)

        # Extract sections (e.g., divs, sections, articles)
        sections = soup.find_all(['div', 'section', 'article', 'p', 'header', 'footer'])
        current_node.sections = sections
        page_nodes.append(current_node)

        for section in sections:
            text = section.get_text(separator=' ', strip=True)
            shingles = get_shingles(text)
            if not shingles:
                continue  # Skip empty sections

            m = MinHash(num_perm=128)
            for shingle in shingles:
                m.update(shingle.encode('utf-8'))

            section_id = str(section_id_counter)
            lsh.insert(section_id, m)
            section_minhashes[section_id] = m
            section_id_counter += 1

        # Extract and process child links
        child_links = get_links(str(soup), current_link, allowed_paths=allowed_paths)
        for link in child_links:
            if link not in node_lookup:
                child_node = PageNode(link)
                node_lookup[link] = child_node
            else:
                child_node = node_lookup[link]
            current_node.children.append(child_node)
            if link not in visited_links and child_node not in queue:
                queue.append(child_node)

        actual_delay = random.uniform(delay - delay_range, delay + delay_range)
        time.sleep(actual_delay)

    # Second pass: Identify common sections
    for section_id, m in section_minhashes.items():
        result = lsh.query(m)
        occurrence_count = len(result)
        section_occurrences[section_id] = occurrence_count

    total_pages = len(page_nodes)
    logger.info(f"Total pages processed: {total_pages}")

    # Determine threshold for common sections
    common_section_threshold_count = total_pages * common_section_threshold

    # Identify common sections
    common_sections = set()
    for section_id, count in section_occurrences.items():
        if count >= common_section_threshold_count:
            common_sections.add(section_id)

    # Prune common sections from pages and collect one copy of each common section
    common_sections_content = []
    collected_common_section_ids = set()

    for node in page_nodes:
        pruned_sections = []
        for section in node.sections:
            text = section.get_text(separator=' ', strip=True)
            shingles = get_shingles(text)
            if not shingles:
                continue

            m = MinHash(num_perm=128)
            for shingle in shingles:
                m.update(shingle.encode('utf-8'))
            result = lsh.query(m)
            is_common = False
            for res_id in result:
                if res_id in common_sections:
                    is_common = True
                    # Collect one copy if not already collected
                    if res_id not in collected_common_section_ids:
                        common_sections_content.append(section)
                        collected_common_section_ids.add(res_id)
                    break

            if not is_common:
                pruned_sections.append(section)

        node.sections = pruned_sections

    # Debugging: Check if common sections are collected
    print(f"Collected {len(common_sections_content)} common sections")

    return root, common_sections_content


def traverse_tree_and_write(node, file, visited=None):
    """Traverses the tree in depth-first order and writes content."""
    if visited is None:
        visited = set()

    if node.url in visited:
        return
    visited.add(node.url)

    if node.sections:
        # Combine the pruned sections back into HTML
        page_html = ''.join(str(section) for section in node.sections)
        # Convert to Markdown
        try:
            markdown_content = md(page_html)
            file.write(markdown_content + '\n\n')
        except Exception as e:
            logger.error(f"Failed to convert content to Markdown: {e}")
    for child in node.children:
        traverse_tree_and_write(child, file, visited)


def crawl_and_convert(start_url, base_url, output_filename,
                      user_agent='*', handle_robots_txt=True,
                      delay=1, delay_range=0.5, extra_remove_selectors=None,
                      similarity_threshold=0.8, common_section_threshold=0.5,
                      allowed_paths=None):
    """Main function to crawl and convert documentation to Markdown."""
    # Build the tree and identify common sections
    root, common_sections_content = build_tree(
        start_url, base_url, user_agent, handle_robots_txt,
        delay, delay_range, extra_remove_selectors,
        similarity_threshold, common_section_threshold,
        allowed_paths
    )

    # Debugging: Check if common sections are being written
    print(f"Writing {len(common_sections_content)} common sections to the output file")

    # Traverse the tree and write the content
    with open(output_filename, 'w', encoding='utf-8') as f:
        # Include common sections once at the beginning
        if common_sections_content:
            common_html = ''.join(str(section) for section in common_sections_content)
            try:
                markdown_content = md(common_html)
                f.write('# Common Sections\n\n')
                f.write(markdown_content + '\n\n')
            except Exception as e:
                logger.error(f"Failed to convert common sections to Markdown: {e}")
        traverse_tree_and_write(root, f)
