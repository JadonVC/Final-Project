from sqlalchemy.orm import Session
from fastapi import HTTPException, status, Response
from ..models import orders as model
from sqlalchemy.exc import SQLAlchemyError
import uuid
from datetime import datetime


def create(db: Session, request):
    # Generate unique tracking number for customer
    tracking_number = f"ORD-{uuid.uuid4().hex[:8].upper()}"

    new_item = model.Order(
        customer_name=request.customer_name,
        phone=request.phone,
        address=request.address,
        order_type=request.order_type,
        description=request.description,
        tracking_number=tracking_number,
        status="received",
        payment_status="pending",
        total_amount=0.00,  # Will be calculated when order details are added
        promo_code_id=getattr(request, 'promo_code_id', None)
    )

    try:
        db.add(new_item)
        db.commit()
        db.refresh(new_item)
    except SQLAlchemyError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A database error occurred during order creation."
        )

    return new_item


def read_all(db: Session):
    try:
        result = db.query(model.Order).all()
    except SQLAlchemyError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="A database error occurred while retrieving orders."
        )
    return result


def read_one(db: Session, item_id):
    try:
        item = db.query(model.Order).filter(model.Order.id == item_id).first()
        if not item:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Id not found!")
        return item
    except SQLAlchemyError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="A database error occurred."
        )


def read_by_tracking_number(db: Session, tracking_number: str):
    """Allow customers to track orders by tracking number"""
    try:
        item = db.query(model.Order).filter(model.Order.tracking_number == tracking_number).first()
        if not item:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tracking number not found!")
    except SQLAlchemyError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="A database error occurred."
        )
    return item


def update(db: Session, item_id, request):
    try:
        item = db.query(model.Order).filter(model.Order.id == item_id)
        if not item.first():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Id not found!")
        update_data = request.dict(exclude_unset=True)
        item.update(update_data, synchronize_session=False)
        db.commit()
    except SQLAlchemyError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A database error occurred during the update."
        )
    return item.first()


def update_status(db: Session, item_id, new_status: str):
    """Staff function to update order status"""
    valid_statuses = ["received", "preparing", "ready", "completed"]
    if new_status not in valid_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status. Must be one of: {valid_statuses}"
        )

    try:
        item = db.query(model.Order).filter(model.Order.id == item_id)
        if not item.first():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Id not found!")
        item.update({"status": new_status}, synchronize_session=False)
        db.commit()
    except SQLAlchemyError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A database error occurred while updating the status."
        )
    return item.first()


def update_total_amount(db: Session, order_id: int, total_amount: float):
    """Update order total when order details are added/modified"""
    try:
        item = db.query(model.Order).filter(model.Order.id == order_id)
        if not item.first():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found!")
        item.update({"total_amount": total_amount}, synchronize_session=False)
        db.commit()
    except SQLAlchemyError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A database error occurred while updating the total amount."
        )
    return item.first()


def get_orders_by_date_range(db: Session, start_date: datetime, end_date: datetime):
    """Staff function to view orders within date range"""
    try:
        result = db.query(model.Order).filter(
            model.Order.order_date >= start_date,
            model.Order.order_date <= end_date
        ).all()
    except SQLAlchemyError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="A database error occurred while retrieving orders by date range."
        )
    return result


def delete(db: Session, item_id):
    try:
        item = db.query(model.Order).filter(model.Order.id == item_id)
        if not item.first():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Id not found!")
        item.delete(synchronize_session=False)
        db.commit()
    except SQLAlchemyError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A database error occurred during the delete operation."
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)