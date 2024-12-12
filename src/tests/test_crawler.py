import asyncio
from bs4 import BeautifulSoup
import os
import logging
from playwright.async_api import async_playwright
import unittest
from unittest.mock import patch, AsyncMock, Mock
from urllib.parse import urljoin

__package__ = ''

from src.libcrawler.libcrawler import \
    build_tree, common_selectors, crawl_and_convert, deduplicate_content, \
    fetch_content, get_links, is_allowed_by_robots, normalize_url, \
    remove_common_elements, traverse_and_build_markdown


# Disable logging during tests
logging.disable(logging.CRITICAL)


class TestFetchContent(unittest.TestCase):

    @patch('src.libcrawler.libcrawler.async_playwright')
    def test_fetch_content_success(self, mock_playwright):
        # Mock the async_playwright context
        mock_playwright_instance = AsyncMock()
        mock_browser = AsyncMock()
        mock_context = AsyncMock()
        mock_page = AsyncMock()

        # Configure the mock chain
        mock_playwright.return_value.__aenter__.return_value = mock_playwright_instance
        mock_playwright_instance.chromium.launch.return_value = mock_browser
        mock_browser.new_context.return_value = mock_context
        mock_context.new_page.return_value = mock_page

        # Mock page content and URL
        mock_page.content.return_value = '<html><body>Test content</body></html>'
        mock_page.url = 'http://example.com/test'

        # Run the fetch_content function asynchronously
        content, url = asyncio.run(fetch_content('http://example.com/test'))

        # Assertions to verify the Playwright API calls
        mock_playwright_instance.chromium.launch.assert_awaited_once()
        mock_browser.new_context.assert_awaited_once_with(user_agent=None, extra_http_headers={})
        mock_context.new_page.assert_awaited_once()
        mock_page.goto.assert_awaited_once_with('http://example.com/test', wait_until='domcontentloaded')
        mock_page.content.assert_awaited_once()

        # Assertions for the function output
        self.assertEqual(content, '<html><body>Test content</body></html>')
        self.assertEqual(url, 'http://example.com/test')

    @patch('src.libcrawler.libcrawler.async_playwright')
    def test_fetch_content_with_headers(self, mock_playwright):
        # Mock the async_playwright context
        mock_playwright_instance = AsyncMock()
        mock_browser = AsyncMock()
        mock_context = AsyncMock()
        mock_page = AsyncMock()

        # Configure the mock chain
        mock_playwright.return_value.__aenter__.return_value = mock_playwright_instance
        mock_playwright_instance.chromium.launch.return_value = mock_browser
        mock_browser.new_context.return_value = mock_context
        mock_context.new_page.return_value = mock_page

        # Mock page content and URL
        mock_page.content.return_value = '<html><body>Test content with headers</body></html>'
        mock_page.url = 'http://example.com/test'

        # Define headers
        headers = {'User-Agent': 'test-agent'}

        # Run the fetch_content function asynchronously
        content, url = asyncio.run(fetch_content('http://example.com/test', headers=headers))

        # Assertions to verify the Playwright API calls
        mock_playwright_instance.chromium.launch.assert_awaited_once()
        mock_browser.new_context.assert_awaited_once_with(user_agent=None, extra_http_headers=headers)
        mock_context.new_page.assert_awaited_once()
        mock_page.goto.assert_awaited_once_with('http://example.com/test', wait_until='domcontentloaded')
        mock_page.content.assert_awaited_once()

        # Assertions for the function output
        self.assertEqual(content, '<html><body>Test content with headers</body></html>')
        self.assertEqual(url, 'http://example.com/test')

    @patch('src.libcrawler.libcrawler.async_playwright')
    def test_fetch_content_failure(self, mock_playwright):
        # Mock the async_playwright context
        mock_playwright_instance = AsyncMock()
        mock_browser = AsyncMock()
        mock_context = AsyncMock()
        mock_page = AsyncMock()

        # Configure the mock chain
        mock_playwright.return_value.__aenter__.return_value = mock_playwright_instance
        mock_playwright_instance.chromium.launch.return_value = mock_browser
        mock_browser.new_context.return_value = mock_context
        mock_context.new_page.return_value = mock_page

        # Simulate a failure
        mock_page.goto.side_effect = Exception('Error')

        # Run the fetch_content function asynchronously
        content, url = asyncio.run(fetch_content('http://example.com/test'))

        # Assertions for the function output
        self.assertIsNone(content)
        self.assertIsNone(url)

    @patch('src.libcrawler.libcrawler.async_playwright')
    def test_user_agent_harmonization(self, mock_playwright):
        # Mock the async_playwright context
        mock_playwright_instance = AsyncMock()
        mock_browser = AsyncMock()
        mock_context = AsyncMock()
        mock_page = AsyncMock()

        # Configure the mock chain
        mock_playwright.return_value.__aenter__.return_value = mock_playwright_instance
        mock_playwright_instance.chromium.launch.return_value = mock_browser
        mock_browser.new_context.return_value = mock_context
        mock_context.new_page.return_value = mock_page

        # Mock page content and URL
        mock_page.content.return_value = '<html><body>Test content with headers and user-agent</body></html>'
        mock_page.url = 'http://example.com/test'

        # Headers without user-agent
        headers = {'Accept': 'text/html'}
        user_agent = 'test-agent'

        # Run the fetch_content function asynchronously
        content, url = asyncio.run(fetch_content('http://example.com/test', user_agent=user_agent, headers=headers))

        # Assertions to verify the Playwright API calls
        mock_playwright_instance.chromium.launch.assert_awaited_once()
        mock_browser.new_context.assert_awaited_once_with(user_agent=user_agent, extra_http_headers=headers)
        mock_context.new_page.assert_awaited_once()
        mock_page.goto.assert_awaited_once_with('http://example.com/test', wait_until='domcontentloaded')
        mock_page.content.assert_awaited_once()

        # Assertions for the function output
        self.assertEqual(content, '<html><body>Test content with headers and user-agent</body></html>')
        self.assertEqual(url, 'http://example.com/test')


