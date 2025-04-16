import typing as tp


T = tp.TypeVar("T")


class Singleton(type, tp.Generic[T]):
    _instances: dict[str, T] = {}

    def __call__(cls, *args: tp.Any, **kwargs: tp.Any) -> T:
        instance: T = super().__call__(*args, **kwargs)
        instance_key = f"{instance.__class__.__name__}_{getattr(instance, "instance_key", "main")}"  # noqa: E501
        if instance_key in cls._instances:
            return cls._instances[instance_key]

        cls._instances[instance_key] = instance
        return instance

    def get_all_instances(cls) -> tp.Generator[T, None, None]:
        for instance_key in cls._instances:
            class_name, _ = instance_key.split("_", 1)
            if class_name == cls.__name__:
                yield cls._instances[instance_key]
