from __future__ import annotations

from datetime import date
from typing import Any


from sqlalchemy import Column, Table, ForeignKey, UniqueConstraint, Identity
from sqlalchemy.orm import DynamicMapped, Mapped, relationship, deferred, mapped_column
from sqlalchemy.orm.collections import attribute_mapped_collection
from sqlalchemy import types

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

from ...lib import roles as r

MSY2_STORAGE = "messy2-storage"

MSY2AttachedFiles = AttachedFiles(MSY2_STORAGE)
MSY2Attachment = Attachment(MSY2_STORAGE)


"""
TODO:
- __searchable__ provides a list of fields that can be searched with full text search.
  needs FullTextSearchMixin since postgresql and sqlite will need different implementations

"""


class Institution(IdentityUUIDv7UserAuditBase, MSY2AttachedFiles, RoleMixin):

    __managing_roles__ = RoleMixin.__managing_roles__ | {r.INSTITUTION_MANAGE}
    __modifying_roles__ = __managing_roles__ | {r.INSTITUTION_MODIFY}

    __tablename__ = "institutions"

    code: Mapped[str] = mapped_column(types.String(24), nullable=False, unique=True)
    alt_codes: Mapped[str | None] = mapped_column(
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
    Column("id", types.Integer, Identity(), primary_key=True),
    Column("project_id", types.Integer, ForeignKey("projects.id"), nullable=False),
    Column(
        "institution_id", types.Integer, ForeignKey("institutions.id"), nullable=False
    ),
    UniqueConstraint("project_id", "institution_id"),
)


class Project(IdentityUUIDv7UserAuditBase, MSY2AttachedFiles, RoleMixin):

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
        order_by=projects_institutions.c.id,
    )

    samples: DynamicMapped[Sample] = relationship(
        "Sample", lazy="dynamic", back_populates="collection", passive_deletes=True
    )


