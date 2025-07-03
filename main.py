
from fastapi import FastAPI, Depends, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

import models
import schemas
import crud
from database import SessionLocal, engine, Base

# Create all database tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 1) Home & Login Pages
@app.get("/", response_class=HTMLResponse)
def show_home(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})

@app.get("/login", response_class=HTMLResponse)
def show_login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

# 2) Login Handler (Admin / Student / Staff)
@app.post("/login", response_class=HTMLResponse)
def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    # Admin login (assign a dummy user_id for admin, e.g., 0)
    if username == "admin" and password == "admin":
        return RedirectResponse(url="/admindashboard?user_id=0", status_code=303)

    # Student login
    student = crud.get_student_by_credentials(db, username, password)
    if student:
        return RedirectResponse(url=f"/studentdashboard?user_id={student.id}", status_code=303)

    # Staff login (principal, faculty, committee)
    staff = crud.get_staff_by_credentials(db, username, password)
    if staff:
        return RedirectResponse(
            url=f"/{staff.role}dashboard?user_id={staff.id}", status_code=303
        )

    # Invalid credentials
    return templates.TemplateResponse(
        "login.html",
        {"request": request, "error": "Invalid credentials"},
        status_code=401
    )

# 3) Admin Dashboard & CRUD Modules
@app.get("/admindashboard", response_class=HTMLResponse)
def admin_dashboard(request: Request, user_id: int, db: Session = Depends(get_db)):
    incidents = crud.get_all_incidents(db)
    return templates.TemplateResponse("admindashboard.html", {"request": request, "incidents": incidents, "user_id": user_id})

# Staff Members (create Principal/Faculty/Committee)
@app.get("/staffmembers", response_class=HTMLResponse)
def staffmembers_form(request: Request, db: Session = Depends(get_db)):
    staff_members = db.query(models.StaffMember).all()
    return templates.TemplateResponse("staffmembers.html", {"request": request, "staff_members": staff_members, "message": None})

@app.post("/add_staff", response_class=HTMLResponse)
def add_staff(
    request: Request,
    name: str = Form(...),
    username: str = Form(...),
    password: str = Form(...),
    role: str = Form(...),
    db: Session = Depends(get_db)
):
    crud.create_staff_member(
        db,
        schemas.StaffMemberCreate(name=name, username=username, password=password, role=role)
    )
    staff_members = db.query(models.StaffMember).all()
    return templates.TemplateResponse(
        "staffmembers.html",
        {"request": request, "staff_members": staff_members, "message": f"{role.title()} added successfully!"}
    )

@app.get("/edit_staff/{staff_id}", response_class=HTMLResponse)
def edit_staff(request: Request, staff_id: int, db: Session = Depends(get_db)):
    staff = db.query(models.StaffMember).filter(models.StaffMember.id == staff_id).first()
    if not staff:
        return templates.TemplateResponse("error.html", {"request": request, "message": "Staff not found"}, status_code=404)
    return templates.TemplateResponse("edit_staff.html", {"request": request, "staff": staff})

@app.post("/update_staff/{staff_id}", response_class=HTMLResponse)
def update_staff(
    request: Request,
    staff_id: int,
    name: str = Form(...),
    username: str = Form(...),
    password: str = Form(...),
    role: str = Form(...),
    db: Session = Depends(get_db)
):
    staff = db.query(models.StaffMember).filter(models.StaffMember.id == staff_id).first()
    if staff:
        staff.name = name
        staff.username = username
        staff.password = password
        staff.role = role
        db.commit()
    staff_members = db.query(models.StaffMember).all()
    return templates.TemplateResponse(
        "staffmembers.html",
        {"request": request, "staff_members": staff_members, "message": "Staff updated successfully!"}
    )

@app.post("/delete_staff/{staff_id}", response_class=HTMLResponse)
def delete_staff(request: Request, staff_id: int, db: Session = Depends(get_db)):
    staff = db.query(models.StaffMember).filter(models.StaffMember.id == staff_id).first()
    if staff:
        db.delete(staff)
        db.commit()
    staff_members = db.query(models.StaffMember).all()
    return templates.TemplateResponse(
        "staffmembers.html",
        {"request": request, "staff_members": staff_members, "message": "Staff deleted successfully!"}
    )

# Students (create student accounts)
@app.get("/students", response_class=HTMLResponse)
def students_form(request: Request, db: Session = Depends(get_db)):
    students = db.query(models.Student).all()
    return templates.TemplateResponse("students.html", {"request": request, "students": students, "message": None})

