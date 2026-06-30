import uuid
from sqlalchemy import Column, String, DateTime, Enum, BigInteger, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    encryption_pub_key = Column(String(1024))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    sessions = relationship("Session", back_populates="owner")

class Session(Base):
    __tablename__ = "sessions"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"))
    project_name = Column(String(255), nullable=False)
    sync_mode = Column(String(50), default="local")
    latest_snapshot_hash = Column(String(256))
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    owner = relationship("User", back_populates="sessions")
    snapshots = relationship("CloudSnapshot", back_populates="session")

class CloudSnapshot(Base):
    __tablename__ = "cloud_snapshots"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String(36), ForeignKey("sessions.id"))
    s3_object_key = Column(String(1024), nullable=False)
    size_bytes = Column(BigInteger, nullable=False)
    is_baseline = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    session = relationship("Session", back_populates="snapshots")
