from __future__ import annotations

from litestar import Litestar

from .lib.app import init_app, Messy2Plugin


def app() -> Litestar:
    return init_app()


__all__ = ["app", "Messy2Plugin"]

# EOF
