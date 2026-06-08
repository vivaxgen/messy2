# SPDX-FileCopyrightText: 2026 Hidayat Trimarsanto <trimarsanto@gmail.com>
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

__copyright__ = "(C) 2026 Hidayat Trimarsanto <trimarsanto@gmail.com>"
__author__ = "trimarsanto@gmail.com"
__license__ = "MPL-2.0"

from datetime import date
from typing import Any


from sqlalchemy import Column, Table, ForeignKey, UniqueConstraint, Identity, select
from sqlalchemy.orm import (
    DynamicMapped,
    Mapped,
    relationship,
    deferred,
    mapped_column,
    object_session,
)
from sqlalchemy.orm.collections import attribute_mapped_collection
from sqlalchemy import types, func
from sqlalchemy.ext.associationproxy import association_proxy, AssociationProxy

from advanced_alchemy.base import orm_registry
from advanced_alchemy.types import JsonB
from advanced_alchemy.types.file_object import FileObject, StoredObject, FileObjectList


from litestar_pulse.db.models.coremixins import (
    AttachedFiles,
    Attachment,
    IdentityUUIDv7UserAuditBase,
    IdentityUserAuditBase,
    RoleMixin,
)
from litestar_pulse.db.models.enumkey import EnumKey, enumkey_proxy
from litestar_pulse.db.models.account import Group, User
from litestar_pulse.db import get_handler

from ...lib import roles as r

MESSy2_STORAGE = "messy2-storage"

MESSy2AttachedFiles = AttachedFiles(MESSy2_STORAGE)
MESSy2Attachment = Attachment(MESSy2_STORAGE)


"""
TODO:
- __searchable__ provides a list of fields that can be searched with full text search.
  needs FullTextSearchMixin since postgresql and sqlite will need different implementations

DESIGN:
- 

Instititution -> the institution (hospital, lab, etc.) that is associated with the specimen,
    can be either originating institution or sampling institution.
Project -> can have multiple institution, but institution can also be shared across projects

Specimen -> the actual specimen
Subject -> the individual (person/host/patient) from which specimen was taken
Labware -> plate, tube, etc. that can hold specimen

StorageUnit -> freezer, shelf, box, etc. that can hold labware
SequencingRun -> libprep + sequencing run, can have multiple plates (labware) and
    multiple samples (specimen) through the plates
Sample -> a sample taken from a subject, can be linked to multiple specimen
    (e.g. multiple swabs taken from the same patient), and can be linked to
    multiple labware (e.g. same sample can be put in multiple tubes for different tests) 

"""


class Institution(IdentityUUIDv7UserAuditBase, MESSy2AttachedFiles, RoleMixin):

    __managing_roles__ = RoleMixin.__managing_roles__ | {r.INSTITUTION_MANAGE}
    __modifying_roles__ = __managing_roles__ | {r.INSTITUTION_MODIFY}
    __vieweing_roles__ = __modifying_roles__ | {r.INSTITUTION_VIEW}

    __tablename__ = "institutions"

    code: Mapped[str] = mapped_column(types.String(24), nullable=False, unique=True)
    alt_code: Mapped[str | None] = mapped_column(
        types.String(47), nullable=True, unique=True
    )
    name: Mapped[str] = mapped_column(types.String(128), nullable=False, unique=True)
    address: Mapped[str] = deferred(
        mapped_column(types.String(128), nullable=False, server_default="")
    )
    zipcode: Mapped[str] = mapped_column(
        types.String(8), nullable=False, server_default=""
    )
    contact: Mapped[str] = mapped_column(
        types.String(64), nullable=False, server_default=""
    )
    remark: Mapped[str] = deferred(
        mapped_column(types.Text, nullable=False, server_default="")
    )

    __searchable__ = ["code", "alt_codes", "name", "address"]


projects_institutions = Table(
    "projects_institutions",
    orm_registry.metadata,
    Column("project_id", types.Integer, ForeignKey("projects.id"), primary_key=True),
    Column(
        "institution_id", types.Integer, ForeignKey("institutions.id"), primary_key=True
    ),
)


