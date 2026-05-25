from __future__ import annotations

from collections.abc import Awaitable, Callable

from litestar import Litestar
from litestar.plugins import InitPlugin
from litestar.config.app import AppConfig

from litestar_pulse.config.app import logger
from litestar_pulse.lib.app import init_app as lp_init_app
from litestar_pulse.db import set_handler_class


class Messy2Plugin(InitPlugin):
    def on_app_init(self, app_config: AppConfig) -> AppConfig:

        # import the handler
        from ..db.handler import MESSy2Handler

        # import the necessary controllers
        from ..registry import ROUTE_HANDLERS

        set_handler_class(MESSy2Handler)

        app_config.route_handlers.extend(ROUTE_HANDLERS)

        return app_config


def init_app() -> Litestar:

    logger.info("Initializing MESSy2 application...")

    return lp_init_app(
        lp_prefix="/_mgr",
        plugins=[Messy2Plugin()],
    )


# EOF