@app.post("/add_student", response_class=HTMLResponse)
def add_student(
    request: Request,
    name: str = Form(...),
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    crud.create_student(
        db,
        schemas.StudentCreate(name=name, username=username, password=password)
    )
    students = db.query(models.Student).all()
    return templates.TemplateResponse(
        "students.html",
        {"request": request, "students": students, "message": "Student added successfully!"}
    )

@app.get("/edit_student/{student_id}", response_class=HTMLResponse)
def edit_student(request: Request, student_id: int, db: Session = Depends(get_db)):
    student = db.query(models.Student).filter(models.Student.id == student_id).first()
    if not student:
        return templates.TemplateResponse("error.html", {"request": request, "message": "Student not found"}, status_code=404)
    return templates.TemplateResponse("edit_student.html", {"request": request, "student": student})

@app.post("/update_student/{student_id}", response_class=HTMLResponse)
def update_student(
    request: Request,
    student_id: int,
    name: str = Form(...),
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    student = db.query(models.Student).filter(models.Student.id == student_id).first()
    if student:
        student.name = name
        student.username = username
        student.password = password
        db.commit()
    students = db.query(models.Student).all()
    return templates.TemplateResponse(
        "students.html",
        {"request": request, "students": students, "message": "Student updated successfully!"}
    )

@app.post("/delete_student/{student_id}", response_class=HTMLResponse)
def delete_student(request: Request, student_id: int, db: Session = Depends(get_db)):
    student = db.query(models.Student).filter(models.Student.id == student_id).first()
    if student:
        db.delete(student)
        db.commit()
    students = db.query(models.Student).all()
    return templates.TemplateResponse(
        "students.html",
        {"request": request, "students": students, "message": "Student deleted successfully!"}
    )

# Static Admin Modules
@app.get("/checkbeststudentawards", response_class=HTMLResponse)
def check_best_student_awards(request: Request, db: Session = Depends(get_db)):
    # Placeholder logic for awards
    return templates.TemplateResponse("checkbeststudentawards.html", {"request": request})

@app.get("/applyscholarship", response_class=HTMLResponse)
def apply_scholarship(request: Request):
    return templates.TemplateResponse("applyscholarship.html", {"request": request})

@app.get("/applybeststudentaward", response_class=HTMLResponse)
def apply_best_student_award(request: Request):
    return templates.TemplateResponse("applybeststudentaward.html", {"request": request})

@app.get("/disciplineactions", response_class=HTMLResponse)
def discipline_actions(request: Request, db: Session = Depends(get_db)):
    incidents = crud.get_all_incidents(db)
    return templates.TemplateResponse("disciplineactions.html", {"request": request, "incidents": incidents})

@app.get("/assignactions", response_class=HTMLResponse)
def assign_actions(request: Request, db: Session = Depends(get_db)):
    incidents = crud.get_all_incidents(db)
    return templates.TemplateResponse("assignactions.html", {"request": request, "incidents": incidents})

@app.get("/disciplineincidents", response_class=HTMLResponse)
def view_incidents(request: Request, db: Session = Depends(get_db)):
    incidents = crud.get_all_incidents(db)
    return templates.TemplateResponse("disciplineincidents.html", {"request": request, "incidents": incidents})

@app.post("/update_incident_status", response_class=HTMLResponse)
def update_incident_status(
    request: Request,
    incident_id: int = Form(...),
    status: str = Form(...),
    db: Session = Depends(get_db)
):
    incident = db.query(models.DisciplineIncident).filter(models.DisciplineIncident.id == incident_id).first()
    if incident:
        incident.status = status
        db.commit()
    return RedirectResponse(url="/disciplineincidents", status_code=303)

@app.get("/severitylevels", response_class=HTMLResponse)
def severity_levels(request: Request):
    return templates.TemplateResponse("severitylevels.html", {"request": request})

@app.get("/checkscholarship", response_class=HTMLResponse)
def check_scholarship(request: Request, db: Session = Depends(get_db)):
    # Placeholder logic for scholarships
    return templates.TemplateResponse("checkscholarship.html", {"request": request})

@app.get("/departments", response_class=HTMLResponse)
def departments(request: Request):
    return templates.TemplateResponse("departments.html", {"request": request})

@app.get("/classes", response_class=HTMLResponse)
def classes(request: Request):
    return templates.TemplateResponse("classes.html", {"request": request})

# 4) Student Dashboard
@app.get("/studentdashboard", response_class=HTMLResponse)
def student_dashboard(request: Request, user_id: int, db: Session = Depends(get_db)):
    student = crud.get_student_by_id(db, user_id)
    if not student:
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "message": "Student not found"},
            status_code=404
        )
    incidents = db.query(models.DisciplineIncident).filter(models.DisciplineIncident.student_id == str(user_id)).all()
    return templates.TemplateResponse("studentdashboard.html", {
        "request": request,
        "student": student,
        "incidents": incidents
    })