class Project(IdentityUUIDv7UserAuditBase, MESSy2AttachedFiles, RoleMixin):

    __managing_roles__ = RoleMixin.__managing_roles__ | {r.PROJECT_MANAGE}
    __modifying_roles__ = __managing_roles__ | {r.PROJECT_MODIFY}

    __tablename__ = "projects"

    code: Mapped[str] = mapped_column(types.String(16), nullable=False, unique=True)
    description: Mapped[str] = mapped_column(
        types.String(256), nullable=False, server_default=""
    )
    remark: Mapped[str] = deferred(
        mapped_column(types.Text, nullable=False, server_default="")
    )
    data: Mapped[dict[str, Any]] = deferred(
        mapped_column(types.JSON, nullable=False, server_default="null")
    )

    group_id: Mapped[int] = mapped_column(
        types.Integer, ForeignKey("groups.id"), nullable=False
    )
    group: Mapped[Group] = relationship(Group, uselist=False, foreign_keys=group_id)

    contact: Mapped[str] = deferred(
        mapped_column(types.String(64), nullable=False, server_default="")
    )

    institutions: Mapped[list[Institution]] = relationship(
        Institution,
        secondary=projects_institutions,
        order_by=projects_institutions.c.institution_id,
    )

    collectioninfos: DynamicMapped["CollectionInfo"] = relationship(
        "CollectionInfo",
        primaryjoin="Project.id == CollectionInfo.project_id",
        back_populates="project",
        passive_deletes=True,
    )

    specimen: DynamicMapped["Specimen"] = relationship(
        "Specimen",
        lazy="dynamic",
        secondary="collectioninfos",
        primaryjoin="Project.id == CollectionInfo.project_id",
        secondaryjoin="CollectionInfo.id == Specimen.collectioninfo_id",
        back_populates="project",
        passive_deletes=True,
    )


class CollectionInfo(IdentityUUIDv7UserAuditBase, MESSy2Attachment, RoleMixin):
    """
    This class represent information of collection event related to specimen collection, such as
    date of collection, time point, location, etc and any other (meta) information pertinent
    to the collection event.
    This is separated from Specimen since it can be shared across multiple specimens
    (e.g. different blood (venous, finger-prick) taken from the same patient at the same time)
    """

    __tablename__ = "collectioninfos"

    # time, location and institution

    date: Mapped[date] = mapped_column(
        types.Date, nullable=False, server_default=func.current_date()
    )

    time_point: Mapped[int] = mapped_column(
        types.Integer, nullable=False, server_default="0"
    )

    sampling_institution_id: Mapped[int] = mapped_column(
        types.Integer, ForeignKey("institutions.id"), nullable=False
    )
    sampling_institution: Mapped[Institution] = relationship(
        Institution, uselist=False, foreign_keys=sampling_institution_id
    )

    # subject and project information
    subject_id: Mapped[int] = mapped_column(
        types.Integer, ForeignKey("subjects.id"), nullable=False
    )
    subject: Mapped[Subject] = relationship(
        "Subject", uselist=False, foreign_keys=subject_id
    )

    project_id: Mapped[int] = mapped_column(
        types.Integer, ForeignKey("projects.id"), nullable=False
    )

    project: Mapped[Project] = relationship(
        "Project",
        uselist=False,
        primaryjoin="CollectionInfo.project_id == Project.id",
        secondary="projects_institutions",
        secondaryjoin="Project.id == projects_institutions.c.project_id",
        back_populates="collectioninfos",
        viewonly=True,
    )

    specimens: DynamicMapped["Specimen"] = relationship(
        "Specimen",
        lazy="dynamic",
        back_populates="collectioninfo",
        passive_deletes=True,
        foreign_keys="Specimen.collectioninfo_id",
    )

    # clinical and other meta information at collection time point

    #


