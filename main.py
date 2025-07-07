from fastapi import FastAPI, Depends, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
import logging

import models
import schemas
import crud
from database import SessionLocal, engine, Base

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

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
    logger.debug(f"Login attempt for username: {username}")
    # Admin login
    if username == "admin" and password == "admin":
        logger.info("Admin login successful")
        return RedirectResponse(url="/admindashboard", status_code=303)

    # Student login
    student = crud.get_student_by_credentials(db, username, password)
    if student:
        logger.info(f"Student login successful: {username}")
        return RedirectResponse(url=f"/studentdashboard?user_id={student.id}", status_code=303)

    # Staff login (principal, faculty, committee)
    staff = crud.get_staff_by_credentials(db, username, password)
    if staff:
        logger.info(f"Staff login successful: {username}, role: {staff.role}")
        return RedirectResponse(
            url=f"/{staff.role}dashboard?user_id={staff.id}", status_code=303
        )

    # Invalid credentials
    logger.warning(f"Invalid login attempt for username: {username}")
    return templates.TemplateResponse(
        "login.html",
        {
            "request": request,
            "error": f"Invalid credentials for username: {username}. Please try again."
        },
        status_code=401
    )

# Logout Route
@app.get("/logout", response_class=RedirectResponse)
def logout(request: Request):
    logger.info("User logged out")
    return RedirectResponse(url="/login", status_code=303)

# 3) Admin Dashboard & CRUD Modules
@app.get("/admindashboard", response_class=HTMLResponse)
def admin_dashboard(request: Request):
    return templates.TemplateResponse("admindashboard.html", {"request": request})

# Staff Members (create, list, update, delete)
@app.get("/staffmembers", response_class=HTMLResponse)
def staffmembers_form(request: Request, db: Session = Depends(get_db)):
    try:
        staff_members = crud.get_all_staff(db)
        return templates.TemplateResponse("staffmembers.html", {
            "request": request,
            "staff_members": staff_members
        })
    except Exception as e:
        logger.error(f"Error fetching staff members: {str(e)}")
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "message": f"Error fetching staff members: {str(e)}"},
            status_code=500
        )

@app.post("/add_staff", response_class=HTMLResponse)
def add_staff(
    request: Request,
    name: str = Form(...),
    username: str = Form(...),
    password: str = Form(...),
    role: str = Form(...),
    db: Session = Depends(get_db)
):
    try:
        crud.create_staff_member(
            db,
            schemas.StaffMemberCreate(name=name, username=username, password=password, role=role)
        )
        logger.info(f"Staff added: {username}, role: {role}")
        return RedirectResponse(url="/staffmembers?message=Staff added successfully", status_code=303)
    except Exception as e:
        logger.error(f"Error adding staff: {str(e)}")
        staff_members = crud.get_all_staff(db)
        return templates.TemplateResponse(
            "staffmembers.html",
            {
                "request": request,
                "error": f"Error adding staff: {str(e)}",
                "staff_members": staff_members
            },
            status_code=400
        )

@app.get("/edit_staff/{staff_id}", response_class=HTMLResponse)
def edit_staff_form(request: Request, staff_id: int, db: Session = Depends(get_db)):
    try:
        staff = crud.get_staff_by_id(db, staff_id)
        if not staff:
            logger.error(f"Staff not found: ID {staff_id}")
            return templates.TemplateResponse(
                "error.html",
                {"request": request, "message": "Staff not found"},
                status_code=404
            )
        return templates.TemplateResponse("edit_staff.html", {
            "request": request,
            "staff": staff
        })
    except Exception as e:
        logger.error(f"Error fetching staff for edit: {str(e)}")
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "message": f"Error: {str(e)}"},
            status_code=500
        )

