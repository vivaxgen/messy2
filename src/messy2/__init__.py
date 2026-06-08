from __future__ import annotations

from litestar import Litestar


def app() -> Litestar:

    from .lib.app import init_app, Messy2Plugin

    return init_app()


__all__ = ["app"]

# EOF
