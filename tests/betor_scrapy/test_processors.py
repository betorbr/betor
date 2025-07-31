from typing import List

import pytest

from betor_scrapy.processors import Title


class TestTitle:
    @pytest.mark.parametrize(
        (
            "value",
            "expected",
        ),
        [
            (
                ["Rick and Morty"],
                "Rick and Morty",
            ),
            (
                [": Rick and Morty"],
                "Rick and Morty",
            ),
            (
                [" Rick and  Morty"],
                "Rick and Morty",
            ),
            (
                [" Rick and   Morty"],
                "Rick and Morty",
            ),
            (
                [" Rick and ", "Morty"],
                "Rick and Morty",
            ),
            (
                ["", " Rick and ", "Morty"],
                "Rick and Morty",
            ),
            (
                ["", " Rick and ", "Morty: ", " Starts"],
                "Rick and Morty: Starts",
            ),
        ],
    )
    def test_ok(self, value: List[str], expected: str):
        processor = Title()
        assert processor(value) == expected
