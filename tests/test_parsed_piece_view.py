from os_urlpattern.parsed_piece_view import (BaseView, FuzzyView,
                                             LastDotSplitFuzzyView, LengthView,
                                             MixedView, PieceView,
                                             view_cls_from_pattern)
from os_urlpattern.pattern import Pattern


def test_view_cls_from_pattern():
    data = [
        ('abc', PieceView, False),
        ('[a-z]{2}', LengthView, False),
        ('[a-z]+', FuzzyView, False),
        ('abc[A-Z]{2}', BaseView, False),
        ('[A-Za-z]123', MixedView, False),
        ('[A-Za-z][\\.]html', LastDotSplitFuzzyView, True),
    ]

    for p_str, view_cls, is_last_path in data:
        assert view_cls_from_pattern(Pattern(p_str), is_last_path) == view_cls