@app.post("/edit_staff/{staff_id}", response_class=HTMLResponse)
def update_staff(
    request: Request,
    staff_id: int,
    name: str = Form(...),
    username: str = Form(...),
    password: str = Form(...),
    role: str = Form(...),
    db: Session = Depends(get_db)
):
    try:
        updated_staff = crud.update_staff_member(
            db,
            staff_id,
            schemas.StaffMemberCreate(name=name, username=username, password=password, role=role)
        )
        if not updated_staff:
            logger.error(f"Staff not found for update: ID {staff_id}")
            return templates.TemplateResponse(
                "error.html",
                {"request": request, "message": "Staff not found"},
                status_code=404
            )
        logger.info(f"Staff updated: ID {staff_id}")
        return RedirectResponse(url="/staffmembers?message=Staff updated successfully", status_code=303)
    except Exception as e:
        logger.error(f"Error updating staff: {str(e)}")
        staff = crud.get_staff_by_id(db, staff_id)
        return templates.TemplateResponse(
            "edit_staff.html",
            {
                "request": request,
                "error": f"Error updating staff: {str(e)}",
                "staff": staff
            },
            status_code=400
        )

@app.post("/delete_staff/{staff_id}", response_class=HTMLResponse)
def delete_staff(request: Request, staff_id: int, db: Session = Depends(get_db)):
    try:
        success = crud.delete_staff_member(db, staff_id)
        if not success:
            logger.error(f"Staff not found for deletion: ID {staff_id}")
            return templates.TemplateResponse(
                "error.html",
                {"request": request, "message": "Staff not found"},
                status_code=404
            )
        logger.info(f"Staff deleted: ID {staff_id}")
        return RedirectResponse(url="/staffmembers?message=Staff deleted successfully", status_code=303)
    except Exception as e:
        logger.error(f"Error deleting staff: {str(e)}")
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "message": f"Error: {str(e)}"},
            status_code=500
        )

# Students (create, list, update, delete)
@app.get("/students", response_class=HTMLResponse)
def students_form(request: Request, db: Session = Depends(get_db)):
    try:
        students = crud.get_all_students(db)
        return templates.TemplateResponse("students.html", {
            "request": request,
            "students": students
        })
    except Exception as e:
        logger.error(f"Error fetching students: {str(e)}")
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "message": f"Error: {str(e)}"},
            status_code=500
        )

@app.post("/add_student", response_class=HTMLResponse)
def add_student(
    request: Request,
    name: str = Form(...),
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    try:
        crud.create_student(
            db,
            schemas.StudentCreate(name=name, username=username, password=password)
        )
        logger.info(f"Student added: {username}")
        return RedirectResponse(url="/students?message=Student added successfully", status_code=303)
    except Exception as e:
        logger.error(f"Error adding student: {str(e)}")
        students = crud.get_all_students(db)
        return templates.TemplateResponse(
            "students.html",
            {
                "request": request,
                "error": f"Error adding student: {str(e)}",
                "students": students
            },
            status_code=400
        )

@app.get("/edit_student/{student_id}", response_class=HTMLResponse)
def edit_student_form(request: Request, student_id: int, db: Session = Depends(get_db)):
    try:
        student = crud.get_student_by_id(db, student_id)
        if not student:
            logger.error(f"Student not found: ID {student_id}")
            return templates.TemplateResponse(
                "error.html",
                {"request": request, "message": "Student not found"},
                status_code=404
            )
        return templates.TemplateResponse("edit_student.html", {
            "request": request,
            "student": student
        })
    except Exception as e:
        logger.error(f"Error fetching student for edit: {str(e)}")
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "message": f"Error: {str(e)}"},
            status_code=500
        )

