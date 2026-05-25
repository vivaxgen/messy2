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

from ..db.models.schema import Project


class ProjectForm(fb.ModelForm):
    name = fb.StringField(
        label="Project Name",
        required=True,
        max_length=64,
    )
    description = fb.StringField(
        label="Description",
        required=False,
        max_length=256,
    )


class ProjectView(LPModelView):
    model_type = Project


def generate_project_table(
    projects: list[Project], request: Request
) -> tuple[t.Tag, str]:

    not_guest = True

    table_body = t.tbody()

    for project in projects:
        row = t.tr()[
            t.td()[
                (
                    t.literal(
                        '<input type="checkbox" name="project-ids" value="%d" />'
                        % project.id
                    )
                    if not_guest
                    else ""
                )
            ],
            t.td()[
                t.a(
                    href=request.url_for("project-view-id", dbid=project.id),
                )[project.code]
            ],
            t.td()[project.description or ""],
        ]

        table_body += row

    project_table = t.table(
        id="project-table",
        class_="table table-condensed table-striped table-sticky",
    )[
        t.thead()[
            t.tr()[
                t.th(style="width: 2em"),
                t.th()["Code"],
                t.th()["Description"],
            ]
        ]
    ]

    project_table.add(table_body)

    # wrap table in a scrollable wrapper so the sticky header works automatically
    wrapped_table = t.div(class_="table-sticky-wrapper")[project_table]

    if not_guest:
        add_button = ("New project", request.url_for("project-edit", dbid=0))

        bar = ct.selection_bar(
            "project-ids",
            action="/project/action",
            add=add_button,
        )
        html, code = bar.render(wrapped_table)

    else:
        html = t.div()[wrapped_table]
        code = ""

    code += template_datatable_js
    return html, code


template_datatable_js = """
"""


# EOF
