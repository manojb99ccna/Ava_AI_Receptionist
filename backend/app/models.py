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


class AvaLead(Base):
    __tablename__ = "ava_leads"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=True)
    phone = Column(String(30), nullable=True)
    email = Column(String(255), nullable=True)
    requested_service = Column(String(255), nullable=True)
    preferred_datetime = Column(String(100), nullable=True)
    status = Column(String(30), nullable=False, default="new")
    source = Column(String(50), nullable=False, default="website_chat")
    created_at = Column(DateTime, server_default=func.now())    




class AvaConversation(Base):
    __tablename__ = "ava_conversations"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(100), unique=True, nullable=False)
    intent = Column(String(50), nullable=True)
    current_step = Column(String(50), nullable=True)
    lead_data = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now()
    )



class AvaMessage(Base):
    __tablename__ = "ava_messages"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(
        Integer,
        ForeignKey("ava_conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    sender = Column(String(20), nullable=False)  # user or ava
    message = Column(Text, nullable=False)
    created_at = Column(DateTime, server_default=func.now())



class AvaBusinessFAQ(Base):
    __tablename__ = "ava_business_faqs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    intent = Column(String(50), index=True, nullable=False)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())