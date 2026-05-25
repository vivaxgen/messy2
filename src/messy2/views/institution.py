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
from litestar_pulse.db.models.account import Any, UserDomain
from litestar_pulse.lib import compositetags as ct
from litestar_pulse.lib import validators as v
from litestar_pulse.lib import formbuilder as fb
from litestar_pulse.views.modelview import LPModelView, form_submit_bar

from ..db.models.schema import Institution


class InstitutionForm(fb.ModelForm):
    model_type = Institution

    uuid = fb.UUIDField(label="UUID", required=False)
    code = fb.StringField(label="Institution Code", required=True, max_length=16)
    alt_code = fb.StringField(label="Alt Code", required=False, max_length=32)
    name = fb.StringField(label="Institution Name", required=True, max_length=64)
    address = fb.StringField(label="Address", required=False, max_length=256)

    async def set_layout(self, controller: LPModelView | None = None) -> t.Tag:
        form_layout = t.fragment()[
            t.fieldset(name="main")[
                f.InlineInput()[
                    self.code.opts(offset=2, size=3),
                    self.uuid.opts(offset=1, size=3),
                ],
                self.alt_code.opts(offset=2, size=4),
                self.name.opts(offset=2, size=8),
                self.address.opts(offset=2, size=8),
            ]
        ]

        return form_layout


class InstitutionView(LPModelView):
    path = "/institution"
    model_type = Institution
    model_form = InstitutionForm

    def augment_repo_options(self, for_listing: bool = False) -> dict[str, Any]:
        options = super().augment_repo_options(for_listing=for_listing)

        if for_listing:
            options["order_by"] = [(Institution.name, False)]
        else:
            options.setdefault("load", []).append(undefer(Institution.address))

        return options

    def generate_instance_table(
        self, instances: list[Institution]
    ) -> tuple[t.Tag, str]:
        return generate_institution_table(instances, self.req)


def generate_institution_table(
    institutions: list[Institution], request: Request
) -> tuple[t.Tag, str]:

    not_guest = True

    table_body = t.tbody()

    for institution in institutions:
        row = t.tr()[
            t.td()[
                (
                    t.literal(
                        '<input type="checkbox" name="institution-ids" value="%d" />'
                        % institution.id
                    )
                    if not_guest
                    else ""
                )
            ],
            t.td()[
                t.a(
                    href=request.url_for("institution-view-id", dbid=institution.id),
                )[institution.code]
            ],
            t.td()[institution.alt_code or ""],
            t.td()[institution.name],
        ]

        table_body += row

    institution_table = t.table(
        id="institution-table",
        class_="table table-condensed table-striped table-sticky",
    )[
        t.thead()[
            t.tr()[
                t.th(style="width: 2em"),
                t.th()["Code"],
                t.th()["Alt Code"],
                t.th()["Name"],
            ]
        ]
    ]

    institution_table.add(table_body)

    # wrap table in a scrollable wrapper so the sticky header works automatically
    wrapped_table = t.div(class_="table-sticky-wrapper")[institution_table]

    if not_guest:
        add_button = ("New institution", request.url_for("institution-edit", dbid=0))

        bar = ct.selection_bar(
            "institution-ids",
            action="/institution/action",
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
