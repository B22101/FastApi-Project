from sqlalchemy import Column, Integer, String, Date
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    email = Column(String, unique=True, index=True)


class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    username = Column(String, unique=True, index=True)
    password = Column(String)


class StaffMember(Base):
    __tablename__ = "staff_members"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)
    role = Column(String, index=True, nullable=False)  # e.g. "principal", "faculty", "committee"


class DisciplineIncident(Base):
    __tablename__ = "discipline_incidents"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(String, index=True)
    student_name = Column(String)
    class_name = Column(String)
    department = Column(String)
    incident_date = Column(Date)
    description = Column(String)
    status = Column(String, default="Pending")
