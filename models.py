from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class StaffMember(Base):
    __tablename__ = "staff_members"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    username = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    role = Column(String, nullable=False)

class Student(Base):
    __tablename__ = "students"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    username = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)

class DisciplineIncident(Base):
    __tablename__ = "discipline_incidents"
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(String, nullable=False)
    student_name = Column(String, nullable=False)
    class_name = Column(String, nullable=False)
    department = Column(String, nullable=False)
    committee_member_id = Column(Integer, ForeignKey("staff_members.id"), nullable=True)
    incident_date = Column(String, nullable=False)
    description = Column(Text, nullable=False)

class DisciplinaryAction(Base):
    __tablename__ = "disciplinary_actions"
    id = Column(Integer, primary_key=True, index=True)
    incident_id = Column(Integer, ForeignKey("discipline_incidents.id"), nullable=False)
    student_id = Column(String, nullable=False)
    action_description = Column(Text, nullable=False)
    assigned_date = Column(String, nullable=False)
