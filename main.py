import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from bson import ObjectId
from datetime import datetime

from database import db, create_document, get_documents
from schemas import Department, Employee, LeaveRequest, Attendance

app = FastAPI(title="HRMS Portal API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "HRMS Portal Backend is running"}

@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }

    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"

    return response

# ------------------------------
# Utility
# ------------------------------

def to_object_id(id_str: str) -> ObjectId:
    try:
        return ObjectId(id_str)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid id format")

# ------------------------------
# Departments CRUD (MVP: list, create)
# ------------------------------

@app.get("/departments")
def list_departments(limit: int = 100):
    items = get_documents("department", {}, limit)
    # Convert ObjectId to string
    for it in items:
        it["_id"] = str(it.get("_id"))
    return items

@app.post("/departments", status_code=201)
def create_department(payload: Department):
    new_id = create_document("department", payload)
    return {"_id": new_id}

# ------------------------------
# Employees CRUD (MVP: list, create)
# ------------------------------

@app.get("/employees")
def list_employees(limit: int = 100, department_id: Optional[str] = None, status: Optional[str] = None):
    q = {}
    if department_id:
        q["department_id"] = department_id
    if status:
        q["status"] = status
    items = get_documents("employee", q, limit)
    for it in items:
        it["_id"] = str(it.get("_id"))
    return items

@app.post("/employees", status_code=201)
def create_employee(payload: Employee):
    new_id = create_document("employee", payload)
    return {"_id": new_id}

# ------------------------------
# Leave Requests (MVP: submit, list, approve/reject)
# ------------------------------

class LeaveAction(BaseModel):
    action: str  # approve | reject

@app.get("/leaves")
def list_leaves(limit: int = 100, employee_id: Optional[str] = None, status: Optional[str] = None):
    q = {}
    if employee_id:
        q["employee_id"] = employee_id
    if status:
        q["status"] = status
    items = get_documents("leaverequest", q, limit)
    for it in items:
        it["_id"] = str(it.get("_id"))
    return items

@app.post("/leaves", status_code=201)
def submit_leave(payload: LeaveRequest):
    new_id = create_document("leaverequest", payload)
    return {"_id": new_id}

@app.post("/leaves/{leave_id}/action")
def act_on_leave(leave_id: str, body: LeaveAction):
    if body.action not in ("approve", "reject"):
        raise HTTPException(status_code=400, detail="Invalid action")
    oid = to_object_id(leave_id)
    res = db["leaverequest"].update_one({"_id": oid}, {"$set": {"status": "approved" if body.action == "approve" else "rejected", "updated_at": datetime.utcnow()}})
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="Leave not found")
    return {"success": True}

# ------------------------------
# Attendance (MVP: check-in, check-out, list)
# ------------------------------

@app.get("/attendance")
def list_attendance(limit: int = 100, employee_id: Optional[str] = None):
    q = {}
    if employee_id:
        q["employee_id"] = employee_id
    items = get_documents("attendance", q, limit)
    for it in items:
        it["_id"] = str(it.get("_id"))
    return items

class CheckIn(BaseModel):
    employee_id: str

@app.post("/attendance/checkin", status_code=201)
def check_in(payload: CheckIn):
    # create attendance doc for today if not exists
    today_str = datetime.utcnow().date().isoformat()
    existing = db["attendance"].find_one({"employee_id": payload.employee_id, "date": today_str})
    if existing:
        raise HTTPException(status_code=400, detail="Already checked in today")
    doc = {
        "employee_id": payload.employee_id,
        "date": today_str,
        "check_in": datetime.utcnow(),
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }
    inserted = db["attendance"].insert_one(doc)
    return {"_id": str(inserted.inserted_id)}

@app.post("/attendance/{attendance_id}/checkout")
def check_out(attendance_id: str):
    oid = to_object_id(attendance_id)
    res = db["attendance"].update_one({"_id": oid, "check_out": {"$exists": False}}, {"$set": {"check_out": datetime.utcnow(), "updated_at": datetime.utcnow()}})
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="Attendance not found or already checked out")
    return {"success": True}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