class Specimen(IdentityUUIDv7UserAuditBase, MESSy2Attachment, RoleMixin):
    """
    This class represent any Specimen record
    """

    __tablename__ = "specimens"

    collectioninfo_id: Mapped[int] = mapped_column(
        types.Integer,
        ForeignKey("collectioninfos.id"),
        nullable=False,  # , unique=True
        # one-to-one relationship, but not enforcing unique constraint since some
        # specimens may not have collection info (eg. control, lab strain, etc)
    )
    collectioninfo: Mapped[CollectionInfo] = relationship(
        CollectionInfo, uselist=False, foreign_keys=collectioninfo_id
    )

    # various code
    code: Mapped[str] = mapped_column(types.String(16), nullable=False, unique=True)

    project: Mapped[Project] = relationship(
        "Project",
        uselist=False,
        primaryjoin="Specimen.collectioninfo_id == CollectionInfo.id",
        secondary="projects_institutions",
        secondaryjoin="CollectionInfo.project_id == Project.id",
        viewonly=True,
    )

    species_id: Mapped[int] = mapped_column(
        types.Integer, ForeignKey("enumkeys.id"), nullable=False
    )
    species = enumkey_proxy("species_id", "@SPECIES")

    passage_id: Mapped[int] = mapped_column(
        types.Integer, ForeignKey("enumkeys.id"), nullable=False
    )
    passage = enumkey_proxy("passage_id", "@PASSAGE")

    # originating lab, where diagnostic tests were performed or samples were prepared
    originating_code: Mapped[str | None] = mapped_column(
        types.String(32), nullable=True
    )

    originating_institution_id: Mapped[int] = mapped_column(
        types.Integer, ForeignKey("institutions.id"), nullable=False
    )
    originating_institution: Mapped[Institution] = relationship(
        Institution, uselist=False, foreign_keys=originating_institution_id
    )

    remark: Mapped[str] = deferred(
        mapped_column(types.Text, nullable=False, server_default="")
    )
    comment: Mapped[str] = deferred(
        mapped_column(types.Text, nullable=False, server_default="")
    )

    flag: Mapped[int] = mapped_column(types.Integer, nullable=False, server_default="0")
    extdata: Mapped[dict[str, Any]] = deferred(
        mapped_column(types.JSON, nullable=False, server_default="null")
    )

    positions: Mapped[list[LabwarePosition]] = relationship(
        "LabwarePosition", back_populates="sample", passive_deletes=True
    )

    __table_args__ = (
        UniqueConstraint("originating_code", "originating_institution_id"),
    )

    __managing_roles__ = RoleMixin.__managing_roles__ | {r.SAMPLE_MANAGE}
    __modifying_roles__ = __managing_roles__ | {r.SAMPLE_MODIFY}


class Subject(IdentityUUIDv7UserAuditBase, MESSy2Attachment, RoleMixin):
    """
    This class represent an individual subject (person/patient/host) record
    """

    __tablename__ = "subjects"

    code: Mapped[str] = mapped_column(types.String(16), nullable=False, unique=True)

    initials: Mapped[str] = mapped_column(
        types.String(8), nullable=False, server_default=""
    )

    last_name: Mapped[str] = mapped_column(
        types.String(64), nullable=False, server_default=""
    )
    first_name: Mapped[str] = mapped_column(
        types.String(64), nullable=False, server_default=""
    )

    father_initials: Mapped[str] = mapped_column(
        types.String(8), nullable=False, server_default=""
    )
    mother_initials: Mapped[str] = mapped_column(
        types.String(8), nullable=False, server_default=""
    )

    # dob - date of birth (allowing to have missing year, month or day)
    dob_year: Mapped[int] = mapped_column(types.Integer, nullable=True)
    dob_month: Mapped[int] = mapped_column(types.Integer, nullable=True)
    dob_day: Mapped[int] = mapped_column(types.Integer, nullable=True)

    remark: Mapped[str] = deferred(
        mapped_column(types.Text, nullable=False, server_default="")
    )
    data: Mapped[dict[str, Any]] = deferred(
        mapped_column(JsonB, nullable=False, server_default="null")
    )

    contact: Mapped[str] = deferred(
        mapped_column(types.String(64), nullable=False, server_default="")
    )


