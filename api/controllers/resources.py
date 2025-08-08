from sqlalchemy.orm import Session
from fastapi import HTTPException, status, Response, Depends
from ..models import resources as model
from sqlalchemy.exc import SQLAlchemyError
from typing import List


def create(db: Session, request):
    new_item = model.Resource(
        item=request.item,
        amount=request.amount,
        unit=request.unit,
        minimum_stock=request.minimum_stock,
        cost_per_unit=request.cost_per_unit
    )

    try:
        db.add(new_item)
        db.commit()
        db.refresh(new_item)
    except SQLAlchemyError as e:
        error = str(e.__dict__['orig'])
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)

    return new_item


def read_all(db: Session):
    try:
        result = db.query(model.Resource).all()
    except SQLAlchemyError as e:
        error = str(e.__dict__['orig'])
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)
    return result


def read_one(db: Session, item_id):
    try:
        item = db.query(model.Resource).filter(model.Resource.id == item_id).first()
        if not item:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Id not found!")
    except SQLAlchemyError as e:
        error = str(e.__dict__['orig'])
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)
    return item


def read_by_item_name(db: Session, item_name: str):
    """Find resource by item name (case-insensitive)"""
    try:
        item = db.query(model.Resource).filter(
            model.Resource.item.ilike(f"%{item_name}%")
        ).all()
    except SQLAlchemyError as e:
        error = str(e.__dict__['orig'])
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)
    return item


def get_low_stock_items(db: Session):
    """CRITICAL: Get all items that are below minimum stock level"""
    try:
        result = db.query(model.Resource).filter(
            model.Resource.amount <= model.Resource.minimum_stock
        ).all()

        low_stock_alerts = []
        for item in result:
            low_stock_alerts.append({
                "id": item.id,
                "item": item.item,
                "current_stock": item.amount,
                "minimum_stock": item.minimum_stock,
                "unit": item.unit,
                "shortage": item.minimum_stock - item.amount,
                "alert_level": "CRITICAL" if item.amount <= 0 else "LOW"
            })

        return low_stock_alerts

    except SQLAlchemyError as e:
        error = str(e.__dict__['orig'])
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)


def get_out_of_stock_items(db: Session):
    """Get items that are completely out of stock"""
    try:
        result = db.query(model.Resource).filter(
            model.Resource.amount <= 0
        ).all()
    except SQLAlchemyError as e:
        error = str(e.__dict__['orig'])
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)
    return result


def check_sufficient_stock(db: Session, resource_id: int, required_amount: int):
    """Check if there's enough stock for a specific amount"""
    try:
        resource = db.query(model.Resource).filter(
            model.Resource.id == resource_id
        ).first()

        if not resource:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found!")

        return {
            "resource_id": resource.id,
            "item": resource.item,
            "available": resource.amount,
            "required": required_amount,
            "sufficient": resource.amount >= required_amount,
            "unit": resource.unit
        }

    except SQLAlchemyError as e:
        error = str(e.__dict__['orig'])
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)


def update_stock(db: Session, resource_id: int, new_amount: int):
    """Update stock amount for a resource"""
    try:
        item = db.query(model.Resource).filter(model.Resource.id == resource_id)
        if not item.first():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found!")

        item.update({"amount": new_amount}, synchronize_session=False)
        db.commit()

        # Check if this update puts item below minimum stock
        updated_item = item.first()
        if updated_item.amount <= updated_item.minimum_stock:
            return {
                "resource": updated_item,
                "warning": f"Stock level for {updated_item.item} is now below minimum ({updated_item.minimum_stock})"
            }

        return {"resource": updated_item, "warning": None}

    except SQLAlchemyError as e:
        error = str(e.__dict__['orig'])
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)


def consume_stock(db: Session, resource_id: int, amount_used: int):
    """Reduce stock when ingredients are used (for order fulfillment)"""
    try:
        resource = db.query(model.Resource).filter(
            model.Resource.id == resource_id
        ).first()

        if not resource:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found!")

        if resource.amount < amount_used:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient stock! Available: {resource.amount}, Required: {amount_used}"
            )

        new_amount = resource.amount - amount_used
        resource.amount = new_amount
        db.commit()
        db.refresh(resource)

        # Return warning if now below minimum
        warning = None
        if new_amount <= resource.minimum_stock:
            warning = f"LOW STOCK ALERT: {resource.item} is now at {new_amount} {resource.unit} (minimum: {resource.minimum_stock})"

        return {
            "resource": resource,
            "amount_consumed": amount_used,
            "remaining_stock": new_amount,
            "warning": warning
        }

    except SQLAlchemyError as e:
        error = str(e.__dict__['orig'])
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)


def restock_item(db: Session, resource_id: int, amount_added: int):
    """Add stock when ingredients are restocked"""
    try:
        resource = db.query(model.Resource).filter(
            model.Resource.id == resource_id
        ).first()

        if not resource:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found!")

        resource.amount += amount_added
        db.commit()
        db.refresh(resource)

        return {
            "resource": resource,
            "amount_added": amount_added,
            "new_stock_level": resource.amount
        }

    except SQLAlchemyError as e:
        error = str(e.__dict__['orig'])
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)


def get_inventory_summary(db: Session):
    """Get complete inventory overview for staff"""
    try:
        all_resources = db.query(model.Resource).all()

        summary = {
            "total_items": len(all_resources),
            "low_stock_count": 0,
            "out_of_stock_count": 0,
            "total_inventory_value": 0.0
        }

        for resource in all_resources:
            # Count low stock items
            if resource.amount <= resource.minimum_stock:
                summary["low_stock_count"] += 1

            # Count out of stock items
            if resource.amount <= 0:
                summary["out_of_stock_count"] += 1

            # Calculate total value (if cost_per_unit is available)
            if resource.cost_per_unit:
                summary["total_inventory_value"] += float(resource.amount * resource.cost_per_unit)

        return summary

    except SQLAlchemyError as e:
        error = str(e.__dict__['orig'])
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)


def update(db: Session, item_id, request):
    try:
        item = db.query(model.Resource).filter(model.Resource.id == item_id)
        if not item.first():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Id not found!")
        update_data = request.dict(exclude_unset=True)
        item.update(update_data, synchronize_session=False)
        db.commit()
    except SQLAlchemyError as e:
        error = str(e.__dict__['orig'])
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)
    return item.first()


def delete(db: Session, item_id):
    try:
        item = db.query(model.Resource).filter(model.Resource.id == item_id)
        if not item.first():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Id not found!")
        item.delete(synchronize_session=False)
        db.commit()
    except SQLAlchemyError as e:
        error = str(e.__dict__['orig'])
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)
    return Response(status_code=status.HTTP_204_NO_CONTENT)