from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.database.base import Base

class KeystrokeFeatureModel(Base):
    __tablename__ = "keystroke_features"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(36), ForeignKey("sessions.id"), nullable=False, index=True)
    sequence_index = Column(Integer, nullable=False)
    dwell_time = Column(Float, nullable=False)
    flight_time = Column(Float, nullable=True) # nullable for first event
    press_to_press_latency = Column(Float, nullable=True) # nullable for first event
    is_backspace = Column(Boolean, nullable=False, default=False)
    is_pause = Column(Boolean, nullable=False, default=False)

    session = relationship("SessionModel", back_populates="keystrokes")
