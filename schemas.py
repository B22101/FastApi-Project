from pydantic import BaseModel

class StaffMemberCreate(BaseModel):
       name: str
       username: str
       password: str
       role: str

class StudentCreate(BaseModel):
       name: str
       username: str
       password: str
class IncidentCreate(BaseModel):
       student_id: str
       student_name: str
       class_name: str
       department: str
       committee_member_id: int | None
       incident_date: str
       description: str

class DisciplinaryActionCreate(BaseModel):
       incident_id: int
       student_id: str
       action_description: str
       assigned_date: str