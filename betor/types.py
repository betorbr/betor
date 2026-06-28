from typing import (
    AsyncGenerator,
    Callable,
    Dict,
    List,
    Literal,
    Optional,
    Sequence,
    Tuple,
    TypeAlias,
    TypeVar,
    Union,
)

import motor.motor_asyncio

T = TypeVar("T")

CursorSort: TypeAlias = Union[str, Tuple[str, int]]

ApaginateParams: TypeAlias = Tuple[
    motor.motor_asyncio.AsyncIOMotorCollection,
    Optional[Dict],
    CursorSort,
    Callable[[Sequence[Dict]], Sequence[T]],
]

ApaginateAggregateParams: TypeAlias = Tuple[
    motor.motor_asyncio.AsyncIOMotorCollection,
    List[Dict],
    Callable[[Sequence[Dict]], Sequence[T]],
]

Languages: TypeAlias = List[str]

InsertOrUpdateResult: TypeAlias = Literal["inserted", "updated", "no_change"]

StrategyResult: TypeAlias = Tuple[float, Optional[str], Optional[str], Optional[T]]

StrategyGenerator: TypeAlias = AsyncGenerator[StrategyResult[T], None]

ScoreKey: TypeAlias = Tuple[str, Optional[T]]

Scores: TypeAlias = Dict[ScoreKey, float]