class TestIgnorePaths(unittest.TestCase):
    def setUp(self):
        self.start_url = 'http://example.com/start'
        self.base_url = 'http://example.com'
        # The ignore_paths can now contain partial matches
        self.ignore_paths = ['/ignore-me', '/skip-this']

@patch('src.libcrawler.libcrawler.fetch_content')
def test_ignore_paths_pre_and_post_fetch(self, mock_fetch_content):
    # Mock the fetch_content to simulate redirects and actual content
    mock_fetch_content.side_effect = [
        ('<html><body>Start Page</body></html>', 'http://example.com/start'),  # First URL
        ('<html><body>Ignored Page</body></html>', 'http://example.com/ignore-me/page'),  # Ignored after redirect
        ('<html><body>Another Ignored Page</body></html>', 'http://example.com/skip-this/page2'),  # Ignored after redirect
        ('<html><body>Allowed Page</body></html>', 'http://example.com/allowed-page')  # Not ignored
    ]

    # Run the build_tree function
    result_tree = build_tree(
        start_url=self.start_url,
        base_url=self.base_url,
        ignore_paths=self.ignore_paths
    )

    # Check that the first URL (pre-fetch) was skipped entirely
    self.assertEqual(mock_fetch_content.call_count, 3)

    # Check that the ignored URLs are not in the result tree (post-fetch)
    for node in result_tree.values():
        self.assertNotIn('http://example.com/ignore-me/page', node.url)
        self.assertNotIn('http://example.com/skip-this/page2', node.url)

    # Check that non-ignored URLs are present in the result tree
    self.assertIn('http://example.com/start', result_tree)
    self.assertIn('http://example.com/allowed-page', [node.url for node in result_tree.values()])

class TestGetLinks(unittest.TestCase):
    def test_get_links_all_paths(self):
        html = '''
        <a href="/page1">Page 1</a>
        <a href="http://example.com/page2">Page 2</a>
        <a href="http://otherdomain.com/page3">Page 3</a>
        '''
        base_url = 'http://example.com'
        links = get_links(html, base_url)
        expected_links = {
            'http://example.com/page1',
            'http://example.com/page2',
        }
        self.assertEqual(links, expected_links)

    def test_get_links_with_allowed_paths(self):
        html = '''
        <a href="/docs/page1">Docs Page 1</a>
        <a href="/api/page2">API Page 2</a>
        <a href="/about">About</a>
        '''
        base_url = 'http://example.com'
        allowed_paths = ['/docs/', '/api/']
        links = get_links(html, base_url, allowed_paths=allowed_paths)
        expected_links = {
            'http://example.com/docs/page1',
            'http://example.com/api/page2',
        }
        self.assertEqual(links, expected_links)

    def test_get_links_with_index_html(self):
        html = '''
        <a href="/docs/">Docs Home</a>
        <a href="/docs/index.html">Docs Index</a>
        <a href="/api/index.html">API Index</a>
        <a href="/api/">API Home</a>
        '''
        base_url = 'http://example.com'
        allowed_paths = ['/docs', '/api']
        links = get_links(html, base_url, allowed_paths=allowed_paths)
        expected_links = {
            'http://example.com/docs',
            'http://example.com/api',
        }
        self.assertEqual(links, expected_links)

    def test_get_links_disallowed_similar_paths(self):
        html = '''
        <a href="/langgraph/page1">Langgraph Page 1</a>
        <a href="/langgraphjs/page2">LanggraphJS Page 2</a>
        <a href="/langgraph-tools/page3">Langgraph Tools Page 3</a>
        <a href="/langgraph">Langgraph Home</a>
        <a href="/langgraphjavascript">Langgraph JavaScript</a>
        '''
        base_url = 'http://example.com'
        allowed_paths = ['/langgraph/']
        links = get_links(html, base_url, allowed_paths=allowed_paths)
        expected_links = {
            'http://example.com/langgraph/page1',
            'http://example.com/langgraph',  # Include the exact path
        }
        self.assertEqual(links, expected_links)