@app.post("/edit_student/{student_id}", response_class=HTMLResponse)
def update_student(
    request: Request,
    student_id: int,
    name: str = Form(...),
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    try:
        updated_student = crud.update_student(
            db,
            student_id,
            schemas.StudentCreate(name=name, username=username, password=password)
        )
        if not updated_student:
            logger.error(f"Student not found for update: ID {student_id}")
            return templates.TemplateResponse(
                "error.html",
                {"request": request, "message": "Student not found"},
                status_code=404
            )
        logger.info(f"Student updated: ID {student_id}")
        return RedirectResponse(url="/students?message=Student updated successfully", status_code=303)
    except Exception as e:
        logger.error(f"Error updating student: {str(e)}")
        student = crud.get_student_by_id(db, student_id)
        return templates.TemplateResponse(
            "edit_student.html",
            {
                "request": request,
                "error": f"Error updating student: {str(e)}",
                "student": student
            },
            status_code=400
        )

@app.post("/delete_student/{student_id}", response_class=HTMLResponse)
def delete_student(request: Request, student_id: int, db: Session = Depends(get_db)):
    try:
        success = crud.delete_student(db, student_id)
        if not success:
            logger.error(f"Student not found for deletion: ID {student_id}")
            return templates.TemplateResponse(
                "error.html",
                {"request": request, "message": "Student not found"},
                status_code=404
            )
        logger.info(f"Student deleted: ID {student_id}")
        return RedirectResponse(url="/students?message=Student deleted successfully", status_code=303)
    except Exception as e:
        logger.error(f"Error deleting student: {str(e)}")
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "message": f"Error: {str(e)}"},
            status_code=500
        )

# Static Admin Modules
@app.get("/checkbeststudentawards", response_class=HTMLResponse)
def check_best_student_awards(request: Request):
    return templates.TemplateResponse("checkbeststudentawards.html", {"request": request})

@app.get("/applyscholarship", response_class=HTMLResponse)
def apply_scholarship(request: Request):
    return templates.TemplateResponse("applyscholarship.html", {"request": request})

@app.get("/applybeststudentaward", response_class=HTMLResponse)
def apply_best_student_award(request: Request):
    return templates.TemplateResponse("applybeststudentaward.html", {"request": request})

@app.get("/disciplineincidents", response_class=HTMLResponse)
def discipline_incidents(request: Request, db: Session = Depends(get_db)):
    try:
        incidents = crud.get_all_incidents(db)
        return templates.TemplateResponse("disciplineincidents.html", {
            "request": request,
            "incidents": incidents
        })
    except Exception as e:
        logger.error(f"Error fetching incidents: {str(e)}")
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "message": f"Error: {str(e)}"},
            status_code=500
        )

@app.get("/severitylevels", response_class=HTMLResponse)
def severity_levels(request: Request):
    return templates.TemplateResponse("severitylevels.html", {"request": request})

@app.get("/checkscholarship", response_class=HTMLResponse)
def check_scholarship(request: Request):
    return templates.TemplateResponse("checkscholarship.html", {"request": request})

@app.get("/departments", response_class=HTMLResponse)
def departments(request: Request):
    return templates.TemplateResponse("departments.html", {"request": request})

@app.get("/classes", response_class=HTMLResponse)
def classes(request: Request):
    return templates.TemplateResponse("classes.html", {"request": request})

# 4) Student Dashboard
@app.get("/studentdashboard", response_class=HTMLResponse)
def student_dashboard(request: Request, user_id: int = None, db: Session = Depends(get_db)):
    if not user_id:
        logger.error("No user_id provided for student dashboard")
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "message": "User ID is required. Please log in."},
            status_code=400
        )
    try:
        student = crud.get_student_by_id(db, user_id)
        if not student:
            logger.error(f"Student not found: ID {user_id}")
            return templates.TemplateResponse(
                "error.html",
                {"request": request, "message": "Student not found"},
                status_code=404
            )
        return templates.TemplateResponse("studentdashboard.html", {
            "request": request,
            "student": student
        })
    except Exception as e:
        logger.error(f"Error fetching student dashboard: {str(e)}")
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "message": f"Error: {str(e)}"},
            status_code=500
        )

