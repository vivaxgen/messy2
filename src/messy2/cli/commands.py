# SPDX-FileCopyrightText: 2026 Hidayat Trimarsanto <trimarsanto@gmail.com>
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

__copyright__ = "(C) 2026 Hidayat Trimarsanto <trimarsanto@gmail.com>"
__author__ = "trimarsanto@gmail.com"
__license__ = "MPL-2.0"

from litestar_pulse.cli.commands import NoReturn, pulsemgr, get_dbhandler

import click

pulsemgr.name = "messy2-cli"


@pulsemgr.command(name="institution-list")
async def institution_list():
    click.echo("Listing user domains...")

    async with get_dbhandler() as dbh:
        institutions = await dbh.repo.institution.list()
        for institution in institutions:
            click.echo(f"- {institution.name}")


@pulsemgr.command(name="institution-add")
async def institution_add():
    click.echo("Adding new institution...")


@pulsemgr.command(name="project-list")
async def project_list():
    pass


@pulsemgr.command(name="project-add")
async def project_add():
    pass


def main() -> NoReturn:
    """
    CLI entry point for pulsemgr standalone command
    """

    pulsemgr()


# EOF
