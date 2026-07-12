from typing import TypeVar, cast

T = TypeVar("T")

def custom_check_runtime(singleton_variable: T | None, error_detail: str) -> T:
    if singleton_variable is None:
        raise RuntimeError(error_detail)
    return cast(T, singleton_variable)

def check_property_runtime(name:str, singleton_variable: T | None) -> T:
    error_detail = f"{name} runtime error. Check lifespan.py for proper initialization"
    return custom_check_runtime(singleton_variable=singleton_variable, error_detail=error_detail)