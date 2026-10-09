from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, func

from .database import Base


class Admin(Base):
    __tablename__ = "admins"

    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    password = Column(String(32), nullable=False)  # md5 hex digest
    name = Column(String(100))
    created_at = Column(DateTime, server_default=func.now())


class AvaSysIntent(Base):
    __tablename__ = "ava_sys_intents"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(String(255))
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now()
    )


class AvaSysIntentTrainingExample(Base):
    __tablename__ = "ava_sys_intent_training_examples"

    id = Column(Integer, primary_key=True)
    intent_id = Column(
        Integer,
        ForeignKey("ava_sys_intents.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False
    )
    text = Column(Text, nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now()
    )