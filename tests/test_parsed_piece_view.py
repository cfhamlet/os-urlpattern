from os_urlpattern.parsed_piece_view import (FuzzyView, LastDotSplitFuzzyView,
                                             LengthView, MixedView, MultiView,
                                             PieceView, view_cls_from_pattern)
from os_urlpattern.pattern import Pattern


def test_view_cls_from_pattern():
    data = [
        ('abc', PieceView, False),
        ('[a-z]{2}', LengthView, False),
        ('[a-z]+', FuzzyView, False),
        ('abc[A-Z]{2}', MultiView, False),
        ('[A-Za-z]{3}123', MixedView, False),
        ('[A-Za-z]+[\\.]html', LastDotSplitFuzzyView, True),
        ('id[_][0-9A-Za-z]+[\.][a-z]+', MixedView, True),
    ]

    for p_str, view_cls, is_last_path in data:
        assert view_cls_from_pattern(Pattern(p_str), is_last_path) == view_cls