class TestIsAllowedByRobots(unittest.TestCase):
    def test_is_allowed_by_robots(self):
        robots_parser = Mock()
        robots_parser.can_fetch.return_value = True
        url = 'http://example.com/page'
        self.assertTrue(is_allowed_by_robots(url, robots_parser=robots_parser))
        robots_parser.can_fetch.assert_called_with('*', '/page')

    def test_is_disallowed_by_robots(self):
        robots_parser = Mock()
        robots_parser.can_fetch.return_value = False
        url = 'http://example.com/secret'
        self.assertFalse(is_allowed_by_robots(url, robots_parser=robots_parser))
        robots_parser.can_fetch.assert_called_with('*', '/secret')

class TestRemoveCommonElements(unittest.TestCase):
    def test_remove_common_elements(self):
        html = '''
        <html>
            <body>
                <header>Header</header>
                <nav>Navigation</nav>
                <section>
                    <header>Section header</header>
                Main content
                </section>
                <footer>Footer</footer>
            </body>
        </html>
        '''
        soup = BeautifulSoup(html, 'html.parser')
        soup = remove_common_elements(soup, extra_remove_selectors=common_selectors)
        result = str(soup)
        self.assertNotIn('Header', result)
        self.assertNotIn('Navigation', result)
        self.assertNotIn('Footer', result)
        self.assertIn('Main content', result)

    def test_remove_common_elements_with_extra_selectors(self):
        html = '''
        <html>
            <body>
                <header>Header</header>
                <div class="ad">Ad Content</div>
                <div>Main content</div>
                <footer>Footer</footer>
            </body>
        </html>
        '''
        soup = BeautifulSoup(html, 'html.parser')
        soup = remove_common_elements(soup, extra_remove_selectors=['header', 'footer', '.ad'])
        result = str(soup)
        self.assertNotIn('Header', result)
        self.assertNotIn('Ad Content', result)
        self.assertNotIn('Footer', result)
        self.assertIn('Main content', result)

class TestBuildTree(unittest.TestCase):
    @patch('src.libcrawler.libcrawler.fetch_content')
    def test_build_tree(self, mock_fetch_content):
        # Mock fetch_content to return predefined HTML content
        def side_effect(url, headers={}, interval=None):
            if url == 'http://example.com/start':
                html = '''
                <html>
                    <body>
                        <div>Start Page Content</div>
                        <a href="/page1">Page 1</a>
                    </body>
                </html>
                '''
                return html, url
            elif url == 'http://example.com/page1':
                html = '''
                <html>
                    <body>
                        <div>Page 1 Content</div>
                        <a href="/start">Start Page</a>
                    </body>
                </html>
                '''
                return html, url
            else:
                return '', url

        mock_fetch_content.side_effect = side_effect

        # Run build_tree
        page_markdowns, _url_to_anchor = asyncio.run(build_tree(
            start_url='http://example.com/start',
            base_url='http://example.com',
            handle_robots_txt=False,
            delay=0,
            delay_range=0,
            allowed_paths=None,
            headers={}
        ))

        # Check that page_markdowns contains two entries
        self.assertIn('http://example.com/start', page_markdowns)
        self.assertIn('http://example.com/page1', page_markdowns)

        # Check content
        self.assertIn('Start Page Content', page_markdowns['http://example.com/start'])
        self.assertIn('Page 1 Content', page_markdowns['http://example.com/page1'])

    @patch('src.libcrawler.libcrawler.fetch_content')
    def test_build_tree_with_headers(self, mock_fetch_content):
        # Mock fetch_content to return predefined HTML content
        def side_effect(url, headers={}, interval=None):
            if url == 'http://example.com/start':
                html = '''
                <html>
                    <body>
                        <div>Start Page Content</div>
                        <a href="/page1">Page 1</a>
                    </body>
                </html>
                '''
                return html, url
            elif url == 'http://example.com/page1':
                html = '''
                <html>
                    <body>
                        <div>Page 1 Content</div>
                        <a href="/start">Start Page</a>
                    </body>
                </html>
                '''
                return html, url
            else:
                return '', url

        mock_fetch_content.side_effect = side_effect

        headers = {'User-Agent': 'test-agent'}

        # Run build_tree with headers
        _page_markdowns, _url_to_anchor = asyncio.run(build_tree(
            start_url='http://example.com/start',
            base_url='http://example.com',
            handle_robots_txt=False,
            delay=0,
            delay_range=0,
            allowed_paths=None,
            headers=headers
        ))

        # Check that fetch_content was called with correct headers
        calls = mock_fetch_content.call_args_list
        for call in calls:
            _args, kwargs = call
            # fetch_content(url, headers={})
            self.assertIn('headers', kwargs)
            self.assertEqual(kwargs['headers'], headers)

