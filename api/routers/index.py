from . import orders, order_details, promocodes, recipes, resources, reviews, sandwiches

def load_routes(app):
    app.include_router(orders.router)
    app.include_router(order_details.router)
    app.include_router(promocodes.router)      # NEW
    app.include_router(recipes.router)         # NEW
    app.include_router(resources.router)       # NEW
    app.include_router(reviews.router)         # NEW
    app.include_router(sandwiches.router)      # NEW