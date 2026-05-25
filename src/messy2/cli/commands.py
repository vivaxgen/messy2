# SPDX-FileCopyrightText: 2026 Hidayat Trimarsanto <trimarsanto@gmail.com>
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

__copyright__ = "(C) 2026 Hidayat Trimarsanto <trimarsanto@gmail.com>"
__author__ = "trimarsanto@gmail.com"
__license__ = "MPL-2.0"

from litestar_pulse.cli.commands import NoReturn, pulsemgr, get_dbhandler

import click


class RebrandedGroup(pulsemgr.__class__):
    def __init__(self, *args, **kwargs):
        # 1. Properly initialize the group with all Click-passed attributes
        super().__init__(*args, **kwargs)

        # 2. Merge parameters (options/arguments) from the existing group
        # This preserves the original options for the new brand
        self.params.extend(pulsemgr.params)

        # 3. Inherit all existing subcommands into this top-level group
        for cmd_name, cmd_obj in pulsemgr.commands.items():
            self.add_command(cmd_obj, name=cmd_name)


@click.group(cls=RebrandedGroup, name="messy2-mgr")
def messy2_mgr(use_ipdb: bool):
    """This new group now has all the old options and commands."""
    from litestar_pulse.db import set_initdb_function
    from ..db.handler import MESSy2Handler
    from ..db.initdb import initialize_database

    click.echo("Initializing MESSy2 CLI...")
    set_initdb_function(initialize_database)

    ctx = click.get_current_context()
    ctx.invoke(pulsemgr.callback, use_ipdb=use_ipdb)  # type: ignore


@messy2_mgr.command(name="institution-list")
async def institution_list():
    click.echo("Listing user domains...")

    async with get_dbhandler() as dbh:
        institutions = await dbh.repo.institution.list()
        for institution in institutions:
            click.echo(f"- {institution.name}")


@messy2_mgr.command(name="institution-add")
async def institution_add():
    click.echo("Adding new institution...")


@messy2_mgr.command(name="project-list")
async def project_list():
    pass


@messy2_mgr.command(name="project-add")
async def project_add():
    pass


def main() -> None:
    """
    CLI entry point for messy2_mgr standalone command
    """

    messy2_mgr()


# EOF
