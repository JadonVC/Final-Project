from sqlalchemy.orm import Session
from fastapi import HTTPException, status, Response, Depends
from ..models import sandwiches as model
from ..models import reviews as review_model
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import func
from typing import List, Optional


def create(db: Session, request):
    new_item = model.Sandwich(
        sandwich_name=request.sandwich_name,
        description=request.description,
        price=request.price,
        calories=request.calories,
        category=request.category,
        is_available=request.is_available
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
        result = db.query(model.Sandwich).all()
    except SQLAlchemyError as e:
        error = str(e.__dict__['orig'])
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)
    return result


def read_available_only(db: Session):
    """Customer function: Get only available sandwiches"""
    try:
        result = db.query(model.Sandwich).filter(
            model.Sandwich.is_available == True
        ).all()
    except SQLAlchemyError as e:
        error = str(e.__dict__['orig'])
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)
    return result


def read_one(db: Session, item_id):
    try:
        item = db.query(model.Sandwich).filter(model.Sandwich.id == item_id).first()
        if not item:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Id not found!")
    except SQLAlchemyError as e:
        error = str(e.__dict__['orig'])
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)
    return item


def search_by_category(db: Session, category: str):
    """CRITICAL: Customer function to search for specific food types (vegetarian, spicy, etc.)"""
    try:
        # Search for sandwiches that contain the category in their category field
        result = db.query(model.Sandwich).filter(
            model.Sandwich.category.ilike(f"%{category}%"),
            model.Sandwich.is_available == True  # Only show available items
        ).all()
    except SQLAlchemyError as e:
        error = str(e.__dict__['orig'])
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)
    return result


def search_by_name(db: Session, name: str):
    """Customer function to search sandwiches by name"""
    try:
        result = db.query(model.Sandwich).filter(
            model.Sandwich.sandwich_name.ilike(f"%{name}%"),
            model.Sandwich.is_available == True
        ).all()
    except SQLAlchemyError as e:
        error = str(e.__dict__['orig'])
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)
    return result


def get_menu_with_ratings(db: Session):
    """Customer function: Get menu with average ratings for each sandwich"""
    try:
        # Get sandwiches with their average ratings
        menu_items = db.query(
            model.Sandwich,
            func.avg(review_model.Review.rating).label('avg_rating'),
            func.count(review_model.Review.id).label('review_count')
        ).outerjoin(
            review_model.Review, model.Sandwich.id == review_model.Review.sandwich_id
        ).filter(
            model.Sandwich.is_available == True
        ).group_by(model.Sandwich.id).all()

        menu_with_ratings = []
        for sandwich, avg_rating, review_count in menu_items:
            menu_with_ratings.append({
                "id": sandwich.id,
                "sandwich_name": sandwich.sandwich_name,
                "description": sandwich.description,
                "price": float(sandwich.price),
                "calories": sandwich.calories,
                "category": sandwich.category,
                "average_rating": round(float(avg_rating), 1) if avg_rating else None,
                "review_count": review_count,
                "created_date": sandwich.created_date
            })

        return menu_with_ratings

    except SQLAlchemyError as e:
        error = str(e.__dict__['orig'])
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)


def get_popular_items(db: Session, limit: int = 10):
    """Staff function: Get most popular items based on order frequency"""
    try:
        from ..models import order_details as order_detail_model

        popular_items = db.query(
            model.Sandwich.id,
            model.Sandwich.sandwich_name,
            model.Sandwich.price,
            func.sum(order_detail_model.OrderDetail.amount).label('total_ordered'),
            func.count(order_detail_model.OrderDetail.id).label('order_frequency'),
            func.avg(review_model.Review.rating).label('avg_rating')
        ).join(
            order_detail_model.OrderDetail, model.Sandwich.id == order_detail_model.OrderDetail.sandwich_id
        ).outerjoin(
            review_model.Review, model.Sandwich.id == review_model.Review.sandwich_id
        ).group_by(
            model.Sandwich.id, model.Sandwich.sandwich_name, model.Sandwich.price
        ).order_by(
            func.sum(order_detail_model.OrderDetail.amount).desc()
        ).limit(limit).all()

        popular_list = []
        for item in popular_items:
            popular_list.append({
                "sandwich_id": item.id,
                "sandwich_name": item.sandwich_name,
                "price": float(item.price),
                "total_ordered": item.total_ordered,
                "order_frequency": item.order_frequency,
                "average_rating": round(float(item.avg_rating), 1) if item.avg_rating else None
            })

        return popular_list

    except SQLAlchemyError as e:
        error = str(e.__dict__['orig'])
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)


