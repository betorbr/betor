from typing import List
from unittest import mock

import pytest

from betor.external_apis.imdb_suggestion_api import (
    IMDbSuggestionAPI,
    IMDbSuggestionResponse,
    IMDbSuggestionResponseLink,
    IMDbSuggestionResponseTitle,
)
from betor.types import ItemType


@pytest.fixture
def imdb_suggestion_api():
    return IMDbSuggestionAPI()


class TestDeterminesImdbId:
    @pytest.mark.parametrize(
        (
            "params",
            "execute_results",
            "expected",
        ),
        [
            [
                {"title": "Title"},
                [
                    IMDbSuggestionResponse(d=[], q="Title", v=1),
                ],
                None,
            ],
            [
                {"title": "Title"},
                [
                    IMDbSuggestionResponse(
                        d=[
                            IMDbSuggestionResponseTitle(
                                i=None,
                                id="tt12345678",
                                l="Title",
                                q="feature",
                                qid="movie",
                                rank=1,
                                s="...",
                                y=2025,
                            )
                        ],
                        q="Title",
                        v=1,
                    ),
                ],
                (
                    "tt12345678",
                    ItemType.movie,
                ),
            ],
            [
                {"title": "Title", "year": 2025},
                [
                    IMDbSuggestionResponse(d=[], q="Title 2025", v=1),
                    IMDbSuggestionResponse(
                        d=[
                            IMDbSuggestionResponseTitle(
                                i=None,
                                id="tt12345678",
                                l="Title",
                                q="feature",
                                qid="movie",
                                rank=1,
                                s="...",
                                y=2025,
                            )
                        ],
                        q="Title",
                        v=1,
                    ),
                ],
                (
                    "tt12345678",
                    ItemType.movie,
                ),
            ],
            [
                {"translated_title": "Título", "year": 2025},
                [
                    IMDbSuggestionResponse(
                        d=[
                            IMDbSuggestionResponseLink(
                                i=None, id="/path1", l="Link 1", s="Link One"
                            ),
                            IMDbSuggestionResponseTitle(
                                i=None,
                                id="tt12345678",
                                l="Title",
                                q="TV Series",
                                qid="tvSeries",
                                rank=1,
                                s="...",
                                y=2025,
                            ),
                        ],
                        q="Title 2025",
                        v=1,
                    ),
                ],
                (
                    "tt12345678",
                    ItemType.tv,
                ),
            ],
        ],
    )
    @pytest.mark.asyncio
    async def test_ok(
        self,
        params: dict,
        execute_results: List[IMDbSuggestionResponse],
        expected,
        imdb_suggestion_api: IMDbSuggestionAPI,
    ):
        with mock.patch.object(
            imdb_suggestion_api, "execute", side_effect=execute_results
        ):
            assert await imdb_suggestion_api.determines_imdb_id(**params) == expected