# 5) Staff Dashboards (Principal, Faculty, Committee)
@app.get("/principaldashboard", response_class=HTMLResponse)
def principal_dashboard(request: Request, user_id: int, db: Session = Depends(get_db)):
    staff = crud.get_staff_by_id(db, user_id)
    if not staff:
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "message": "Staff not found"},
            status_code=404
        )
    incidents = crud.get_all_incidents(db)
    return templates.TemplateResponse("principaldashboard.html", {
        "request": request,
        "staff": staff,
        "incidents": incidents
    })

@app.get("/facultydashboard", response_class=HTMLResponse)
def faculty_dashboard(request: Request, user_id: int, db: Session = Depends(get_db)):
    staff = crud.get_staff_by_id(db, user_id)
    if not staff:
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "message": "Staff not found"},
            status_code=404
        )
    incidents = crud.get_all_incidents(db)
    return templates.TemplateResponse("facultydashboard.html", {
        "request": request,
        "staff": staff,
        "incidents": incidents
    })

@app.get("/committeedashboard", response_class=HTMLResponse)
def committee_dashboard(request: Request, user_id: int, db: Session = Depends(get_db)):
    staff = crud.get_staff_by_id(db, user_id)
    if not staff:
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "message": "Staff not found"},
            status_code=404
        )
    incidents = crud.get_all_incidents(db)
    return templates.TemplateResponse("committeedashboard.html", {
        "request": request,
        "staff": staff,
        "incidents": incidents
    })

# Student Routes
@app.get("/sd_disciplineincidents", response_class=HTMLResponse)
def sd_discipline_incidents(request: Request, user_id: int, db: Session = Depends(get_db)):
    student = crud.get_student_by_id(db, user_id)
    if not student:
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "message": "Student not found"},
            status_code=404
        )
    incidents = db.query(models.DisciplineIncident).filter(models.DisciplineIncident.student_id == str(user_id)).all()
    return templates.TemplateResponse("sd_disciplineincidents.html", {
        "request": request,
        "incidents": incidents,
        "student": student
    })

@app.get("/sd_viewdisciplineactions", response_class=HTMLResponse)
def sd_view_actions(request: Request, user_id: int, db: Session = Depends(get_db)):
    student = crud.get_student_by_id(db, user_id)
    if not student:
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "message": "Student not found"},
            status_code=404
        )
    incidents = db.query(models.DisciplineIncident).filter(models.DisciplineIncident.student_id == str(user_id)).all()
    return templates.TemplateResponse("sd_viewdisciplineactions.html", {
        "request": request,
        "actions": incidents,
        "student": student
    })

@app.get("/sd_applyscholarship", response_class=HTMLResponse)
def sd_apply_scholarship(request: Request, user_id: int):
    return templates.TemplateResponse("sd_applyscholarship.html", {"request": request, "user_id": user_id})

@app.get("/sd_applyaward", response_class=HTMLResponse)
def sd_apply_award(request: Request, user_id: int):
    return templates.TemplateResponse("sd_applyaward.html", {"request": request, "user_id": user_id})

# Faculty Routes
@app.get("/fd_disciplineincidents", response_class=HTMLResponse)
def fd_discipline_incidents(request: Request, user_id: int, db: Session = Depends(get_db)):
    staff = crud.get_staff_by_id(db, user_id)
    if not staff:
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "message": "Staff not found"},
            status_code=404
        )
    incidents = crud.get_all_incidents(db)
    return templates.TemplateResponse("fd_disciplineincidents.html", {
        "request": request,
        "incidents": incidents,
        "staff": staff
    })

