from typing import (
    TYPE_CHECKING,
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

if TYPE_CHECKING:
    from betor.adapters.determines_strategies.strategy import Strategy
    from betor.enums import ItemType


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

StrategyResult: TypeAlias = Tuple[
    "Strategy", float, Optional[str], Optional[str], Optional["ItemType"]
]

StrategyGenerator: TypeAlias = AsyncGenerator[StrategyResult, None]

ScoreKey: TypeAlias = Tuple[str, Optional["ItemType"]]

Scores: TypeAlias = Dict[ScoreKey, float]