class Labware(IdentityUUIDv7UserAuditBase, MESSy2AttachedFiles, RoleMixin):
    """
    This class represent a labware (plate, tube, etc.) record
    """

    __tablename__ = "labwares"

    code: Mapped[str] = mapped_column(
        types.String(32), nullable=False, unique=True, server_default=""
    )
    date: Mapped[date] = mapped_column(
        types.Date, nullable=False, server_default=func.current_date()
    )

    specimen_type_id: Mapped[int] = mapped_column(
        types.Integer, ForeignKey("enumkeys.id"), nullable=False
    )
    specimen_type = enumkey_proxy("specimen_type_id", "@SPECIMEN_TYPE")

    experiment_type_id: Mapped[int] = mapped_column(
        types.Integer, ForeignKey("enumkeys.id"), nullable=False
    )
    experiment_type = enumkey_proxy("experiment_type_id", "@EXPERIMENT_TYPE")

    storage: Mapped[str] = deferred(
        mapped_column(types.String(64), nullable=False, server_default="")
    )
    remark: Mapped[str] = deferred(
        mapped_column(types.Text, nullable=False, server_default="")
    )

    positions: Mapped[list[LabwarePosition]] = relationship(
        "LabwarePosition",
        order_by="LabwarePosition.id",
        passive_deletes=True,
        back_populates="labware",
    )

    storageunit_id: Mapped[int | None] = mapped_column(
        types.Integer, ForeignKey("storageunits.id", ondelete="SET NULL"), nullable=True
    )
    storageunit: Mapped[StorageUnit | None] = relationship(
        "StorageUnit",
        back_populates="labwares",
        passive_deletes=True,
    )

    sequencingruns: Mapped[list[SequencingRunPlate]] = relationship(
        "SequencingRunPlate",
        order_by="sequencingrunplates.c.labware_id",
        back_populates="plate",
    )

    __managing_roles__ = RoleMixin.__managing_roles__ | {r.PLATE_MANAGE}
    __modifying_roles__ = __managing_roles__ | {r.PLATE_MODIFY}


class StorageUnit(IdentityUUIDv7UserAuditBase, MESSy2AttachedFiles, RoleMixin):
    """
    This class represent a storage unit (freezer, shelf, box, etc.) record
    """

    __tablename__ = "storageunits"

    code: Mapped[str] = mapped_column(
        types.String(32), nullable=False, unique=True, server_default=""
    )
    description: Mapped[str] = mapped_column(
        types.String(256), nullable=False, server_default=""
    )
    physical_location: Mapped[str] = mapped_column(
        types.String(64), nullable=False, server_default=""
    )
    remark: Mapped[str] = deferred(
        mapped_column(types.Text, nullable=False, server_default="")
    )
    data: Mapped[dict[str, Any]] = deferred(
        mapped_column(JsonB, nullable=False, server_default="null")
    )

    labwares: Mapped[list[Labware]] = relationship(
        Labware,
        back_populates="storageunit",
        passive_deletes=True,
    )

    group_id: Mapped[int] = mapped_column(
        types.Integer, ForeignKey("groups.id"), nullable=False
    )
    group: Mapped[Group] = relationship(Group, uselist=False, foreign_keys=group_id)


class LabwarePosition(IdentityUserAuditBase, RoleMixin):

    __tablename__ = "labwarepositions"

    labware_id: Mapped[int] = mapped_column(
        types.Integer, ForeignKey("labwares.id"), index=True, nullable=False
    )
    labware: Mapped[Labware] = relationship(
        Labware,
        uselist=False,
        foreign_keys=labware_id,
        back_populates="positions",
    )

    sample_id: Mapped[int] = mapped_column(
        types.Integer, ForeignKey("specimens.id"), index=True, nullable=True
    )
    sample: Mapped["Specimen"] = relationship(
        "Specimen", uselist=False, foreign_keys=sample_id
    )

    position: Mapped[str] = mapped_column(
        types.String(3), nullable=False, server_default=""
    )
    value: Mapped[float] = mapped_column(
        types.Float, nullable=False, server_default="-1"
    )
    volume: Mapped[float] = mapped_column(
        types.Float, nullable=False, server_default="-1"
    )
    note: Mapped[str | None] = mapped_column(types.String(31), nullable=True)