# Student Routes
@app.get("/sd_disciplineincidents", response_class=HTMLResponse)
def sd_discipline_incidents(request: Request, user_id: int = None, db: Session = Depends(get_db)):
    if not user_id:
        logger.error("No user_id provided for student discipline incidents")
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "message": "User ID is required. Please log in."},
            status_code=400
        )
    try:
        student = crud.get_student_by_id(db, user_id)
        if not student:
            logger.error(f"Student not found: ID {user_id}")
            return templates.TemplateResponse(
                "error.html",
                {"request": request, "message": "Student not found"},
                status_code=404
            )
        incidents = db.query(models.DisciplineIncident).filter(models.DisciplineIncident.student_id == str(student.id)).all()
        return templates.TemplateResponse("sd_disciplineincidents.html", {
            "request": request,
            "incidents": incidents,
            "student": student
        })
    except Exception as e:
        logger.error(f"Error fetching student discipline incidents: {str(e)}")
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "message": f"Error: {str(e)}"},
            status_code=500
        )

@app.get("/sd_viewdisciplineactions", response_class=HTMLResponse)
def sd_view_actions(request: Request, user_id: int = None, db: Session = Depends(get_db)):
    if not user_id:
        logger.error("No user_id provided for student discipline actions")
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "message": "User ID is required. Please log in."},
            status_code=400
        )
    try:
        student = crud.get_student_by_id(db, user_id)
        if not student:
            logger.error(f"Student not found: ID {user_id}")
            return templates.TemplateResponse(
                "error.html",
                {"request": request, "message": "Student not found"},
                status_code=404
            )
        actions = crud.get_actions_by_student_id(db, str(student.id))
        return templates.TemplateResponse("sd_viewdisciplineactions.html", {
            "request": request,
            "actions": actions,
            "student": student
        })
    except Exception as e:
        logger.error(f"Error fetching student discipline actions: {str(e)}")
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "message": f"Error: {str(e)}"},
            status_code=500
        )

@app.get("/sd_applyscholarship", response_class=HTMLResponse)
def sd_apply_scholarship(request: Request, user_id: int = None):
    if not user_id:
        logger.error("No user_id provided for student scholarship application")
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "message": "User ID is required. Please log in."},
            status_code=400
        )
    return templates.TemplateResponse("sd_applyscholarship.html", {"request": request, "user_id": user_id})

@app.get("/sd_applyaward", response_class=HTMLResponse)
def sd_apply_award(request: Request, user_id: int = None):
    if not user_id:
        logger.error("No user_id provided for student award application")
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "message": "User ID is required. Please log in."},
            status_code=400
        )
    return templates.TemplateResponse("sd_applyaward.html", {"request": request, "user_id": user_id})

# 5) Staff Dashboards (Principal, Faculty, Committee)
@app.get("/principaldashboard", response_class=HTMLResponse)
def principal_dashboard(request: Request, user_id: int = None, db: Session = Depends(get_db)):
    if not user_id:
        logger.error("No user_id provided for principal dashboard")
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "message": "User ID is required. Please log in."},
            status_code=400
        )
    try:
        staff = crud.get_staff_by_id(db, user_id)
        if not staff or staff.role != "principal":
            logger.error(f"Unauthorized access to principal dashboard: ID {user_id}, role {staff.role if staff else None}")
            return templates.TemplateResponse(
                "error.html",
                {"request": request, "message": "Unauthorized access"},
                status_code=403
            )
        return templates.TemplateResponse("principaldashboard.html", {
            "request": request,
            "staff": staff
        })
    except Exception as e:
        logger.error(f"Error fetching principal dashboard: {str(e)}")
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "message": f"Error: {str(e)}"},
            status_code=500
        )