class TestDeduplicateContent(unittest.TestCase):
    def test_deduplicate_content_no_common(self):
        page_markdowns = {
            'http://example.com/start': 'Start Page Content\n\nUnique to Start',
            'http://example.com/page1': 'Page 1 Content\n\nUnique to Page1',
            'http://example.com/page2': 'Page 2 Content\n\nUnique to Page2',
        }
        unique_content, common_content = deduplicate_content(
            page_markdowns, similarity_threshold=0.99, min_block_length=20
        )

        # No common content expected
        self.assertEqual(len(common_content), 0)

        # All unique content should be present
        self.assertEqual(unique_content['http://example.com/start'], ['Start Page Content', 'Unique to Start'])
        self.assertEqual(unique_content['http://example.com/page1'], ['Page 1 Content', 'Unique to Page1'])
        self.assertEqual(unique_content['http://example.com/page2'], ['Page 2 Content', 'Unique to Page2'])

    def test_deduplicate_content_with_common(self):
        page_markdowns = {
            'http://example.com/start': 'Common Content\n\nStart Page Content',
            'http://example.com/page1': 'Common Content\n\nPage 1 Content',
            'http://example.com/page2': 'Common Content\n\nPage 2 Content',
        }
        unique_content, common_content = deduplicate_content(
            page_markdowns, similarity_threshold=0.99, min_block_length=20
        )

        # Common content should have 'Common Content'
        self.assertIn('Common Content', common_content)

        # Unique content should exclude 'Common Content'
        self.assertEqual(unique_content['http://example.com/start'], ['Start Page Content'])
        self.assertEqual(unique_content['http://example.com/page1'], ['Page 1 Content'])
        self.assertEqual(unique_content['http://example.com/page2'], ['Page 2 Content'])

class TestTraverseAndBuildMarkdown(unittest.TestCase):
    def test_traverse_and_build_markdown(self):
        unique_content = {
            'http://example.com/start': ['Start Page Content'],
            'http://example.com/page1': ['Page 1 Content'],
            'http://example.com/page2': ['Page 2 Content'],
        }
        common_content = ['Common Content']
        url_to_anchor = {
            'http://example.com/start': 'start',
            'http://example.com/page1': 'page1',
            'http://example.com/page2': 'page2',
        }
        final_markdown = traverse_and_build_markdown(unique_content, common_content, url_to_anchor)

        # Check that anchors are correctly added
        self.assertIn('<a id="start">http://example.com/start</a>', final_markdown)
        self.assertIn('<a id="page1">http://example.com/page1</a>', final_markdown)
        self.assertIn('<a id="page2">http://example.com/page2</a>', final_markdown)

        # Check that unique content is present
        self.assertIn('Start Page Content', final_markdown)
        self.assertIn('Page 1 Content', final_markdown)
        self.assertIn('Page 2 Content', final_markdown)

        # Check that common sections are added at the end
        self.assertIn('# Common Sections', final_markdown)
        self.assertIn('Common Content', final_markdown)

