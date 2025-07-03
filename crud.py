from sqlalchemy.orm import Session
import models, schemas

# ─── User (for your existing /users APIs) ────────────────────────────────────────
def create_user(db: Session, user: schemas.UserCreate):
    db_user = models.User(name=user.name, email=user.email)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_users(db: Session):
    return db.query(models.User).all()


# ─── Student ─────────────────────────────────────────────────────────────────────
def create_student(db: Session, student: schemas.StudentCreate):
    db_student = models.Student(
        name=student.name,
        username=student.username,
        password=student.password  # TODO: hash in production
    )
    db.add(db_student)
    db.commit()
    db.refresh(db_student)
    return db_student

def get_student_by_credentials(db: Session, username: str, password: str):
    return (
        db.query(models.Student)
          .filter(
              models.Student.username == username,
              models.Student.password == password
          )
          .first()
    )

def get_student_by_id(db: Session, student_id: int):
    return db.query(models.Student).filter(models.Student.id == student_id).first()


# ─── StaffMember ─────────────────────────────────────────────────────────────────
def create_staff_member(db: Session, staff: schemas.StaffMemberCreate):
    db_obj = models.StaffMember(
        name=staff.name,
        username=staff.username,
        password=staff.password,  # TODO: hash in production
        role=staff.role
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

def get_staff_by_credentials(db: Session, username: str, password: str):
    return (
        db.query(models.StaffMember)
          .filter(
              models.StaffMember.username == username,
              models.StaffMember.password == password
          )
          .first()
    )

def get_staff_by_id(db: Session, staff_id: int):
    return db.query(models.StaffMember).filter(models.StaffMember.id == staff_id).first()
def create_incident(db: Session, incident: schemas.IncidentCreate):
    db_incident = models.DisciplineIncident(**incident.dict())
    db.add(db_incident)
    db.commit()
    db.refresh(db_incident)
    return db_incident

def get_all_incidents(db: Session):
    return db.query(models.DisciplineIncident).all()