class Sample(IdentityUUIDv7UserAuditBase, MSY2Attachment, RoleMixin):

    __tablename__ = "samples"

    collection_id: Mapped[int] = mapped_column(
        types.Integer,
        ForeignKey("collections.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    collection: Mapped[Any] = relationship(
        "Collection", uselist=False, back_populates="samples"
    )

    # various code
    code: Mapped[str] = mapped_column(types.String(16), nullable=False, unique=True)
    acc_code: Mapped[str | None] = mapped_column(
        types.String(31), nullable=True, unique=True
    )
    received_date: Mapped[date] = mapped_column(types.Date, nullable=False)

    sequence_name: Mapped[str | None] = mapped_column(
        types.String(63), nullable=True, index=True, unique=True
    )

    species_id: Mapped[int] = mapped_column(
        types.Integer, ForeignKey("eks.id"), nullable=False
    )
    species = enumkey_proxy("species_id", "@SPECIES")

    passage_id: Mapped[int] = mapped_column(
        types.Integer, ForeignKey("eks.id"), nullable=False
    )
    passage = enumkey_proxy("passage_id", "@PASSAGE")

    collection_date: Mapped[date] = mapped_column(
        types.Date, index=True, nullable=False
    )
    location: Mapped[str] = mapped_column(
        types.String(64), nullable=False, index=True, server_default=""
    )
    location_info: Mapped[str] = mapped_column(
        types.String(128), nullable=False, server_default=""
    )

    host_id: Mapped[int] = mapped_column(
        types.Integer, ForeignKey("eks.id"), nullable=False
    )
    host = enumkey_proxy("host_id", "@SPECIES")

    host_info: Mapped[str] = mapped_column(
        types.String(64), nullable=False, server_default=""
    )
    host_gender: Mapped[str] = mapped_column(
        types.String(1), nullable=False, server_default="X"
    )
    host_age: Mapped[float] = mapped_column(
        types.Float, nullable=False, server_default="-1"
    )

    host_occupation_id: Mapped[int] = mapped_column(
        types.Integer, ForeignKey("eks.id"), nullable=False
    )
    host_occupation = enumkey_proxy("host_occupation_id", "@HOST_OCCUPATION")

    host_status_id: Mapped[int] = mapped_column(
        types.Integer, ForeignKey("eks.id"), nullable=False
    )
    host_status = enumkey_proxy("host_status_id", "@HOST_STATUS")

    host_severity: Mapped[int] = mapped_column(
        types.Integer, nullable=False, server_default="-1"
    )

    infection_date: Mapped[date | None] = mapped_column(types.Date, nullable=True)
    symptom_date: Mapped[date | None] = mapped_column(types.Date, nullable=True)
    # space-delimited symptom list
    symptoms: Mapped[str] = mapped_column(
        types.String(128), nullable=False, server_default=""
    )
    # space-delimited comorbid list
    comorbids: Mapped[str] = mapped_column(
        types.String(128), nullable=False, server_default=""
    )
    last_infection_date: Mapped[date | None] = mapped_column(types.Date, nullable=True)
    last_infection_info: Mapped[str] = mapped_column(
        types.String(64), nullable=False, server_default=""
    )

    category_id: Mapped[int] = mapped_column(
        types.Integer, ForeignKey("eks.id"), nullable=False
    )
    category = enumkey_proxy("category_id", "@CATEGORY")

    specimen_type_id: Mapped[int] = mapped_column(
        types.Integer, ForeignKey("eks.id"), nullable=False
    )
    specimen_type = enumkey_proxy("specimen_type_id", "@SPECIMEN_TYPE")

    outbreak: Mapped[str] = mapped_column(
        types.String(64), nullable=False, server_default=""
    )
    last_vaccinated_date: Mapped[date | None] = mapped_column(types.Date, nullable=True)
    last_vaccinated_dose: Mapped[int] = mapped_column(
        types.Integer, nullable=False, server_default="-1"
    )
    last_vaccinated_info: Mapped[str] = mapped_column(
        types.String(64), nullable=False, server_default=""
    )
    treatment: Mapped[str] = mapped_column(
        types.String(64), nullable=False, server_default=""
    )

    viral_load: Mapped[float] = mapped_column(
        types.Float, nullable=False, server_default="-1"
    )
    ct_target1: Mapped[float] = mapped_column(
        types.Float, nullable=False, server_default="-1"
    )
    ct_target2: Mapped[float] = mapped_column(
        types.Float, nullable=False, server_default="-1"
    )
    ct_target3: Mapped[float] = mapped_column(
        types.Float, nullable=False, server_default="-1"
    )
    ct_target4: Mapped[float] = mapped_column(
        types.Float, nullable=False, server_default="-1"
    )
    ct_host1: Mapped[float] = mapped_column(
        types.Float, nullable=False, server_default="-1"
    )
    ct_host2: Mapped[float] = mapped_column(
        types.Float, nullable=False, server_default="-1"
    )

    ct_method_id: Mapped[int] = mapped_column(
        types.Integer, ForeignKey("eks.id"), nullable=False
    )
    ct_method = enumkey_proxy("ct_method_id", "@CT_METHOD")

    ct_info: Mapped[str] = mapped_column(
        types.String(64), nullable=False, server_default=""
    )

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

    # sampling institution, where the samples were initially taken, usually hospital
    # or health facility.
    sampling_code: Mapped[str | None] = mapped_column(types.String(32), nullable=True)

    sampling_institution_id: Mapped[int] = mapped_column(
        types.Integer, ForeignKey("institutions.id"), nullable=False
    )
    sampling_institution: Mapped[Institution] = relationship(
        Institution, uselist=False, foreign_keys=sampling_institution_id
    )

    related_sample_id: Mapped[int | None] = mapped_column(
        types.Integer, ForeignKey("samples.id"), nullable=True
    )

    # sample identification

    host_dob: Mapped[date | None] = mapped_column(types.Date, nullable=True)
    host_nik: Mapped[str] = mapped_column(
        types.String(24), nullable=False, server_default=""
    )
    host_nar: Mapped[str] = mapped_column(
        types.String(24), nullable=False, server_default=""
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

    platepositions: Mapped[list[PlatePosition]] = relationship(
        "PlatePosition", back_populates="sample", passive_deletes=True
    )

    sequences: DynamicMapped[Any] = relationship(
        "Sequence", lazy="dynamic", back_populates="sample", passive_deletes=True
    )

    lineages: Mapped[list[Any]] = relationship(
        "Lineage", back_populates="sample", passive_deletes=True
    )

    __table_args__ = (
        UniqueConstraint("originating_code", "originating_institution_id"),
        UniqueConstraint("sampling_code", "sampling_institution_id"),
    )

    __ek_fields__ = [
        "species",
        "passage",
        "host",
        "host_status",
        "host_occupation",
        "specimen_type",
        "ct_method",
        "category",
    ]

    __managing_roles__ = RoleMixin.__managing_roles__ | {r.SAMPLE_MANAGE}
    __modifying_roles__ = __managing_roles__ | {r.SAMPLE_MODIFY}


class Subject(IdentityUUIDv7UserAuditBase, MSY2Attachment, RoleMixin):
    """
    This class represent an individual subject (person/patient/host) record
    """

    __tablename__ = "subjects"

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


class PlatePosition(IdentityUserAuditBase, RoleMixin):

    __tablename__ = "platepositions"

    labware_id: Mapped[int] = mapped_column(
        types.Integer,
        ForeignKey("labwares.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    labware: Mapped[Labware] = relationship(
        "Labware", uselist=False, foreign_keys=labware_id, back_populates="positions"
    )

    sample_id: Mapped[int] = mapped_column(
        types.Integer, ForeignKey("samples.id"), index=True, nullable=False
    )
    sample: Mapped[Sample] = relationship(
        Sample, uselist=False, foreign_keys=sample_id, back_populates="platepositions"
    )

    # position will be 384:A01 -> P24, 96: A01 -> H12
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

    __table_args__ = (UniqueConstraint("labware_id", "position"),)


class Labware(IdentityUUIDv7UserAuditBase, MSY2AttachedFiles, RoleMixin):
    """
    This class represent a labware (plate, tube, etc.) record
    """

    __tablename__ = "labwares"

    user_id: Mapped[int] = mapped_column(
        types.Integer, ForeignKey("users.id"), nullable=False
    )
    user: Mapped[User] = relationship(User, uselist=False, foreign_keys=user_id)

    # primary group of user
    group_id: Mapped[int] = mapped_column(
        types.Integer, ForeignKey("groups.id"), nullable=False
    )
    group: Mapped[Group] = relationship(Group, uselist=False, foreign_keys=group_id)

    code: Mapped[str] = mapped_column(
        types.String(32), nullable=False, unique=True, server_default=""
    )
    date: Mapped[date] = mapped_column(
        types.Date, nullable=False, server_default=func.current_date()
    )

    specimen_type_id: Mapped[int] = mapped_column(
        types.Integer, ForeignKey("eks.id"), nullable=False
    )
    specimen_type = enumkey_proxy("specimen_type_id", "@SPECIMEN_TYPE")

    experiment_type_id: Mapped[int] = mapped_column(
        types.Integer, ForeignKey("eks.id"), nullable=False
    )
    experiment_type = enumkey_proxy("experiment_type_id", "@EXPERIMENT_TYPE")

    storage: Mapped[str] = deferred(
        mapped_column(types.String(64), nullable=False, server_default="")
    )
    remark: Mapped[str] = deferred(
        mapped_column(types.Text, nullable=False, server_default="")
    )

    positions: Mapped[list[PlatePosition]] = relationship(
        PlatePosition,
        order_by="PlatePosition.id",
        passive_deletes=True,
        back_populates="labware",
    )

    sequencingruns: Mapped[list[SequencingRunPlate]] = relationship(
        "SequencingRunPlate",
        order_by="sequencingrunplates.c.plate_id",
        back_populates="plate",
    )

    __ek_fields__ = ["specimen_type", "experiment_type"]

    __managing_roles__ = RoleMixin.__managing_roles__ | {r.PLATE_MANAGE}
    __modifying_roles__ = __managing_roles__ | {r.PLATE_MODIFY}


plate_file_table = Table(
    "plates_files",
    metadata,
    Column("id", types.Integer, Identity(), primary_key=True),
    Column(
        "plate_id",
        types.Integer,
        ForeignKey("plates.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    ),
    Column(
        "file_id",
        types.Integer,
        ForeignKey("fileattachments.id", ondelete="CASCADE"),
        nullable=False,
    ),
    UniqueConstraint("plate_id", "file_id"),
)


class StorageUnit(IdentityUUIDv7UserAuditBase, MSY2AttachedFiles, RoleMixin):
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
        mapped_column(types.JSON, nullable=False, server_default="null")
    )

    group_id: Mapped[int] = mapped_column(
        types.Integer, ForeignKey("groups.id"), nullable=False
    )
    group: Mapped[Group] = relationship(Group, uselist=False, foreign_keys=group_id)


class LabwarePosition(IdentityUserAuditBase, RoleMixin):

    __tablename__ = "labwarepositions"

    storageunit_id: Mapped[int] = mapped_column(
        types.Integer,
        ForeignKey("storageunits.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    storageunit: Mapped[StorageUnit] = relationship(
        StorageUnit,
        uselist=False,
        foreign_keys=storageunit_id,
        back_populates="labwares",
    )

    labware_id: Mapped[int] = mapped_column(
        types.Integer, ForeignKey("labwares.id"), index=True, nullable=False
    )
    labware: Mapped[Labware] = relationship(
        Labware, uselist=False, foreign_keys=labware_id, back_populates="storageunits"
    )

    position: Mapped[str] = mapped_column(
        types.String(16), nullable=False, server_default=""
    )


class SequencingRun(IdentityUUIDv7UserAuditBase, MSY2AttachedFiles, RoleMixin):
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
        types.Integer, ForeignKey("eks.id"), nullable=False
    )
    sequencing_kit = EK.proxy("sequencing_kit_id", "@SEQUENCING_KIT")

    remark: Mapped[str] = deferred(
        mapped_column(types.Text, nullable=False, server_default="")
    )

    sequences: DynamicMapped[Any] = relationship(
        "Sequence", lazy="dynamic", back_populates="sequencingrun", passive_deletes=True
    )

    plates: Mapped[list[SequencingRunPlate]] = relationship(
        "SequencingRunPlate",
        order_by="sequencingrunplates.c.plate_id",
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
            q = select(func.count(Sample.id))
        else:
            q = select(Sample)
        q = (
            q.join(PlatePosition)
            .join(Plate)
            .join(SequencingRunPlate)
            .filter(SequencingRunPlate.sequencingrun_id == self.id)
            .filter(~Sample.code.in_(["-", "*", "NTC1", "NTC2", "NTC3", "NTC4"]))
        )
        if scalar:
            return object_session(self).scalar(q)
        return object_session(self).execute(q).scalars()

    def update(self, obj):

        if isinstance(obj, dict):

            dbh = get_dbhandler()

            if "group" in obj:
                obj["group_id"] = dbh.get_group(obj["group"]).id
                del obj["group"]

            if type(inst := obj.get("sequencing_provider", None)) == str:
                self.sequencing_provider_id = dbh.get_institutions_by_codes(
                    obj["sequencing_provider"], None, raise_if_empty=True
                )[0].id
                del obj["sequencing_provider"]

            convert_date(obj, "date")

            self.update_fields_with_dict(
                obj, additional_fields=["depthplots", "qcreport", "screenshot"]
            )
            self.update_ek_with_dict(obj, dbh=dbh)

        else:
            raise RuntimeError("PROG/ERR: can only update from dict object")

    def as_dict(self, exclude=None):
        d = super().as_dict(exclude={"sequences", "plates", "additional_files"})
        d["plates"] = [
            [p.plate.code, p.adapterindex, p.lane, p.note] for p in self.plates
        ]
        return d

    @classmethod
    def from_dict(cls, a_dict, dbh):
        run = super().from_dict(a_dict, dbh)
        for rp in a_dict.get("plates", []):
            plate = dbh.get_plates_by_codes(rp[0], groups=None, ignore_acl=True)[0]
            d = dict(
                sequencingrun_id=run.id,
                plate_id=plate.id,
                adapterindex=rp[1],
                lane=rp[2],
                note=rp[3],
            )
            srp = SequencingRunPlate.from_dict(d, dbh)

    def can_modify(self, user):
        if user.has_roles(*self.__managing_roles__):
            return True
        if user.has_roles(*self.__modifying_roles__):  # and user.in_group(self.group):
            return True
        return False


class SequencingRunPlate(IdentityUUIDv7UserAuditBase, MSY2AttachedFiles, RoleMixin):

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

    plate_id: Mapped[int] = mapped_column(
        types.Integer,
        ForeignKey("plates.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    plate: Mapped[Labware] = relationship(
        Labware, uselist=False, foreign_keys=plate_id, back_populates="sequencingruns"
    )

    adapterindex_id: Mapped[int] = mapped_column(
        types.Integer, ForeignKey("eks.id"), nullable=False
    )
    adapterindex = EK.proxy("adapterindex_id", "@ADAPTERINDEX")

    lane: Mapped[int] = mapped_column(types.Integer, nullable=False, server_default="1")

    note: Mapped[str | None] = mapped_column(types.Text, nullable=True)

    __ek_fields__ = {"adapterindex"}

    __table_args__ = (
        UniqueConstraint("sequencingrun_id", "plate_id"),
        UniqueConstraint("sequencingrun_id", "adapterindex_id", "lane"),
    )


# EOF
