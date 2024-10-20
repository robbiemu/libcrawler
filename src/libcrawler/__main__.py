import argparse
import json
from urllib.parse import urljoin

from .libcrawler import crawl_and_convert
from libcrawler.version import __version__


def main():
    parser = argparse.ArgumentParser(description=f'Crawl documentation and convert to Markdown. v{__version__}')
    parser.add_argument('base_url', help='The base URL of the documentation site.')
    parser.add_argument('starting_point', help='The starting path of the documentation.')
    parser.add_argument('-o', '--output', default='documentation.md',
                        help='Output filename (default: documentation.md).')
    parser.add_argument('--no-robots', action='store_true',
                        help='Ignore robots.txt rules.')
    parser.add_argument('--delay', type=float, default=1.0,
                        help='Delay between requests in seconds.')
    parser.add_argument('--delay-range', type=float, default=0.5,
                        help='Range for random delay variation.')
    parser.add_argument('--remove-selectors', nargs='*',
                        help='Additional CSS selectors to remove from pages.')
    parser.add_argument('--similarity-threshold', type=float, default=0.6,
                        help='Similarity threshold for section comparison (default: 0.6).')
    parser.add_argument('--allowed-paths', nargs='*', 
                        help='List of URL paths to include during crawling.')
    parser.add_argument('--ignore-paths', nargs='*',
                        help='List of URL paths to exclude from crawling.')

    parser.add_argument('--user-agent', type=str, help='Custom User-Agent string.')
    headers_group = parser.add_mutually_exclusive_group()
    headers_group.add_argument('--headers-file', type=str, 
                               help='Path to a JSON file containing headers.')
    headers_group.add_argument('--headers-json', type=json.loads,
                               help='Raw JSON string representing the headers.')

    args = parser.parse_args()

    # Adjust logic for handling headers
    headers = None
    if args.headers_file:
        try:
            with open(args.headers_file, 'r') as file:
                headers = json.load(file)
        except (json.JSONDecodeError, FileNotFoundError) as e:
            print(f"Error loading headers from file: {e}")
            return
    elif args.headers_json:
        try:
            headers = args.headers_json
        except json.JSONDecodeError as e:
            print(f"Invalid JSON format for --headers-json: {e}")
            return

    start_url = urljoin(args.base_url, args.starting_point)

    # Adjust crawl_and_convert call to handle ignore-paths and optional headers
    crawl_and_convert(
        start_url=start_url,
        base_url=args.base_url,
        output_filename=args.output,
        user_agent=args.user_agent if hasattr(args, 'user_agent') else '*',
        handle_robots_txt=not args.no_robots,
        headers=headers,
        delay=args.delay,
        delay_range=args.delay_range,
        extra_remove_selectors=args.remove_selectors,
        similarity_threshold=args.similarity_threshold,
        allowed_paths=args.allowed_paths,
        ignore_paths=args.ignore_paths  # Pass the ignore-paths argument
    )


if __name__ == '__main__':
    main()