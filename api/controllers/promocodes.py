from sqlalchemy.orm import Session
from fastapi import HTTPException, status, Response, Depends
from ..models import promocodes as model
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime


def create(db: Session, request):
    new_item = model.PromoCode(
        code=request.code.upper(),  # Store codes in uppercase for consistency
        discount_amount=request.discount_amount,
        expiration_date=request.expiration_date,
        usage_limit=request.usage_limit,
        minimum_order_amount=request.minimum_order_amount,
        description=request.description,
        is_active=request.is_active
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
        result = db.query(model.PromoCode).all()
    except SQLAlchemyError as e:
        error = str(e.__dict__['orig'])
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)
    return result


def read_active_codes(db: Session):
    """Get only active, non-expired promo codes"""
    try:
        result = db.query(model.PromoCode).filter(
            model.PromoCode.is_active == True,
            model.PromoCode.expiration_date > datetime.now(),
            model.PromoCode.times_used < model.PromoCode.usage_limit
        ).all()
    except SQLAlchemyError as e:
        error = str(e.__dict__['orig'])
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)
    return result


def read_one(db: Session, item_id):
    try:
        item = db.query(model.PromoCode).filter(model.PromoCode.id == item_id).first()
        if not item:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Id not found!")
    except SQLAlchemyError as e:
        error = str(e.__dict__['orig'])
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)
    return item


def read_by_code(db: Session, promo_code: str):
    """Find promo code by code string"""
    try:
        item = db.query(model.PromoCode).filter(
            model.PromoCode.code == promo_code.upper()
        ).first()
        if not item:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Promo code not found!")
    except SQLAlchemyError as e:
        error = str(e.__dict__['orig'])
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)
    return item


def validate_promo_code(db: Session, promo_code: str, order_total: float):
    """Validate if promo code can be applied to an order"""
    try:
        code = db.query(model.PromoCode).filter(
            model.PromoCode.code == promo_code.upper()
        ).first()

        if not code:
            return {
                "is_valid": False,
                "discount_amount": 0.0,
                "message": "Promo code not found"
            }

        # Check if code is active
        if not code.is_active:
            return {
                "is_valid": False,
                "discount_amount": 0.0,
                "message": "Promo code is no longer active"
            }

        # Check expiration
        if code.expiration_date <= datetime.now():
            return {
                "is_valid": False,
                "discount_amount": 0.0,
                "message": "Promo code has expired"
            }

        # Check usage limit
        if code.times_used >= code.usage_limit:
            return {
                "is_valid": False,
                "discount_amount": 0.0,
                "message": "Promo code usage limit reached"
            }

        # Check minimum order amount
        if order_total < code.minimum_order_amount:
            return {
                "is_valid": False,
                "discount_amount": 0.0,
                "message": f"Minimum order amount of ${code.minimum_order_amount} required"
            }

        # Code is valid!
        return {
            "is_valid": True,
            "discount_amount": float(code.discount_amount),
            "message": f"Promo code applied! ${float(code.discount_amount)} off"
        }

    except SQLAlchemyError as e:
        error = str(e.__dict__['orig'])
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)


def apply_promo_code(db: Session, promo_code: str):
    """Increment usage count when promo code is used"""
    try:
        code = db.query(model.PromoCode).filter(
            model.PromoCode.code == promo_code.upper()
        ).first()

        if not code:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Promo code not found!")

        # Increment usage count
        code.times_used += 1
        db.commit()
        db.refresh(code)

    except SQLAlchemyError as e:
        error = str(e.__dict__['orig'])
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)

    return code


def update(db: Session, item_id, request):
    try:
        item = db.query(model.PromoCode).filter(model.PromoCode.id == item_id)
        if not item.first():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Id not found!")

        update_data = request.dict(exclude_unset=True)
        # Ensure code is uppercase if being updated
        if 'code' in update_data:
            update_data['code'] = update_data['code'].upper()

        item.update(update_data, synchronize_session=False)
        db.commit()
    except SQLAlchemyError as e:
        error = str(e.__dict__['orig'])
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)
    return item.first()


def deactivate_code(db: Session, item_id):
    """Staff function to quickly deactivate a promo code"""
    try:
        item = db.query(model.PromoCode).filter(model.PromoCode.id == item_id)
        if not item.first():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Id not found!")
        item.update({"is_active": False}, synchronize_session=False)
        db.commit()
    except SQLAlchemyError as e:
        error = str(e.__dict__['orig'])
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)
    return item.first()


def delete(db: Session, item_id):
    try:
        item = db.query(model.PromoCode).filter(model.PromoCode.id == item_id)
        if not item.first():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Id not found!")
        item.delete(synchronize_session=False)
        db.commit()
    except SQLAlchemyError as e:
        error = str(e.__dict__['orig'])
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)
    return Response(status_code=status.HTTP_204_NO_CONTENT)