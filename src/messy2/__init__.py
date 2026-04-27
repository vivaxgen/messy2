from __future__ import annotations


from litestar.plugins import InitPlugin
from litestar.config.app import AppConfig

from litestar_pulse.db import set_handler_class


class Messy2Plugin(InitPlugin):
    def on_app_init(self, app_config: AppConfig) -> AppConfig:

        # import the handler
        from .db.handler import MSY2Handler

        # import the necessary controllers
        from .registry import ROUTE_HANDLERS

        set_handler_class(MSY2Handler)

        app_config.route_handlers.extend(ROUTE_HANDLERS)


# EOF
