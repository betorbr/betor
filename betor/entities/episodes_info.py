from typing import List, TypedDict


class Episode(TypedDict):
    season: int
    episode: int


class EpisodesInfo(TypedDict):
    episodes: List[Episode]
