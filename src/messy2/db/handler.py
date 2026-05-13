# SPDX-FileCopyrightText: 2026 Hidayat Trimarsanto <trimarsanto@gmail.com>
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

__copyright__ = "(C) 2026 Hidayat Trimarsanto <trimarsanto@gmail.com>"
__author__ = "trimarsanto@gmail.com"
__license__ = "MPL-2.0"

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from advanced_alchemy.repository import SQLAlchemyAsyncRepository
from advanced_alchemy.service import SQLAlchemyAsyncRepositoryService

import lazy_object_proxy as lop

from litestar_pulse.db import handler, set_handler_class

from .models import schema

# Institution


class InstitutionRepo(SQLAlchemyAsyncRepository[schema.Institution]):
    model_type = schema.Institution


class InstitutionService(handler.LPBaseService[schema.Institution]):
    repository_type = InstitutionRepo

    async def before_update_from_dict(
        self, instance: schema.Institution, data: dict
    ) -> None:

        if "files" in data:
            await self.update_fileobject_list(instance, "files", data)


# Project


class ProjectRepo(SQLAlchemyAsyncRepository[schema.Project]):
    model_type = schema.Project


class ProjectService(handler.LPBaseService[schema.Project]):
    repository_type = ProjectRepo

    async def before_update_from_dict(
        self, instance: schema.Project, data: dict
    ) -> None:

        if self.handler is None:
            raise ValueError("Handler is not set for ProjectService")

        if not isinstance(self.handler, MESSy2Handler):
            raise ValueError(
                "Handler for ProjectService must be an instance of MESSy2Handler"
            )

        # check if data contains "group" or "group_id", since they are mutually exclusive,
        # we can check for either one to determine if group update is needed
        if "group" in data and "group_id" in data:
            raise ValueError(
                "Updating site requires group_id or group field, but not both"
            )

        if "group" in data:
            data["group"] = await self.handler.normalize_groups(data["group"])

        if "institutions" in data:
            data["institutions"] = await self.handler.normalize_institutions(
                data["institutions"]
            )

        if "files" in data:
            await self.update_fileobject_list(instance, "files", data)


class Model(handler.Model):
    Institution = schema.Institution
    Project = schema.Project
    Sample = schema.Sample
    Subject = schema.Subject


class MESSy2Handler(handler.LPHandler):

    model = Model()

    def __init__(self, session: AsyncSession) -> None:

        handler: MESSy2Handler

        super().__init__(session=session)  # type: ignore

        # preapre all AsyncRepos & AsyncServices

        self.repo.Institution = lop.Proxy(lambda: InstitutionRepo(session=self.session))
        self.service.Institution = lop.Proxy(
            lambda: InstitutionService(
                session=self.session,
                repository=self.repo.Institution.__wrapped__,
                handler=self,
            )
        )

        self.repo.Project = lop.Proxy(lambda: ProjectRepo(session=self.session))
        self.service.Project = lop.Proxy(
            lambda: ProjectService(
                session=self.session,
                repository=self.repo.Project.__wrapped__,
                handler=self,
            )
        )

    async def normalize_institutions(
        self, institutions: list[Any] | Any
    ) -> list[schema.Institution] | schema.Institution:
        """Normalize a list of institution identifiers (int IDs or string or Institution objects) to a list of Institution objects."""
        scalar = False
        normalized_institutions: list[schema.Institution] = []
        if not isinstance(institutions, list):
            scalar = True
            institutions = [institutions]
        for institution_id in institutions:
            if isinstance(institution_id, schema.Institution):
                normalized_institutions.append(institution_id)
            else:
                if isinstance(institution_id, str):
                    institution_code = institution_id.strip()
                    institution = (
                        await self.repo.Institution.__wrapped__.get_one_or_none(
                            code=institution_code
                        )
                    )
                    if institution is None:
                        raise ValueError(
                            f"Institution with code '{institution_code}' not found"
                        )
                    normalized_institutions.append(institution)
                    continue
                try:
                    institution_id = int(institution_id)
                    normalized_institutions.append(
                        await self.repo.Institution.__wrapped__.get(institution_id)
                    )
                except (ValueError, TypeError):
                    raise ValueError(
                        f"Invalid institution identifier: {institution_id}"
                    )

        if scalar and normalized_institutions:
            return normalized_institutions[0]
        return normalized_institutions


set_handler_class(MESSy2Handler)

# EOF
