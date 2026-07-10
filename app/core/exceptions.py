from typing import TypeVar, cast

T = TypeVar("T")

def check_property_runtime(name:str, singleton_variable: T | None) -> T:
    if singleton_variable is None:
        raise RuntimeError(f"{name} runtime error. Check lifespan.py for proper initialization")
    return cast(T, singleton_variable)