class SequencingRun(IdentityUUIDv7UserAuditBase, MESSy2AttachedFiles, RoleMixin):
    """
    This class represent a libprep + sequencing run
    """

    __tablename__ = "sequencingruns"
    __attachedfiles_category__ = {"depth-plot", "general", "qc-report", "screenshot"}

    code: Mapped[str] = mapped_column(
        types.String(16), nullable=False, unique=True, server_default=""
    )
    serial: Mapped[str] = mapped_column(
        types.String(48), nullable=False, unique=True, server_default=""
    )
    date: Mapped[date] = mapped_column(
        types.Date, nullable=False, server_default=func.current_date()
    )

    # primary group of user
    group_id: Mapped[int] = mapped_column(
        types.Integer, ForeignKey("groups.id"), nullable=False
    )
    group: Mapped[Group] = relationship(Group, uselist=False, foreign_keys=group_id)

    sequencing_provider_id: Mapped[int] = mapped_column(
        types.Integer, ForeignKey("institutions.id"), nullable=False
    )
    sequencing_provider: Mapped[Institution] = relationship(
        Institution, uselist=False, foreign_keys=sequencing_provider_id
    )

    sequencing_kit_id: Mapped[int] = mapped_column(
        types.Integer, ForeignKey("enumkeys.id"), nullable=False
    )
    sequencing_kit = enumkey_proxy("sequencing_kit_id", "@SEQUENCING_KIT")

    remark: Mapped[str] = deferred(
        mapped_column(types.Text, nullable=False, server_default="")
    )

    plates: Mapped[list[SequencingRunPlate]] = relationship(
        "SequencingRunPlate",
        order_by="sequencingrunplates.c.labware_id",
        back_populates="sequencingrun",
    )

    __ek_fields__ = ["sequencing_kit"]

    __managing_roles__ = RoleMixin.__managing_roles__ | {r.SEQUENCINGRUN_MANAGE}
    __modifying_roles__ = __managing_roles__ | {r.SEQUENCINGRUN_MODIFY}

    def __str__(self):
        return self.code

    def __repr__(self):
        return f"SequencingRun('{self.code}')"

    def get_related_samples(self, scalar=False):
        if scalar:
            q = select(func.count(Specimen.id))
        else:
            q = select(Specimen)
        q = (
            q.join(LabwarePosition)
            .join(Labware)
            .join(SequencingRunPlate)
            .filter(SequencingRunPlate.sequencingrun_id == self.id)
            .filter(~Specimen.code.in_(["-", "*", "NTC1", "NTC2", "NTC3", "NTC4"]))
        )
        if scalar:
            return object_session(self).scalar(q)  # type: ignore
        return object_session(self).execute(q).scalars()  # type: ignore


class SequencingRunPlate(IdentityUUIDv7UserAuditBase, MESSy2AttachedFiles, RoleMixin):

    __tablename__ = "sequencingrunplates"

    sequencingrun_id: Mapped[int] = mapped_column(
        types.Integer,
        ForeignKey("sequencingruns.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    sequencingrun: Mapped[SequencingRun] = relationship(
        SequencingRun,
        uselist=False,
        foreign_keys=sequencingrun_id,
        back_populates="plates",
    )

    labware_id: Mapped[int] = mapped_column(
        types.Integer,
        ForeignKey("labwares.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    plate: Mapped[Labware] = relationship(
        Labware, uselist=False, foreign_keys=labware_id, back_populates="sequencingruns"
    )

    adapterindex_id: Mapped[int] = mapped_column(
        types.Integer, ForeignKey("enumkeys.id"), nullable=False
    )
    adapterindex = enumkey_proxy("adapterindex_id", "@ADAPTERINDEX")

    lane: Mapped[int] = mapped_column(types.Integer, nullable=False, server_default="1")

    note: Mapped[str | None] = mapped_column(types.Text, nullable=True)

    __ek_fields__ = {"adapterindex"}

    __table_args__ = (
        UniqueConstraint("sequencingrun_id", "labware_id"),
        UniqueConstraint("sequencingrun_id", "adapterindex_id", "lane"),
    )


# EOF
