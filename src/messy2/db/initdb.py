# SPDX-FileCopyrightText: 2026 Hidayat Trimarsanto <trimarsanto@gmail.com>
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

__copyright__ = "(C) 2026 Hidayat Trimarsanto <trimarsanto@gmail.com>"
__author__ = "trimarsanto@gmail.com"
__license__ = "MPL-2.0"

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from litestar_pulse.db import handler_factory
from litestar_pulse.db import initdb, get_handler
from litestar_pulse.lib.app import logger

from .handler import MESSy2Handler
from .fixtures import seed


async def initialize_seed(session: AsyncSession, result_dict: dict[str, Any]) -> bool:
    """
    Initializes the MESSy2 database with seed data.

    Args:
        session (AsyncSession): The database session to use for seeding.
        result_dict (dict[str, Any]): A dictionary to store the results of the seeding process.

    Returns:
        bool: True if seeding was successful, False otherwise.
    """

    logger.info("Initializing seed data...")
    dbh = handler_factory(session)
    assert dbh is not None, "Database handler is not initialized"

    # initialize additional EnumKeys and Groups from MESSy2 seed data
    ok = await initdb.initialize_lp_seed(session, result_dict, seed)
    if not ok:
        logger.error("Failed to seed MESSy2 database")
        return False

    # additional MESSy2 specific seeding can be added here if needed
    # site_payloads = await normalize_site_payload(getattr(seed, "SITES", []))
    # sites = await ensure_sites(site_payloads)
    # result_dict["sites"] = sites

    return True


async def initialize_database(initialize: bool = True) -> dict[str, int]:
    """
    Initializes the database by creating all tables and optionally seeding it with initial data.

    Args:
        initialize (bool): Whether to initialize the database with seed data. Defaults to True.

    Returns:
        dict[str, int]: A dictionary containing the count of records in each table after initialization.
    """

    initdb.add_initdb_function(initialize_seed)
    if initialize:
        return await initdb.initialize_database()
    return {}


# EPF
