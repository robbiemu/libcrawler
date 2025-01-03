"""
Crawl a webpage that represents API or library documentation and convert the whole chain of pages into a single large markdown document.
Pages that are not part of the library documentation are excluded.
"""

from .version import __version__

import aiofiles
from bs4 import BeautifulSoup
from collections import defaultdict
from difflib import SequenceMatcher
import logging
from markdownify import markdownify as md
from playwright.async_api import async_playwright
import random
import asyncio 
from urllib.parse import urljoin, urlparse, urlunparse
from urllib.robotparser import RobotFileParser


# Configure logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


common_selectors = ['header', 'footer', 'nav', '.nav', '.navbar', '.footer']


class PageNode:
    """Represents a page in the documentation tree."""

    def __init__(self, url):
        self.url = url
        self.children = []
        self.anchor_id = None

    def __repr__(self):
        from pprint import pformat
        return pformat(vars(self), indent=4, width=1)


def normalize_url(url):
    """Normalizes the URL by removing fragments, query parameters, and default filenames."""
    parsed_url = urlparse(url)
    path = parsed_url.path

    # Remove 'index.html' or 'index.htm' from the end of the path
    if path.endswith('/index.html') or path.endswith('/index.htm'):
        path = path[:-len('index.html')]
    # Remove trailing slashes
    path = path.rstrip('/')

    # Reconstruct the URL without fragment and query
    normalized_url = urlunparse((parsed_url.scheme, parsed_url.netloc, path, '', '', ''))
    return normalized_url


async def wait_for_stable_dom(page, timeout=10000, interval=None):
    """Waits for the DOM to stabilize using MutationObserver."""
    if interval is None:
        interval = 1000
    await page.evaluate(f"""
        new Promise(resolve => {{
            const observer = new MutationObserver((mutations, obs) => {{
                if (document.readyState === 'complete') {{
                    obs.disconnect(); // Stop observing
                    resolve();
                }}
            }});
            observer.observe(document.body, {{ childList: true, subtree: true }});
            setTimeout(resolve, {timeout}); // Fallback timeout
        }});
    """)
    await asyncio.sleep(interval / 1000)  # Allow additional time if necessary


async def fetch_content(url, user_agent=None, headers=None, interval=None):
    """Fetches HTML content from a URL using Playwright, following redirects."""
    if headers is None:
        headers = {}
    # Harmonize user-agent with headers
    if user_agent:
        headers['User-Agent'] = user_agent

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            context = await browser.new_context(user_agent=user_agent, extra_http_headers=headers)
            page = await context.new_page()
            await page.goto(url, wait_until='domcontentloaded')
            await wait_for_stable_dom(page, interval=interval)  # Wait for the DOM to stabilize
            content = await page.content()
            final_url = page.url
            await browser.close()
            return content, final_url
    except Exception as e:
        logger.error(f"Failed to fetch {url}: {e}")
        return None, None


def get_links(html, current_url, allowed_paths=None):
    """Extracts documentation links from HTML content."""
    soup = BeautifulSoup(html, 'html.parser')
    anchors = soup.find_all('a', href=True)
    current_netloc = urlparse(current_url).netloc
    links = set()

    # Do not normalize allowed paths (keep trailing slashes)
    if allowed_paths:
        allowed_paths = [path.rstrip('/') + '/' if not path.endswith('/') else path for path in allowed_paths]

    for a in anchors:
        href = a['href']
        full_url = urljoin(current_url, href)
        full_url = normalize_url(full_url)
        parsed_url = urlparse(full_url)

        if parsed_url.netloc != current_netloc:
            continue

        # Normalize parsed_url.path (remove trailing slash)
        normalized_path = parsed_url.path.rstrip('/')

        if allowed_paths:
            # Check for exact match or if the path starts with allowed path followed by '/'
            if not any(normalized_path == path.rstrip('/') or normalized_path.startswith(path.rstrip('/') + '/') for path in allowed_paths):
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


def remove_common_elements(soup, extra_remove_selectors=None):
    """Removes specified common elements."""
    if extra_remove_selectors is not None:
        selectors = extra_remove_selectors  # Use only extra_remove_selectors
    else:
        #selectors = ['header', 'footer', 'nav', '.nav', '.navbar', '.footer']
        selectors = []

    for selector in selectors:
        for element in soup.select(selector):
            element.decompose()
    return soup


