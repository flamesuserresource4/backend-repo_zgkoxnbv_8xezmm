"""
Database Schemas

Define your MongoDB collection schemas here using Pydantic models.
These schemas are used for data validation in your application.

Each Pydantic model represents a collection in your database.
Model name is converted to lowercase for the collection name:
- User -> "user" collection
- Product -> "product" collection
- BlogPost -> "blogs" collection
"""

from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import date, datetime

# ------------------------------
# HRMS PORTAL SCHEMAS (MVP)
# ------------------------------

class Department(BaseModel):
    name: str = Field(..., description="Department name")
    description: Optional[str] = Field(None, description="Department description")

class Employee(BaseModel):
    first_name: str = Field(..., description="First name")
    last_name: str = Field(..., description="Last name")
    email: str = Field(..., description="Work email")
    department_id: Optional[str] = Field(None, description="Reference to department _id as string")
    role: Optional[str] = Field(None, description="Job title/role")
    hire_date: Optional[date] = Field(None, description="Date of joining")
    salary: Optional[float] = Field(None, ge=0, description="Base salary")
    status: Literal["active", "inactive"] = Field("active", description="Employment status")

class LeaveRequest(BaseModel):
    employee_id: str = Field(..., description="Employee _id as string")
    start_date: date = Field(..., description="Leave start date")
    end_date: date = Field(..., description="Leave end date")
    leave_type: Literal["annual", "sick", "unpaid", "other"] = Field("annual", description="Type of leave")
    reason: Optional[str] = Field(None, description="Reason for leave")
    status: Literal["pending", "approved", "rejected"] = Field("pending", description="Approval status")

class Attendance(BaseModel):
    employee_id: str = Field(..., description="Employee _id as string")
    attendance_date: date = Field(..., description="Attendance date")
    check_in: Optional[datetime] = Field(None, description="Check-in timestamp")
    check_out: Optional[datetime] = Field(None, description="Check-out timestamp")

# Example schemas retained for reference but not used directly in HRMS
class User(BaseModel):
    name: str
    email: str
    address: str
    age: Optional[int] = Field(None, ge=0, le=120)
    is_active: bool = True

class Product(BaseModel):
    title: str
    description: Optional[str] = None
    price: float
    category: str
    in_stock: bool = True