@app.get("/facultydashboard", response_class=HTMLResponse)
def faculty_dashboard(request: Request, user_id: int = None, db: Session = Depends(get_db)):
    if not user_id:
        logger.error("No user_id provided for faculty dashboard")
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "message": "User ID is required. Please log in."},
            status_code=400
        )
    try:
        staff = crud.get_staff_by_id(db, user_id)
        if not staff or staff.role != "faculty":
            logger.error(f"Unauthorized access to faculty dashboard: ID {user_id}, role {staff.role if staff else None}")
            return templates.TemplateResponse(
                "error.html",
                {"request": request, "message": "Unauthorized access"},
                status_code=403
            )
        return templates.TemplateResponse("facultydashboard.html", {
            "request": request,
            "staff": staff
        })
    except Exception as e:
        logger.error(f"Error fetching faculty dashboard: {str(e)}")
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "message": f"Error: {str(e)}"},
            status_code=500
        )

@app.get("/committeedashboard", response_class=HTMLResponse)
def committee_dashboard(request: Request, user_id: int = None, db: Session = Depends(get_db)):
    if not user_id:
        logger.error("No user_id provided for committee dashboard")
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "message": "User ID is required. Please log in."},
            status_code=400
        )
    try:
        staff = crud.get_staff_by_id(db, user_id)
        if not staff or staff.role != "committee":
            logger.error(f"Unauthorized access to committee dashboard: ID {user_id}, role {staff.role if staff else None}")
            return templates.TemplateResponse(
                "error.html",
                {"request": request, "message": "Unauthorized access"},
                status_code=403
            )
        return templates.TemplateResponse("committeedashboard.html", {
            "request": request,
            "staff": staff,
            "message": request.query_params.get("message")
        })
    except Exception as e:
        logger.error(f"Error fetching committee dashboard: {str(e)}")
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "message": f"Error: {str(e)}"},
            status_code=500
        )

# Faculty Routes
@app.get("/fd_disciplineincidents", response_class=HTMLResponse)
def fd_discipline_incidents(request: Request, user_id: int = None, db: Session = Depends(get_db)):
    if not user_id:
        logger.error("No user_id provided for faculty discipline incidents")
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "message": "User ID is required. Please log in."},
            status_code=400
        )
    try:
        staff = crud.get_staff_by_id(db, user_id)
        if not staff or staff.role != "faculty":
            logger.error(f"Unauthorized access to faculty discipline incidents: ID {user_id}, role {staff.role if staff else None}")
            return templates.TemplateResponse(
                "error.html",
                {"request": request, "message": "Unauthorized access"},
                status_code=403
            )
        students = crud.get_all_students(db)
        committee_members = db.query(models.StaffMember).filter(models.StaffMember.role == "committee").all()
        return templates.TemplateResponse("fd_disciplineincidents.html", {
            "request": request,
            "students": students,
            "committee_members": committee_members,
            "staff": staff,
            "message": request.query_params.get("message"),
            "form_data": {}
        })
    except Exception as e:
        logger.error(f"Error fetching faculty discipline incidents: {str(e)}")
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "message": f"Error: {str(e)}"},
            status_code=500
        )