def get_unpopular_items(db: Session):
    """Staff function: Get items that are rarely ordered or have low ratings"""
    try:
        from ..models import order_details as order_detail_model

        # Get items with few orders or low ratings
        unpopular_items = db.query(
            model.Sandwich.id,
            model.Sandwich.sandwich_name,
            model.Sandwich.price,
            func.coalesce(func.sum(order_detail_model.OrderDetail.amount), 0).label('total_ordered'),
            func.avg(review_model.Review.rating).label('avg_rating'),
            func.count(review_model.Review.id).label('review_count')
        ).outerjoin(
            order_detail_model.OrderDetail, model.Sandwich.id == order_detail_model.OrderDetail.sandwich_id
        ).outerjoin(
            review_model.Review, model.Sandwich.id == review_model.Review.sandwich_id
        ).group_by(
            model.Sandwich.id, model.Sandwich.sandwich_name, model.Sandwich.price
        ).having(
            func.coalesce(func.sum(order_detail_model.OrderDetail.amount), 0) <= 5
        ).order_by(
            func.coalesce(func.sum(order_detail_model.OrderDetail.amount), 0)
        ).all()

        unpopular_list = []
        for item in unpopular_items:
            unpopular_list.append({
                "sandwich_id": item.id,
                "sandwich_name": item.sandwich_name,
                "price": float(item.price),
                "total_ordered": item.total_ordered,
                "average_rating": round(float(item.avg_rating), 1) if item.avg_rating else None,
                "review_count": item.review_count,
                "recommendation": "Consider removing or improving recipe" if item.total_ordered <= 2 else "Monitor performance"
            })

        return unpopular_list

    except SQLAlchemyError as e:
        error = str(e.__dict__['orig'])
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)


def toggle_availability(db: Session, sandwich_id: int):
    """Staff function: Quick toggle availability on/off"""
    try:
        sandwich = db.query(model.Sandwich).filter(model.Sandwich.id == sandwich_id).first()
        if not sandwich:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sandwich not found!")

        # Toggle availability
        sandwich.is_available = not sandwich.is_available
        db.commit()
        db.refresh(sandwich)

        status_text = "available" if sandwich.is_available else "unavailable"
        return {
            "sandwich": sandwich,
            "message": f"{sandwich.sandwich_name} is now {status_text}"
        }

    except SQLAlchemyError as e:
        error = str(e.__dict__['orig'])
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)


def get_category_list(db: Session):
    """Customer function: Get all unique categories for filtering"""
    try:
        # Get all non-null categories and split them
        categories = db.query(model.Sandwich.category).filter(
            model.Sandwich.category.isnot(None),
            model.Sandwich.is_available == True
        ).distinct().all()

        # Parse comma-separated categories
        all_categories = set()
        for category_row in categories:
            if category_row[0]:  # category_row is a tuple
                category_list = [cat.strip().lower() for cat in category_row[0].split(',')]
                all_categories.update(category_list)

        return sorted(list(all_categories))

    except SQLAlchemyError as e:
        error = str(e.__dict__['orig'])
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)


def get_sandwich_with_details(db: Session, sandwich_id: int):
    """Get sandwich with complete details including ratings, recipes, and reviews"""
    try:
        sandwich = db.query(model.Sandwich).filter(model.Sandwich.id == sandwich_id).first()
        if not sandwich:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sandwich not found!")

        # Get rating summary
        rating_stats = db.query(
            func.avg(review_model.Review.rating).label('avg_rating'),
            func.count(review_model.Review.id).label('review_count')
        ).filter(review_model.Review.sandwich_id == sandwich_id).first()

        # Get recent reviews
        recent_reviews = db.query(review_model.Review).filter(
            review_model.Review.sandwich_id == sandwich_id
        ).order_by(review_model.Review.review_date.desc()).limit(5).all()

        return {
            "sandwich": sandwich,
            "average_rating": round(float(rating_stats.avg_rating), 1) if rating_stats.avg_rating else None,
            "review_count": rating_stats.review_count,
            "recent_reviews": recent_reviews
        }

    except SQLAlchemyError as e:
        error = str(e.__dict__['orig'])
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)


def update(db: Session, item_id, request):
    try:
        item = db.query(model.Sandwich).filter(model.Sandwich.id == item_id)
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
        item = db.query(model.Sandwich).filter(model.Sandwich.id == item_id)
        if not item.first():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Id not found!")
        item.delete(synchronize_session=False)
        db.commit()
    except SQLAlchemyError as e:
        error = str(e.__dict__['orig'])
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)
    return Response(status_code=status.HTTP_204_NO_CONTENT)