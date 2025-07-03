from pydantic import BaseModel
from datetime import date
class UserCreate(BaseModel):
    name: str
    email: str

class User(UserCreate):
    id: int

class Config:
        from_attributes = True
class StudentBase(BaseModel):
    name: str
    username: str

class StudentCreate(StudentBase):
    password: str

class Student(StudentBase):
    id: int

    class Config:
        orm_mode = True
class StaffMemberBase(BaseModel):
    name: str
    username: str
    role: str

class StaffMemberCreate(StaffMemberBase):
    password: str

class StaffMember(StaffMemberBase):
    id: int

    class Config:
        orm_mode = True        

class IncidentCreate(BaseModel):
    student_id: str
    student_name: str
    class_name: str
    department: str
    incident_date: date
    description: str

class Incident(IncidentCreate):
    id: int
    status: str

    class Config:
        orm_mode = True
        