@app.post("/fd_submit_incident", response_class=HTMLResponse)
def fd_submit_incident(
    request: Request,
    student_id: str = Form(...),
    student_name: str = Form(...),
    class_name: str = Form(...),
    department: str = Form(...),
    incident_date: str = Form(...),
    description: str = Form(...),
    db: Session = Depends(get_db)
):
    incident_data = schemas.IncidentCreate(
        student_id=student_id,
        student_name=student_name,
        class_name=class_name,
        department=department,
        incident_date=incident_date,
        description=description
    )
    crud.create_incident(db, incident_data)
    return RedirectResponse(url="/fd_disciplineincidents", status_code=303)

@app.get("/fd_applybeststudentaward", response_class=HTMLResponse)
def fd_best_award(request: Request, user_id: int):
    return templates.TemplateResponse("fd_applybeststudentaward.html", {"request": request, "user_id": user_id})

@app.get("/fd_applyscholarship", response_class=HTMLResponse)
def fd_scholarship(request: Request, user_id: int):
    return templates.TemplateResponse("fd_applyscholarship.html", {"request": request, "user_id": user_id})

# Committee Routes
@app.get("/cd_disciplineincidents", response_class=HTMLResponse)
def cd_view_incidents(request: Request, user_id: int, db: Session = Depends(get_db)):
    staff = crud.get_staff_by_id(db, user_id)
    if not staff:
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "message": "Staff not found"},
            status_code=404
        )
    incidents = crud.get_all_incidents(db)
    return templates.TemplateResponse("cd_disciplineincidents.html", {
        "request": request,
        "incidents": incidents,
        "staff": staff
    })

@app.get("/cd_assignactions", response_class=HTMLResponse)
def cd_assign_actions(request: Request, user_id: int, db: Session = Depends(get_db)):
    staff = crud.get_staff_by_id(db, user_id)
    if not staff:
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "message": "Staff not found"},
            status_code=404
        )
    incidents = crud.get_all_incidents(db)
    return templates.TemplateResponse("cd_assignactions.html", {
        "request": request,
        "incidents": incidents,
        "staff": staff
    })

@app.post("/assign_action", response_class=HTMLResponse)
def assign_action(
    request: Request,
    incident_id: int = Form(...),
    action: str = Form(...),
    db: Session = Depends(get_db)
):
    incident = db.query(models.DisciplineIncident).filter(models.DisciplineIncident.id == incident_id).first()
    if incident:
        incident.status = "Action Assigned: " + action
        db.commit()
    return RedirectResponse(url="/cd_assignactions", status_code=303)

@app.get("/cd_disciplineactions", response_class=HTMLResponse)
def cd_manage_actions(request: Request, user_id: int, db: Session = Depends(get_db)):
    staff = crud.get_staff_by_id(db, user_id)
    if not staff:
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "message": "Staff not found"},
            status_code=404
        )
    incidents = db.query(models.DisciplineIncident).filter(models.DisciplineIncident.status.contains("Action Assigned")).all()
    return templates.TemplateResponse("cd_disciplineactions.html", {
        "request": request,
        "actions": incidents,
        "staff": staff
    })

# Principal Routes
@app.get("/pd_checkbeststudentawards", response_class=HTMLResponse)
def pd_best_awards(request: Request, user_id: int, db: Session = Depends(get_db)):
    staff = crud.get_staff_by_id(db, user_id)
    if not staff:
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "message": "Staff not found"},
            status_code=404
        )
    # Placeholder logic for awards
    return templates.TemplateResponse("pd_checkbeststudentawards.html", {
        "request": request,
        "nominations": [],
        "staff": staff
    })

@app.get("/pd_disciplineactions", response_class=HTMLResponse)
def pd_discipline_actions(request: Request, user_id: int, db: Session = Depends(get_db)):
    staff = crud.get_staff_by_id(db, user_id)
    if not staff:
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "message": "Staff not found"},
            status_code=404
        )
    incidents = db.query(models.DisciplineIncident).filter(models.DisciplineIncident.status.contains("Action Assigned")).all()
    return templates.TemplateResponse("pd_disciplineactions.html", {
        "request": request,
        "actions": incidents,
        "staff": staff
    })

@app.get("/pd_checkscholarship", response_class=HTMLResponse)
def pd_check_scholarship(request: Request, user_id: int, db: Session = Depends(get_db)):
    staff = crud.get_staff_by_id(db, user_id)
    if not staff:
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "message": "Staff not found"},
            status_code=404
        )
    # Placeholder logic for scholarships
    return templates.TemplateResponse("pd_checkscholarship.html", {
        "request": request,
        "scholarships": [],
        "staff": staff
    })