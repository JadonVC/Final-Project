from fastapi import APIRouter, Depends, FastAPI, status, Response
from sqlalchemy.orm import Session
from ..controllers import orders as controller
from ..schemas import orders as schema
from ..dependencies.database import engine, get_db
from datetime import datetime

router = APIRouter(
    tags=['Orders'],
    prefix="/orders"
)

@router.post("/", response_model=schema.Order)
def create(request: schema.OrderCreate, db: Session = Depends(get_db)):
    return controller.create(db=db, request=request)

@router.get("/", response_model=list[schema.Order])
def read_all(db: Session = Depends(get_db)):
    return controller.read_all(db)

# SPECIFIC ROUTES FIRST (before the generic /{item_id})
@router.get("/track/{tracking_number}", response_model=schema.Order)
def track_order(tracking_number: str, db: Session = Depends(get_db)):
    """Customer function: Track order by tracking number"""
    return controller.read_by_tracking_number(db, tracking_number=tracking_number)

@router.get("/date-range/", response_model=list[schema.Order])
def get_orders_by_date_range(start_date: datetime, end_date: datetime, db: Session = Depends(get_db)):
    """Staff function: Get orders within specific date range for revenue reporting"""
    return controller.get_orders_by_date_range(db, start_date=start_date, end_date=end_date)

# GENERIC ROUTES LAST
@router.get("/{item_id}", response_model=schema.Order)
def read_one(item_id: int, db: Session = Depends(get_db)):
    return controller.read_one(db, item_id=item_id)

@router.put("/{item_id}", response_model=schema.Order)
def update(item_id: int, request: schema.OrderUpdate, db: Session = Depends(get_db)):
    return controller.update(db=db, request=request, item_id=item_id)

@router.put("/{item_id}/status", response_model=schema.Order)
def update_status(item_id: int, new_status: str, db: Session = Depends(get_db)):
    """Staff function: Update order status (received, preparing, ready, completed)"""
    return controller.update_status(db, item_id=item_id, new_status=new_status)

@router.put("/{item_id}/total", response_model=schema.Order)
def update_total(item_id: int, total_amount: float, db: Session = Depends(get_db)):
    """System function: Update order total when order details change"""
    return controller.update_total_amount(db, order_id=item_id, total_amount=total_amount)

@router.delete("/{item_id}")
def delete(item_id: int, db: Session = Depends(get_db)):
    return controller.delete(db=db, item_id=item_id)