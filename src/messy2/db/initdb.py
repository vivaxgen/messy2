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

    institution_payloads = await normalize_institution_payload(
        getattr(seed, "INSTITUTIONS", [])
    )
    institutions = await ensure_institutions(institution_payloads)
    result_dict["institutions"] = institutions

    project_payloads = await normalize_project_payload(getattr(seed, "PROJECTS", []))
    projects = await ensure_projects(project_payloads)
    result_dict["projects"] = projects

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


async def normalize_institution_payload(payloads: list[Any]) -> list[dict[str, Any]]:
    """
    Normalizes institution payloads to ensure they conform to the expected format.

    Args:
        payloads (list[Any]): A list of institution payloads to normalize.

    Returns:
        list[dict[str, Any]]: A list of normalized institution payloads.
    """

    normalized_payloads = []
    for payload in payloads:
        if isinstance(payload, dict):
            normalized_payloads.append(payload)
        else:
            logger.warning(f"Skipping invalid institution payload: {payload}")
    return normalized_payloads


async def ensure_institutions(payloads: list[dict[str, Any]]) -> int:
    """
    Ensures that institutions exist in the database based on the provided payloads.

    Args:
        payloads (list[dict[str, Any]]): A list of institution payloads to ensure.
    Returns:
        int: The number of institution records that were ensured in the database.
    """

    dbh = get_handler()
    assert dbh is not None, "Database handler is not initialized"

    counter = 0
    dbh = get_handler()
    for payload in payloads:
        institution = await dbh.service.Institution.upsert_from_dict(payload, "code")
        logger.info(f"Ensured Institution with code '{institution.code}'")
        counter += 1

    return counter


async def normalize_project_payload(payloads: list[Any]) -> list[dict[str, Any]]:
    """
    Normalizes project payloads to ensure they conform to the expected format.

    Args:
        payloads (list[Any]): A list of project payloads to normalize.

    Returns:
        list[dict[str, Any]]: A list of normalized project payloads.
    """

    normalized_payloads = []
    for payload in payloads:
        if isinstance(payload, dict):
            normalized_payloads.append(payload)
        else:
            logger.warning(f"Skipping invalid project payload: {payload}")
    return normalized_payloads


async def ensure_projects(payloads: list[dict[str, Any]]) -> int:
    """
    Ensures that projects exist in the database based on the provided payloads.

    Args:
        payloads (list[dict[str, Any]]): A list of project payloads to ensure.

    Returns:
        int: The number of project records that were ensured in the database.
    """

    dbh = get_handler()
    assert dbh is not None, "Database handler is not initialized"

    counter = 0
    for payload in payloads:
        project = await dbh.service.Project.upsert_from_dict(payload, "code")
        logger.info(
            f"Ensured Project with code '{project.code}' owned by group: {project.group}"
        )
        counter += 1

    return counter


# EOF
