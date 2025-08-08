from sqlalchemy.orm import Session
from fastapi import HTTPException, status, Response, Depends
from ..models import reviews as model
from ..models import orders as order_model
from ..models import sandwiches as sandwich_model
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import func
from datetime import datetime


def create(db: Session, request):
    # Verify that the order exists and get customer name from it
    order = db.query(order_model.Order).filter(
        order_model.Order.id == request.order_id
    ).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found!")

    # Verify that the sandwich exists
    sandwich = db.query(sandwich_model.Sandwich).filter(
        sandwich_model.Sandwich.id == request.sandwich_id
    ).first()
    if not sandwich:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sandwich not found!")

    # Verify that this order actually contains this sandwich (review verification)
    from ..models import order_details as order_detail_model
    order_contains_sandwich = db.query(order_detail_model.OrderDetail).filter(
        order_detail_model.OrderDetail.order_id == request.order_id,
        order_detail_model.OrderDetail.sandwich_id == request.sandwich_id
    ).first()
    if not order_contains_sandwich:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You can only review sandwiches that you actually ordered!"
        )

    # Check if customer already reviewed this sandwich from this order
    existing_review = db.query(model.Review).filter(
        model.Review.order_id == request.order_id,
        model.Review.sandwich_id == request.sandwich_id
    ).first()
    if existing_review:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You have already reviewed this sandwich from this order!"
        )

    new_item = model.Review(
        order_id=request.order_id,
        sandwich_id=request.sandwich_id,
        customer_name=order.customer_name,  # Pull from verified order
        rating=request.rating,
        comment=request.comment
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
        result = db.query(model.Review).all()
    except SQLAlchemyError as e:
        error = str(e.__dict__['orig'])
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)
    return result


def read_one(db: Session, item_id):
    try:
        item = db.query(model.Review).filter(model.Review.id == item_id).first()
        if not item:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Id not found!")
    except SQLAlchemyError as e:
        error = str(e.__dict__['orig'])
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)
    return item


def read_by_sandwich(db: Session, sandwich_id: int):
    """Get all reviews for a specific sandwich"""
    try:
        result = db.query(model.Review).filter(
            model.Review.sandwich_id == sandwich_id
        ).order_by(model.Review.review_date.desc()).all()
    except SQLAlchemyError as e:
        error = str(e.__dict__['orig'])
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)
    return result


def read_by_customer(db: Session, customer_name: str):
    """Get all reviews by a specific customer"""
    try:
        result = db.query(model.Review).filter(
            model.Review.customer_name.ilike(f"%{customer_name}%")
        ).order_by(model.Review.review_date.desc()).all()
    except SQLAlchemyError as e:
        error = str(e.__dict__['orig'])
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)
    return result


def get_low_rated_dishes(db: Session, max_rating: int = 2):
    """CRITICAL: Staff function to identify dishes with complaints/low ratings"""
    try:
        # Get sandwiches with average rating <= max_rating
        low_rated = db.query(
            sandwich_model.Sandwich.id,
            sandwich_model.Sandwich.sandwich_name,
            func.avg(model.Review.rating).label('avg_rating'),
            func.count(model.Review.id).label('review_count')
        ).join(
            model.Review, sandwich_model.Sandwich.id == model.Review.sandwich_id
        ).group_by(
            sandwich_model.Sandwich.id, sandwich_model.Sandwich.sandwich_name
        ).having(
            func.avg(model.Review.rating) <= max_rating
        ).order_by(func.avg(model.Review.rating)).all()

        problem_dishes = []
        for dish in low_rated:
            # Get recent complaints for this dish
            recent_complaints = db.query(model.Review).filter(
                model.Review.sandwich_id == dish.id,
                model.Review.rating <= max_rating,
                model.Review.comment.isnot(None)
            ).order_by(model.Review.review_date.desc()).limit(3).all()

            problem_dishes.append({
                "sandwich_id": dish.id,
                "sandwich_name": dish.sandwich_name,
                "average_rating": round(float(dish.avg_rating), 2),
                "total_reviews": dish.review_count,
                "recent_complaints": [
                    {
                        "rating": complaint.rating,
                        "comment": complaint.comment,
                        "customer": complaint.customer_name,
                        "date": complaint.review_date
                    } for complaint in recent_complaints
                ]
            })

        return problem_dishes

    except SQLAlchemyError as e:
        error = str(e.__dict__['orig'])
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)


def get_sandwich_rating_summary(db: Session, sandwich_id: int):
    """Get detailed rating breakdown for a specific sandwich"""
    try:
        # Get rating distribution
        rating_counts = db.query(
            model.Review.rating,
            func.count(model.Review.rating).label('count')
        ).filter(
            model.Review.sandwich_id == sandwich_id
        ).group_by(model.Review.rating).all()

        # Get overall stats
        overall_stats = db.query(
            func.avg(model.Review.rating).label('avg_rating'),
            func.count(model.Review.id).label('total_reviews')
        ).filter(
            model.Review.sandwich_id == sandwich_id
        ).first()

        # Get sandwich name
        sandwich = db.query(sandwich_model.Sandwich).filter(
            sandwich_model.Sandwich.id == sandwich_id
        ).first()
        if not sandwich:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sandwich not found!")

        # Format response
        rating_breakdown = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        for rating, count in rating_counts:
            rating_breakdown[rating] = count

        return {
            "sandwich_id": sandwich_id,
            "sandwich_name": sandwich.sandwich_name,
            "average_rating": round(float(overall_stats.avg_rating), 2) if overall_stats.avg_rating else 0,
            "total_reviews": overall_stats.total_reviews,
            "five_star_count": rating_breakdown[5],
            "four_star_count": rating_breakdown[4],
            "three_star_count": rating_breakdown[3],
            "two_star_count": rating_breakdown[2],
            "one_star_count": rating_breakdown[1]
        }

    except SQLAlchemyError as e:
        error = str(e.__dict__['orig'])
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)


def add_staff_response(db: Session, review_id: int, staff_response: str):
    """Staff function to respond to customer reviews"""
    try:
        review = db.query(model.Review).filter(model.Review.id == review_id).first()
        if not review:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found!")

        review.staff_response = staff_response
        review.response_date = datetime.now()
        db.commit()
        db.refresh(review)

    except SQLAlchemyError as e:
        error = str(e.__dict__['orig'])
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)

    return review


def get_unanswered_reviews(db: Session):
    """Staff function to find reviews that need responses"""
    try:
        result = db.query(model.Review).filter(
            model.Review.staff_response.is_(None)
        ).order_by(model.Review.review_date.desc()).all()
    except SQLAlchemyError as e:
        error = str(e.__dict__['orig'])
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)
    return result


def get_reviews_needing_attention(db: Session):
    """Staff function to get low-rated reviews that need immediate attention"""
    try:
        result = db.query(model.Review).filter(
            model.Review.rating <= 2,
            model.Review.staff_response.is_(None)
        ).order_by(model.Review.review_date.desc()).all()
    except SQLAlchemyError as e:
        error = str(e.__dict__['orig'])
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)
    return result


def update(db: Session, item_id, request):
    try:
        item = db.query(model.Review).filter(model.Review.id == item_id)
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
        item = db.query(model.Review).filter(model.Review.id == item_id)
        if not item.first():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Id not found!")
        item.delete(synchronize_session=False)
        db.commit()
    except SQLAlchemyError as e:
        error = str(e.__dict__['orig'])
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)
    return Response(status_code=status.HTTP_204_NO_CONTENT)