# SPDX-FileCopyrightText: 2026 Hidayat Trimarsanto <trimarsanto@gmail.com>
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

__copyright__ = "(C) 2026 Hidayat Trimarsanto <trimarsanto@gmail.com>"
__author__ = "trimarsanto@gmail.com"
__license__ = "MPL-2.0"

from sqlalchemy import select
from sqlalchemy.orm import object_session, undefer

from tagato import tags as t, formfields as f

from litestar import Response, Request, get
from litestar.response import Redirect

from litestar_pulse.lib import roles as r
from litestar_pulse.db.models.account import UserDomain
from litestar_pulse.lib import compositetags as ct
from litestar_pulse.lib import validators as v
from litestar_pulse.lib import formbuilder as fb
from litestar_pulse.views.modelview import LPModelView, form_submit_bar

from ..db.models.schema import Institution


class InstitutionForm(fb.ModelForm):
    model_type = Institution

    code = fb.StringField(
        label="Institution Code",
        required=True,
        max_length=16,
    )
    name = fb.StringField(
        label="Institution Name",
        required=True,
        max_length=64,
    )
    description = fb.StringField(
        label="Description",
        required=False,
        max_length=256,
    )


class InstitutionView(LPModelView):
    model_type = Institution
    model_form = InstitutionForm


def generate_institution_table(
    institutions: list[Institution], request: Request
) -> tuple[t.Tag, str]:
    pass


# EOF
