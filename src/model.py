import datetime
from typing import Annotated

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
    or_,
)
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy.orm import (
    Mapped,
    configure_mappers,
    declarative_base,
    mapped_column,
    relationship,
)
from sqlalchemy.types import VARCHAR, TypeDecorator
from sqlalchemy_continuum import make_versioned

make_versioned(user_cls=None)

Base = declarative_base()


class StringListType(TypeDecorator):
    impl = VARCHAR
    cache_ok = True

    def process_bind_param(self, value, dialect):  # noqa: ARG002, PLR6301
        if value is not None:
            return ",".join(value)
        return None

    def process_result_value(self, value, dialect):  # noqa: ARG002, PLR6301
        if value is not None:
            return value.split(",")
        return None

    @staticmethod
    def is_equal(column, value):
        return func.strpos(column, value) > 0

    @staticmethod
    def in_(column, values):
        return or_(*[StringList.is_equal(column, value) for value in values])


StringList = Annotated[StringListType, "StringList"]


class Agent(Base):
    __tablename__ = "agent"
    id = Column(Integer, primary_key=True)
    name = Column(String)


class Root(Base):
    __tablename__ = "root"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    type: Mapped[str] = mapped_column(unique=False, index=False, nullable=False)
    __mapper_args__ = {  # noqa: RUF012
        "polymorphic_identity": "root",
        "polymorphic_on": type,
    }


class TimestampMixin:
    creation_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    update_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class Entity(TimestampMixin, Root):
    __versioned__ = {}
    __tablename__ = "entity"
    id: Mapped[int] = mapped_column(
        ForeignKey("root.id"), primary_key=True, autoincrement=True
    )
    # _type: Mapped[str] = mapped_column(unique=False, index=False, nullable=False)
    # TODO: keep the _ ? put on agent ?
    createdBy = relationship(
        "Agent", uselist=False, foreign_keys="Entity.createdBy_id"
    )
    # TODO: move to mandatory
    createdBy_id: Mapped[int] = mapped_column(
        ForeignKey("agent.id"), nullable=True
    )
    updatedBy = relationship(
        "Agent", uselist=False, foreign_keys="Entity.updatedBy_id"
    )
    # TODO: move to mandatory
    updatedBy_id: Mapped[int] = mapped_column(
        ForeignKey("agent.id"), nullable=True
    )
    __mapper_args__ = {  # noqa: RUF012
        "polymorphic_identity": "entity",
    }


class ReconstructionMorphology(Entity):
    __versioned__ = {}
    __tablename__ = "reconstruction_morphology"
    id: Mapped[int] = mapped_column(
        ForeignKey("entity.id"), primary_key=True, autoincrement=True
    )
    description: Mapped[str] = mapped_column(
        unique=False, index=False, nullable=False
    )
    # name is not unique
    name: Mapped[str] = mapped_column(unique=False, index=True, nullable=False)
    morphology_description_vector: Mapped[str] = mapped_column(
        TSVECTOR, nullable=True
    )

    __mapper_args__ = {"polymorphic_identity": "reconstruction_morphology"}  # noqa: RUF012


class SingleNeuronSynaptome(Entity):
    __versioned__ = {}
    __tablename__ = "single_neuron_synaptome"
    id = Column(
        Integer, ForeignKey("entity.id"), primary_key=True, autoincrement=True
    )
    description = Column(Text, nullable=False, default="")
    name = Column(String, nullable=False, default="")
    seed = Column(Integer, nullable=False, default=-1)

    __mapper_args__ = {"polymorphic_identity": "single_neuron_synaptome"}


configure_mappers()

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

engine = create_engine("postgresql://postgres@localhost:5434/t2")
Base.metadata.create_all(engine)