@app.post("/fd_submit_incident", response_class=HTMLResponse)
def fd_submit_incident(
    request: Request,
    student_id: str = Form(...),
    student_name: str = Form(...),
    class_name: str = Form(...),
    department: str = Form(...),
    committee_member_id: str = Form(...),  # Changed to str to avoid type mismatch
    incident_date: str = Form(...),
    description: str = Form(...),
    user_id: int = Form(None),
    db: Session = Depends(get_db)
):
    if not user_id:
        logger.error("No user_id provided for faculty incident submission")
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "message": "User ID is required. Please log in."},
            status_code=400
        )
    try:
        # Verify faculty role
        staff = crud.get_staff_by_id(db, user_id)
        if not staff or staff.role != "faculty":
            logger.error(f"Unauthorized access to faculty incident submission: ID {user_id}, role {staff.role if staff else None}")
            return templates.TemplateResponse(
                "error.html",
                {"request": request, "message": "Unauthorized access"},
                status_code=403
            )
        # Validate committee_member_id
        committee_member_id_int = int(committee_member_id) if committee_member_id else None
        if committee_member_id_int:
            committee_member = db.query(models.StaffMember).filter(
                models.StaffMember.id == committee_member_id_int,
                models.StaffMember.role == "committee"
            ).first()
            if not committee_member:
                raise ValueError(f"Invalid committee member ID: {committee_member_id}")
        # Create incident
        incident_data = schemas.IncidentCreate(
            student_id=student_id,
            student_name=student_name,
            class_name=class_name,
            department=department,
            committee_member_id=committee_member_id_int,
            incident_date=incident_date,
            description=description
        )
        logger.debug(f"Incident data: {incident_data}")
        crud.create_incident(db, incident_data)
        logger.info(f"Incident reported by user_id: {user_id}")
        return RedirectResponse(url=f"/fd_disciplineincidents?user_id={user_id}&message=Incident reported successfully", status_code=303)
    except ValueError as ve:
        logger.error(f"Validation error: {str(ve)}")
        students = crud.get_all_students(db)
        committee_members = db.query(models.StaffMember).filter(models.StaffMember.role == "committee").all()
        form_data = {
            "student_id": student_id,
            "student_name": student_name,
            "class_name": class_name,
            "department": department,
            "committee_member_id": committee_member_id,
            "incident_date": incident_date,
            "description": description
        }
        return templates.TemplateResponse(
            "fd_disciplineincidents.html",
            {
                "request": request,
                "error": f"Validation error: {str(ve)}",
                "students": students,
                "committee_members": committee_members,
                "staff": staff,
                "form_data": form_data
            },
            status_code=400
        )
    except Exception as e:
        logger.error(f"Error reporting incident: {str(e)}")
        students = crud.get_all_students(db)
        committee_members = db.query(models.StaffMember).filter(models.StaffMember.role == "committee").all()
        form_data = {
            "student_id": student_id,
            "student_name": student_name,
            "class_name": class_name,
            "department": department,
            "committee_member_id": committee_member_id,
            "incident_date": incident_date,
            "description": description
        }
        return templates.TemplateResponse(
            "fd_disciplineincidents.html",
            {
                "request": request,
                "error": f"Error reporting incident: {str(e)}",
                "students": students,
                "committee_members": committee_members,
                "staff": staff,
                "form_data": form_data
            },
            status_code=500
        )

@app.get("/fd_applybeststudentaward", response_class=HTMLResponse)
def fd_best_award(request: Request, user_id: int = None):
    if not user_id:
        logger.error("No user_id provided for faculty award application")
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "message": "User ID is required. Please log in."},
            status_code=400
        )
    return templates.TemplateResponse("fd_applybeststudentaward.html", {
        "request": request,
        "user_id": user_id
    })

@app.get("/fd_applyscholarship", response_class=HTMLResponse)
def fd_scholarship(request: Request, user_id: int = None):
    if not user_id:
        logger.error("No user_id provided for faculty scholarship application")
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "message": "User ID is required. Please log in."},
            status_code=400
        )
    return templates.TemplateResponse("fd_applyscholarship.html", {
        "request": request,
        "user_id": user_id
    })

# Committee Routes
@app.get("/cd_disciplineincidents", response_class=HTMLResponse)
def cd_view_incidents(request: Request, user_id: int = None, db: Session = Depends(get_db)):
    if not user_id:
        logger.error("No user_id provided for committee discipline incidents")
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "message": "User ID is required. Please log in."},
            status_code=400
        )
    try:
        staff = crud.get_staff_by_id(db, user_id)
        if not staff or staff.role != "committee":
            logger.error(f"Unauthorized access to committee discipline incidents: ID {user_id}, role {staff.role if staff else None}")
            return templates.TemplateResponse(
                "error.html",
                {"request": request, "message": "Unauthorized access"},
                status_code=403
            )
        incidents = crud.get_incidents_by_committee_member(db, user_id)
        logger.debug(f"Fetched {len(incidents)} incidents for committee member ID {user_id}")
        return templates.TemplateResponse("cd_disciplineincidents.html", {
            "request": request,
            "incidents": incidents,
            "staff": staff,
            "message": request.query_params.get("message"),
            "error": request.query_params.get("error")
        })
    except Exception as e:
        logger.error(f"Error fetching committee discipline incidents: {str(e)}")
        return templates.TemplateResponse(
            "cd_disciplineincidents.html",
            {
                "request": request,
                "error": f"No incidents assigned to you: {str(e)}",
                "incidents": [],
                "staff": crud.get_staff_by_id(db, user_id)
            },
            status_code=200
        )

