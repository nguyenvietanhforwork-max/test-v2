"""SQLAlchemy declarative base."""

from sqlalchemy.orm import DeclarativeBase, declared_attr


class Base(DeclarativeBase):
    @declared_attr.directive
    def __tablename__(cls) -> str:  # noqa: N805
        # CamelCase → snake_case
        out = []
        for i, ch in enumerate(cls.__name__):
            if i and ch.isupper():
                out.append("_")
            out.append(ch.lower())
        return "".join(out)
