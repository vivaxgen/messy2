# SPDX-FileCopyrightText: 2026 Hidayat Trimarsanto <trimarsanto@gmail.com>
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

__copyright__ = "(C) 2026 Hidayat Trimarsanto <trimarsanto@gmail.com>"
__author__ = "trimarsanto@gmail.com"
__license__ = "MPL-2.0"

from sqlalchemy.ext.asyncio import AsyncSession

from advanced_alchemy.repository import SQLAlchemyAsyncRepository
from advanced_alchemy.service import SQLAlchemyAsyncRepositoryService

import lazy_object_proxy as lop

from litestar_pulse.db.handler import LPHandler

from .models import schema

# Institution


class InstitutionRepo(SQLAlchemyAsyncRepository[schema.Institution]):
    model_type = schema.Institution


class InstitutionService(SQLAlchemyAsyncRepositoryService[schema.Institution]):
    repository_type = InstitutionRepo

    async def before_update_from_dict(
        self, instance: schema.Institution, data: dict
    ) -> None:

        if "files" in data:
            await self.update_fileobject_list(instance, "files", data)


# Project


class ProjectRepo(SQLAlchemyAsyncRepository[schema.Project]):
    model_type = schema.Project


class ProjectService(SQLAlchemyAsyncRepositoryService[schema.Project]):
    repository_type = ProjectRepo

    async def before_update_from_dict(
        self, instance: schema.Project, data: dict
    ) -> None:

        if "files" in data:
            await self.update_fileobject_list(instance, "files", data)


class MSY2Model:
    Institution = schema.Institution
    Project = schema.Project
    Sample = schema.Sample
    Subject = schema.Subject


class MSY2Handler(LPHandler):

    model = MSY2Model()

    def __init__(self, session: AsyncSession) -> None:

        super().__init__(session)

        # preapre all AsyncRepos & AsyncServices

        self.repo.Institution = lop.Proxy(lambda: InstitutionRepo(session=self.session))
        self.service.Institution = lop.Proxy(
            lambda: InstitutionService(
                session=self.session, repository=self.repo.Institution.__wrapped__
            )
        )

        self.repo.Project = lop.Proxy(lambda: ProjectRepo(session=self.session))
        self.service.Project = lop.Proxy(
            lambda: ProjectService(
                session=self.session, repository=self.repo.Project.__wrapped__
            )
        )