@app.post("/cd_assign_action", response_class=HTMLResponse)
def cd_assign_action(
    request: Request,
    incident_id: int = Form(...),
    student_id: str = Form(...),
    action_description: str = Form(...),
    assigned_date: str = Form(...),
    user_id: int = Form(None),
    db: Session = Depends(get_db)
):
    if not user_id:
        logger.error("No user_id provided for assigning action")
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "message": "User ID is required. Please log in."},
            status_code=400
        )
    try:
        action_data = schemas.DisciplinaryActionCreate(
            incident_id=incident_id,
            student_id=student_id,
            action_description=action_description,
            assigned_date=assigned_date
        )
        crud.create_disciplinary_action(db, action_data)
        logger.info(f"Action assigned for incident ID {incident_id} by user_id: {user_id}")
        return RedirectResponse(url=f"/cd_disciplineincidents?user_id={user_id}&message=Action assigned successfully", status_code=303)
    except Exception as e:
        logger.error(f"Error assigning action: {str(e)}")
        incidents = crud.get_incidents_by_committee_member(db, user_id)
        return templates.TemplateResponse(
            "cd_disciplineincidents.html",
            {
                "request": request,
                "error": f"Error assigning action: {str(e)}",
                "incidents": incidents,
                "staff": crud.get_staff_by_id(db, user_id)
            },
            status_code=400
        )

@app.get("/cd_assignactions", response_class=HTMLResponse)
def cd_assign_actions(request: Request, user_id: int = None, db: Session = Depends(get_db)):
    if not user_id:
        logger.error("No user_id provided for assign actions")
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "message": "User ID is required. Please log in."},
            status_code=400
        )
    try:
        staff = crud.get_staff_by_id(db, user_id)
        if not staff or staff.role != "committee":
            logger.error(f"Unauthorized access to assign actions: ID {user_id}, role {staff.role if staff else None}")
            return templates.TemplateResponse(
                "error.html",
                {"request": request, "message": "Unauthorized access"},
                status_code=403
            )
        incidents = crud.get_incidents_by_committee_member(db, user_id)
        logger.debug(f"Fetched {len(incidents)} incidents for assign actions by user_id: {user_id}")
        return templates.TemplateResponse("cd_assignactions.html", {
            "request": request,
            "incidents": incidents,
            "staff": staff,
            "message": request.query_params.get("message"),
            "error": request.query_params.get("error")
        })
    except Exception as e:
        logger.error(f"Error fetching assign actions page: {str(e)}")
        return templates.TemplateResponse(
            "cd_assignactions.html",
            {
                "request": request,
                "error": f"No incidents assigned to you: {str(e)}",
                "incidents": [],
                "staff": crud.get_staff_by_id(db, user_id)
            },
            status_code=200
        )

@app.post("/cd_assignactions", response_class=HTMLResponse)
def cd_submit_action(
    request: Request,
    incident_id: int = Form(...),
    student_id: str = Form(...),
    action_description: str = Form(...),
    assigned_date: str = Form(...),
    user_id: int = Form(None),
    db: Session = Depends(get_db)
):
    if not user_id:
        logger.error("No user_id provided for submitting action")
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "message": "User ID is required. Please log in."},
            status_code=400
        )
    try:
        action_data = schemas.DisciplinaryActionCreate(
            incident_id=incident_id,
            student_id=student_id,
            action_description=action_description,
            assigned_date=assigned_date
        )
        crud.create_disciplinary_action(db, action_data)
        logger.info(f"Action assigned for incident ID {incident_id} by user_id: {user_id}")
        return RedirectResponse(url=f"/cd_assignactions?user_id={user_id}&message=Action assigned successfully", status_code=303)
    except Exception as e:
        logger.error(f"Error submitting action: {str(e)}")
        incidents = crud.get_incidents_by_committee_member(db, user_id)
        return templates.TemplateResponse(
            "cd_assignactions.html",
            {
                "request": request,
                "error": f"Error assigning action: {str(e)}",
                "incidents": incidents,
                "staff": crud.get_staff_by_id(db, user_id)
            },
            status_code=400
        )

