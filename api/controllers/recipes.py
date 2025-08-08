from sqlalchemy.orm import Session
from fastapi import HTTPException, status, Response, Depends
from ..models import recipes as model
from ..models import sandwiches as sandwich_model
from ..models import resources as resource_model
from sqlalchemy.exc import SQLAlchemyError


def create(db: Session, request):
    # Verify that sandwich and resource exist
    sandwich_exists = db.query(sandwich_model.Sandwich).filter(
        sandwich_model.Sandwich.id == request.sandwich_id
    ).first()
    if not sandwich_exists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sandwich not found!")

    resource_exists = db.query(resource_model.Resource).filter(
        resource_model.Resource.id == request.resource_id
    ).first()
    if not resource_exists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found!")

    new_item = model.Recipe(
        sandwich_id=request.sandwich_id,
        resource_id=request.resource_id,
        amount=request.amount,
        unit=request.unit
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
        result = db.query(model.Recipe).all()
    except SQLAlchemyError as e:
        error = str(e.__dict__['orig'])
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)
    return result


def read_one(db: Session, item_id):
    try:
        item = db.query(model.Recipe).filter(model.Recipe.id == item_id).first()
        if not item:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Id not found!")
    except SQLAlchemyError as e:
        error = str(e.__dict__['orig'])
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)
    return item


def read_by_sandwich(db: Session, sandwich_id: int):
    """Get all ingredients/resources needed for a specific sandwich"""
    try:
        result = db.query(model.Recipe).filter(
            model.Recipe.sandwich_id == sandwich_id
        ).all()
    except SQLAlchemyError as e:
        error = str(e.__dict__['orig'])
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)
    return result


def read_by_resource(db: Session, resource_id: int):
    """Get all sandwiches that use a specific ingredient/resource"""
    try:
        result = db.query(model.Recipe).filter(
            model.Recipe.resource_id == resource_id
        ).all()
    except SQLAlchemyError as e:
        error = str(e.__dict__['orig'])
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)
    return result


def check_ingredient_availability(db: Session, sandwich_id: int, quantity_needed: int = 1):
    """Check if enough ingredients are available to make a sandwich"""
    try:
        # Get all ingredients needed for this sandwich
        recipes = db.query(model.Recipe).filter(
            model.Recipe.sandwich_id == sandwich_id
        ).all()

        insufficient_ingredients = []

        for recipe in recipes:
            # Get current stock of this ingredient
            resource = db.query(resource_model.Resource).filter(
                resource_model.Resource.id == recipe.resource_id
            ).first()

            if not resource:
                insufficient_ingredients.append({
                    "ingredient": "Unknown",
                    "needed": recipe.amount * quantity_needed,
                    "available": 0,
                    "unit": recipe.unit
                })
                continue

            total_needed = recipe.amount * quantity_needed

            if resource.amount < total_needed:
                insufficient_ingredients.append({
                    "ingredient": resource.item,
                    "needed": total_needed,
                    "available": resource.amount,
                    "unit": recipe.unit
                })

        return {
            "can_fulfill": len(insufficient_ingredients) == 0,
            "insufficient_ingredients": insufficient_ingredients
        }

    except SQLAlchemyError as e:
        error = str(e.__dict__['orig'])
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)


def get_recipe_with_details(db: Session, sandwich_id: int):
    """Get complete recipe with sandwich and ingredient details"""
    try:
        recipes = db.query(model.Recipe).filter(
            model.Recipe.sandwich_id == sandwich_id
        ).all()

        if not recipes:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No recipe found for this sandwich!")

        recipe_details = []
        for recipe in recipes:
            # Get resource details
            resource = db.query(resource_model.Resource).filter(
                resource_model.Resource.id == recipe.resource_id
            ).first()

            recipe_details.append({
                "recipe_id": recipe.id,
                "amount": recipe.amount,
                "unit": recipe.unit,
                "ingredient_name": resource.item if resource else "Unknown",
                "available_stock": resource.amount if resource else 0
            })

        return recipe_details

    except SQLAlchemyError as e:
        error = str(e.__dict__['orig'])
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)


def update(db: Session, item_id, request):
    try:
        item = db.query(model.Recipe).filter(model.Recipe.id == item_id)
        if not item.first():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Id not found!")

        update_data = request.dict(exclude_unset=True)

        # Verify sandwich and resource exist if they're being updated
        if 'sandwich_id' in update_data:
            sandwich_exists = db.query(sandwich_model.Sandwich).filter(
                sandwich_model.Sandwich.id == update_data['sandwich_id']
            ).first()
            if not sandwich_exists:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sandwich not found!")

        if 'resource_id' in update_data:
            resource_exists = db.query(resource_model.Resource).filter(
                resource_model.Resource.id == update_data['resource_id']
            ).first()
            if not resource_exists:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found!")

        item.update(update_data, synchronize_session=False)
        db.commit()
    except SQLAlchemyError as e:
        error = str(e.__dict__['orig'])
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)
    return item.first()


def delete(db: Session, item_id):
    try:
        item = db.query(model.Recipe).filter(model.Recipe.id == item_id)
        if not item.first():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Id not found!")
        item.delete(synchronize_session=False)
        db.commit()
    except SQLAlchemyError as e:
        error = str(e.__dict__['orig'])
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)
    return Response(status_code=status.HTTP_204_NO_CONTENT)