async def build_tree(start_url, base_url, user_agent='*', handle_robots_txt=True, 
               headers=None, delay=1, delay_range=0.5, interval=None, 
               extra_remove_selectors=None, allowed_paths=None, ignore_paths=None):
    if headers is None:
        headers = {}
    visited_links = set()
    root = PageNode(start_url)
    node_lookup = {}
    normalized_start_url = normalize_url(start_url)
    node_lookup[normalized_start_url] = root
    queue = [root]

    robots_parser = load_robots_txt(base_url) if handle_robots_txt else None

    # Harmonize User-agent and Headers
    if user_agent:
        headers.setdefault('User-Agent', user_agent)

    # Store page content in Markdown
    page_markdowns = {}
    url_to_anchor = {}
    anchor_counter = 1

    while queue:
        current_node = queue.pop(0)
        current_link = normalize_url(current_node.url)

        if current_link in visited_links:
            continue
        visited_links.add(current_link)

        if ignore_paths is None:
            ignore_paths = []
        if any(ignore_path in current_link for ignore_path in ignore_paths):
            logger.info(f"Skipping {current_link} matching ignore_paths")
            continue  

        if handle_robots_txt and robots_parser:
            if not is_allowed_by_robots(current_link, user_agent, robots_parser):
                logger.info(f"Disallowed by robots.txt: {current_link}")
                continue

        logger.info(f'Processing {current_link}')
        page_content, page_url = await fetch_content(current_node.url, headers=headers, interval=interval)  
        if not page_content or (page_url and any(ignore_path in page_url for ignore_path in ignore_paths)):
            continue  

        soup = BeautifulSoup(page_content, 'html.parser')
        soup = remove_common_elements(soup, extra_remove_selectors=extra_remove_selectors)

        # Assign anchor ID
        parsed_url = urlparse(current_link)
        path = parsed_url.path.strip('/')
        anchor_name = path.replace('/', '_') or 'home'
        if anchor_name in url_to_anchor.values():
            anchor_name += f'_{anchor_counter}'
            anchor_counter += 1
        url_to_anchor[current_link] = anchor_name
        current_node.anchor_id = anchor_name

        # Adjust links in the HTML
        for a in soup.find_all('a', href=True):
            href = a['href']
            full_url = urljoin(current_node.url, href)
            normalized_full_url = normalize_url(full_url)
            if normalized_full_url in url_to_anchor:
                # Adjust link to point to anchor
                anchor = url_to_anchor[normalized_full_url]
                a['href'] = f'#{anchor}'
            else:
                # Ensure external links are absolute
                if not urlparse(href).netloc:
                    a['href'] = full_url

        # Convert to Markdown
        try:
            markdown_content = md(str(soup))
            page_markdowns[current_link] = markdown_content
        except Exception as e:
            logger.error(f"Failed to convert HTML to Markdown for {current_link}: {e}")

        # Extract and process child links
        child_links = get_links(str(soup), current_node.url, allowed_paths=allowed_paths)
        for link in child_links:
            normalized_link = normalize_url(link)
            if normalized_link not in node_lookup:
                child_node = PageNode(link)
                node_lookup[normalized_link] = child_node
            else:
                child_node = node_lookup[normalized_link]
            current_node.children.append(child_node)
            if normalized_link not in visited_links and child_node not in queue:
                queue.append(child_node)

        actual_delay = random.uniform(delay - delay_range, delay + delay_range)
        await asyncio.sleep(actual_delay)  # Replaced time.sleep with await asyncio.sleep

    for url, anchor in url_to_anchor.items():
        for key, content in page_markdowns.items():
            page_markdowns[key] = content.replace(url, f"#{anchor}")


    return page_markdowns, url_to_anchor


