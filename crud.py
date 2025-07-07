from sqlalchemy.orm import Session
from models import StaffMember, Student, DisciplineIncident, DisciplinaryAction
from schemas import StaffMemberCreate, StudentCreate, IncidentCreate, DisciplinaryActionCreate

# -------------------- Staff Functions --------------------

def create_staff_member(db: Session, staff: StaffMemberCreate):
    db_staff = StaffMember(
        name=staff.name,
        username=staff.username,
        password=staff.password,
        role=staff.role
    )
    db.add(db_staff)
    db.commit()
    db.refresh(db_staff)
    return db_staff

def get_staff_by_credentials(db: Session, username: str, password: str):
    return db.query(StaffMember).filter(
        StaffMember.username == username,
        StaffMember.password == password
    ).first()

def get_staff_by_id(db: Session, staff_id: int):
    return db.query(StaffMember).filter(StaffMember.id == staff_id).first()

def get_all_staff(db: Session):
    return db.query(StaffMember).all()

def update_staff_member(db: Session, staff_id: int, staff: StaffMemberCreate):
    db_staff = db.query(StaffMember).filter(StaffMember.id == staff_id).first()
    if db_staff:
        db_staff.name = staff.name
        db_staff.username = staff.username
        db_staff.password = staff.password
        db_staff.role = staff.role
        db.commit()
        db.refresh(db_staff)
    return db_staff

def delete_staff_member(db: Session, staff_id: int):
    db_staff = db.query(StaffMember).filter(StaffMember.id == staff_id).first()
    if db_staff:
        db.delete(db_staff)
        db.commit()
        return True
    return False

# -------------------- Student Functions --------------------

def create_student(db: Session, student: StudentCreate):
    db_student = Student(
        name=student.name,
        username=student.username,
        password=student.password
    )
    db.add(db_student)
    db.commit()
    db.refresh(db_student)
    return db_student

def get_student_by_credentials(db: Session, username: str, password: str):
    return db.query(Student).filter(
        Student.username == username,
        Student.password == password
    ).first()

def get_student_by_id(db: Session, student_id: int):
    return db.query(Student).filter(Student.id == student_id).first()

def get_all_students(db: Session):
    return db.query(Student).all()

def update_student(db: Session, student_id: int, student: StudentCreate):
    db_student = db.query(Student).filter(Student.id == student_id).first()
    if db_student:
        db_student.name = student.name
        db_student.username = student.username
        db_student.password = student.password
        db.commit()
        db.refresh(db_student)
    return db_student

def delete_student(db: Session, student_id: int):
    db_student = db.query(Student).filter(Student.id == student_id).first()
    if db_student:
        db.delete(db_student)
        db.commit()
        return True
    return False

# -------------------- Incident Functions --------------------

def create_incident(db: Session, incident: IncidentCreate):
    try:
        db_incident = DisciplineIncident(
            student_id=incident.student_id,
            student_name=incident.student_name,
            class_name=incident.class_name,
            department=incident.department,
            committee_member_id=incident.committee_member_id,
            incident_date=incident.incident_date,
            description=incident.description
        )
        db.add(db_incident)
        db.commit()
        db.refresh(db_incident)
        return db_incident
    except Exception as e:
        db.rollback()
        raise Exception(f"Database error: {str(e)}")

def get_all_incidents(db: Session):
    return db.query(DisciplineIncident).all()

def get_incidents_by_committee_member(db: Session, committee_member_id: int):
    return db.query(DisciplineIncident).filter(
        DisciplineIncident.committee_member_id == committee_member_id
    ).all()

# -------------------- Disciplinary Action Functions --------------------

def create_disciplinary_action(db: Session, action: DisciplinaryActionCreate):
    db_action = DisciplinaryAction(
        incident_id=action.incident_id,
        student_id=action.student_id,
        action_description=action.action_description,
        assigned_date=action.assigned_date
    )
    db.add(db_action)
    db.commit()
    db.refresh(db_action)
    return db_action

def get_actions_by_student_id(db: Session, student_id: str):
    return db.query(DisciplinaryAction).filter(
        DisciplinaryAction.student_id == student_id
    ).all()