class TestCrawlAndConvert(unittest.TestCase):
    def setUp(self):
        # Set up parameters for testing
        self.base_url = 'http://example.com'
        self.starting_point = '/start'
        self.start_url = urljoin(self.base_url, self.starting_point)
        self.output_filename = 'test_output.md'

        # Mock HTML pages with links between them
        self.html_start = """
        <html>
            <body>
                <header><h1>pages</h1></header>
                <div>Common Content</div>
                <div>
                    <h2>Start Page</h2>
                    the Start Page content like a b and c
                </div>
                <h3>nav</h3>
                <ul>
                    <li><a id="start">Start Page</a></li>
                    <li><a id="page1" href="/page1">Page 1</a></li>
                    <li><a id="page2" href="/page2">Page 2</a></li>
                </ul>
            </body>
        </html>
        """

        self.html_page1 = """
        <html>
            <body>
                <div>Common Content</div>
                <div>
                <h2>Page 1</h2>
                <span>Only Page 1's content should appear here.</span>
                </div>
                <h3>nav</h3>
                <ul>
                    <li><a id="start" href="/start">Start Page</a></li>
                    <li><a id="page1">Page 1</a></li>
                    <li><a id="page2" href="/page2">Page 2</a></li>
                </ul>
            </body>
        </html>
        """

        self.html_page2 = """
        <html>
            <body>
                <div>Common Content</div>
                <div>
                <h2>Page 2</h2>
                <p>This is Page's 2 Content</p>
                <a id="page3" href="/page3.html">Page 3</a>
                </div>
                <h3>nav</h3>
                <ul>
                    <li><a id="start" href="/start">Start Page</a></li>
                    <li><a id="page1" href="/page1">Page 1</a></li>
                    <li><a id="page2">Page 2</a></li>
                </ul>
            </body>
        </html>
        """

        self.html_page3 = """
        <html>
            <body>
                <div>Common Content</div>
                <div>
                <h2>Page 3</h2>
                random pg 3 Content
                </div>
            </body>
        </html>
        """

    def tearDown(self):
        if os.path.exists(self.output_filename):
            os.remove(self.output_filename)

    @patch('src.libcrawler.libcrawler.fetch_content')
    def test_crawl_and_convert(self, mock_fetch_content):
        # Define side effect for fetch_content
        def side_effect(url, headers={}, interval=None):
            normalized_url = normalize_url(url)
            if normalized_url == normalize_url(self.start_url):
                return self.html_start, url
            elif normalized_url == normalize_url(urljoin(self.base_url, 'page1')):
                return self.html_page1, urljoin(self.base_url, 'page1')
            elif normalized_url == normalize_url(urljoin(self.base_url, 'page2')):
                return self.html_page2, urljoin(self.base_url, 'page2')
            elif normalized_url == normalize_url(urljoin(self.base_url, 'page3.html')):
                return self.html_page3, urljoin(self.base_url, 'page3.html')
            elif normalized_url == normalize_url(urljoin(self.base_url, 'index.html')):
                # index.html redirects to start
                return self.html_start, self.start_url
            else:
                return '', url

        mock_fetch_content.side_effect = side_effect

        headers = {'User-Agent': 'test-agent'}

        # Run the crawler with appropriate similarity threshold
        asyncio.run(
            crawl_and_convert(
                start_url=self.start_url,
                base_url=self.base_url,
                output_filename=self.output_filename,
                delay=0,
                delay_range=0,
                extra_remove_selectors=['header', 'footer', '.footer'],
                similarity_threshold=0.6,  # Increased threshold
                headers=headers
            )
        )

        # Check that fetch_content was called with headers
        calls = mock_fetch_content.call_args_list
        for call in calls:
            _args, kwargs = call
            self.assertIn('headers', kwargs)
            self.assertEqual(kwargs['headers'], headers)

        # Read the content
        with open(self.output_filename, 'r', encoding='utf-8') as f:
            content = f.read()

            # Check that common sections are included once at the end
            self.assertIn('# Common Sections', content)
            self.assertEqual(content.count('Common Content'), 1)  # Common content should appear once

            # Check that unique content is present
            self.assertIn('the Start Page content like a b and c', content)
            self.assertIn('Only Page 1\'s content should appear here.', content)
            self.assertIn('This is Page\'s 2 Content', content)
            self.assertIn('random pg 3 Content', content)

            # Check that internal links are adjusted to anchors
            self.assertIn('[Page 1](#page1)', content)
            self.assertIn('[Page 2](#page2)', content)

            # Ensure that common content is not duplicated
            occurrences = content.count('Common Content')
            self.assertEqual(occurrences, 1)

if __name__ == '__main__':
    unittest.main()
