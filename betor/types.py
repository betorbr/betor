from typing import Callable, Dict, Optional, Sequence, Tuple, TypeAlias, TypeVar, Union

import motor.motor_asyncio

T = TypeVar("T")

CursorSort: TypeAlias = Union[str, Tuple[str, int]]

ApaginateParams: TypeAlias = Tuple[
    motor.motor_asyncio.AsyncIOMotorCollection,
    Optional[Dict],
    CursorSort,
    Callable[[Sequence[Dict]], Sequence[T]],
]
