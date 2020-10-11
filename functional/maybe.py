import typing as ty
from dataclasses import dataclass

T = ty.TypeVar('T')
U = ty.TypeVar('U')


@dataclass
class Maybe(ty.Generic[T]):
    def get(self):
        raise NotImplementedError

    def __rshift__(self, f: ty.Callable[[T], 'Maybe[U]']) -> 'Maybe[U]':
        return f(self.get()) if not self.__class__ == Nothing else Nothing()


@dataclass
class Nothing(Maybe[T]):
    def get(self):
        raise ValueError


@dataclass
class Just(Maybe[T]):
    value: T

    def get(self):
        return self.value


def sqrt(a: float) -> Maybe[float]:
    import math
    if a < 0:
        return Nothing()
    return Just[float](math.sqrt(a))


n: float = 2.0
sqrt2 = sqrt(2.0)
print(sqrt2)
sqrtsqrt2 = sqrt(2.0) >> sqrt

print(sqrtsqrt2)
print(sqrt(-1) >> sqrt)
