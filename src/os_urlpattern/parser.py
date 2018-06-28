"""High-level APIs for parsing.
"""

from .parse_utils import fuzzy_digest as _fuzzy_digest
from .parse_utils import PieceParser, analyze_url, analyze_url_pattern_string


def parse(url_or_pattern):
    """Parse URL or URL pattern string.

    Args:
        url_or_pattern (str): URL or URL pattern.

    Returns:
        tuple: 2-tuples, (url_meta, parsed_pieces)
    """
    url_meta = None
    parsed_pieces = None
    if url_or_pattern.startswith(u'/'):  # URL pattern
        from .pattern_matcher import MatchPattern
        url_meta, pattern_strings = analyze_url_pattern_string(url_or_pattern)
        parsed_pieces = tuple([MatchPattern(p, i == url_meta.path_depth)
                               for i, p in enumerate(pattern_strings, 1)])
    else:  # URL
        parser = PieceParser()
        url_meta, pieces = analyze_url(url_or_pattern)
        parsed_pieces = tuple([parser.parse(piece) for piece in pieces])

    return url_meta, parsed_pieces


def fuzzy_digest(url_or_pattern):
    """Generate hex digest string from URL or URL pattern.

    Same fuzzy-digest same matcher.

    Args:
        url_or_pattern (str): URL or URL pattern.

    Returns:
        str: Digest value as a string of hexadecimal digits.
    """
    return _fuzzy_digest(*parse(url_or_pattern))