@app.get("/cd_disciplineactions", response_class=HTMLResponse)
def cd_discipline_actions(request: Request, user_id: int = None, db: Session = Depends(get_db)):
    if not user_id:
        logger.error("No user_id provided for discipline actions")
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "message": "User ID is required. Please log in."},
            status_code=400
        )
    try:
        staff = crud.get_staff_by_id(db, user_id)
        if not staff or staff.role != "committee":
            logger.error(f"Unauthorized access to discipline actions: ID {user_id}, role {staff.role if staff else None}")
            return templates.TemplateResponse(
                "error.html",
                {"request": request, "message": "Unauthorized access"},
                status_code=403
            )
        actions = db.query(models.DisciplinaryAction).all()
        logger.debug(f"Fetched {len(actions)} disciplinary actions for user_id: {user_id}")
        return templates.TemplateResponse("cd_disciplineactions.html", {
            "request": request,
            "actions": actions,
            "staff": staff,
            "message": request.query_params.get("message"),
            "error": request.query_params.get("error")
        })
    except Exception as e:
        logger.error(f"Error fetching discipline actions: {str(e)}")
        return templates.TemplateResponse(
            "cd_disciplineactions.html",
            {
                "request": request,
                "error": f"No disciplinary actions available: {str(e)}",
                "actions": [],
                "staff": crud.get_staff_by_id(db, user_id)
            },
            status_code=200
        )

# Principal Routes
@app.get("/pd_checkbeststudentawards", response_class=HTMLResponse)
def pd_best_awards(request: Request, user_id: int = None):
    if not user_id:
        logger.error("No user_id provided for principal best student awards")
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "message": "User ID is required. Please log in."},
            status_code=400
        )
    return templates.TemplateResponse("pd_checkbeststudentawards.html", {
        "request": request,
        "nominations": [],
        "user_id": user_id
    })

@app.get("/pd_disciplineactions", response_class=HTMLResponse)
def pd_discipline_actions(request: Request, user_id: int = None, db: Session = Depends(get_db)):
    if not user_id:
        logger.error("No user_id provided for principal discipline actions")
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "message": "User ID is required. Please log in."},
            status_code=400
        )
    try:
        staff = crud.get_staff_by_id(db, user_id)
        if not staff or staff.role != "principal":
            logger.error(f"Unauthorized access to principal discipline actions: ID {user_id}, role {staff.role if staff else None}")
            return templates.TemplateResponse(
                "error.html",
                {"request": request, "message": "Unauthorized access"},
                status_code=403
            )
        actions = db.query(models.DisciplinaryAction).all()
        return templates.TemplateResponse("pd_disciplineactions.html", {
            "request": request,
            "actions": actions,
            "staff": staff
        })
    except Exception as e:
        logger.error(f"Error fetching principal discipline actions: {str(e)}")
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "message": f"Error: {str(e)}"},
            status_code=500
        )

@app.get("/pd_checkscholarship", response_class=HTMLResponse)
def pd_check_scholarship(request: Request, user_id: int = None):
    if not user_id:
        logger.error("No user_id provided for principal scholarship check")
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "message": "User ID is required. Please log in."},
            status_code=400
        )
    return templates.TemplateResponse("pd_checkscholarship.html", {
        "request": request,
        "scholarships": [],
        "user_id": user_id
    })