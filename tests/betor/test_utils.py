import pytest

from betor.utils import jaccard_similarity


class TestJaccardSimilarity:
    @pytest.mark.parametrize(
        (
            "a",
            "b",
            "expected",
        ),
        [
            ("foo", "foo", 1.0),
            ("foo", "bar", 0.0),
            ("foo test", "foo foo", 0.5),
        ],
    )
    def test_expected(self, a: str, b: str, expected: float):
        assert jaccard_similarity(a, b) == expected