def deduplicate_content(page_markdowns, similarity_threshold=0.6, min_block_length=20):
    """
    Deduplicates content across multiple Markdown documents by identifying similar blocks of text.
    Returns the unique content and the common sections.
    """
    # Tokenize content into blocks (e.g., paragraphs)
    page_blocks = {}
    all_blocks = []
    block_to_id = {}
    id_counter = 0

    for url, content in page_markdowns.items():
        blocks = [block.strip() for block in content.split('\n\n') if block.strip()]
        page_blocks[url] = blocks
        for block in blocks:
            if block not in block_to_id:
                block_to_id[block] = id_counter
                all_blocks.append(block)
                id_counter += 1

    # Initialize Union-Find data structure
    parent = [i for i in range(id_counter)]  # parent[i] = i

    def find(u):
        while parent[u] != u:
            parent[u] = parent[parent[u]]  # Path compression
            u = parent[u]
        return u

    def union(u, v):
        u_root = find(u)
        v_root = find(v)
        if u_root != v_root:
            parent[v_root] = u_root

    # Compare blocks and union similar ones
    for i in range(len(all_blocks)):
        block_i = all_blocks[i]
        if len(block_i) < min_block_length:
            continue  # Skip blocks that are too short
        for j in range(i + 1, len(all_blocks)):
            block_j = all_blocks[j]
            if len(block_j) < min_block_length:
                continue  # Skip blocks that are too short
            # Compute similarity
            similarity = SequenceMatcher(None, block_i, block_j).ratio()
            if similarity >= similarity_threshold:
                id_i = block_to_id[block_i]
                id_j = block_to_id[block_j]
                union(id_i, id_j)


    # Build groups of similar blocks
    group_to_blocks = defaultdict(list)
    for block, idx in block_to_id.items():
        group_id = find(idx)
        group_to_blocks[group_id].append(block)

    # Identify common groups (blocks that appear in more than one page)
    block_occurrences = defaultdict(set)  # group_id -> set of URLs

    for url, blocks in page_blocks.items():
        for block in blocks:
            idx = block_to_id[block]
            group_id = find(idx)
            block_occurrences[group_id].add(url)

    # Identify common blocks
    common_groups = set()
    for group_id, urls in block_occurrences.items():
        if len(urls) > 1:
            common_groups.add(group_id)

    # Get representative block for each group
    group_representative = {}
    for group_id, blocks in group_to_blocks.items():
        # Choose the longest block as representative (or any heuristic)
        representative = max(blocks, key=len)
        group_representative[group_id] = representative

    # Remove common blocks from individual pages
    unique_content = {}
    for url, blocks in page_blocks.items():
        unique_blocks = []
        for block in blocks:
            idx = block_to_id[block]
            group_id = find(idx)
            if group_id not in common_groups:
                unique_blocks.append(block)
        unique_content[url] = unique_blocks

    # Collect common blocks (use representatives)
    common_blocks = [group_representative[group_id] for group_id in common_groups]

    return unique_content, common_blocks


def traverse_and_build_markdown(unique_content, common_content, url_to_anchor):
    """
    Constructs the final Markdown document by combining unique content and common sections.
    """
    final_markdown = ""

    # Build the content using the assigned anchors
    for url, blocks in unique_content.items():
        anchor = url_to_anchor.get(url, '')
        if anchor:
            final_markdown += f'# [Page] <a id="{anchor}">{url}</a>\n\n'
        final_markdown += '\n\n'.join(blocks)
        final_markdown += '\n\n'

    # Add common sections at the end
    if common_content:
        final_markdown += '# Common Sections\n\n'
        final_markdown += '\n\n'.join(common_content)
        final_markdown += '\n'

    return final_markdown


async def crawl_and_convert(
    start_url,
    base_url,
    output_filename,
    user_agent='*',
    handle_robots_txt=True,
    headers=None,
    delay=1,
    delay_range=0.5,
    interval=None,
    extra_remove_selectors=None,
    similarity_threshold=0.8,
    allowed_paths=None,
    ignore_paths=None
):
    # Build the tree and get page_markdowns and url_to_anchor
    page_markdowns, url_to_anchor = await build_tree(  
        start_url=start_url,
        base_url=base_url,
        user_agent=user_agent,
        handle_robots_txt=handle_robots_txt,
        headers=headers,
        delay=delay,
        delay_range=delay_range,
        interval=interval,
        extra_remove_selectors=extra_remove_selectors,
        allowed_paths=allowed_paths,
        ignore_paths=ignore_paths
    )

    # Deduplicate content
    unique_content, common_content = deduplicate_content(page_markdowns, similarity_threshold)

    # Build the final Markdown document
    final_markdown = traverse_and_build_markdown(unique_content, common_content, url_to_anchor)

    # Save to file
    async with aiofiles.open(output_filename, 'w', encoding='utf-8') as f:  # Use aiofiles for async file operations
        await f.write(final_markdown)
