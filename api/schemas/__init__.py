# In your api/models/__init__.py file, add this:

# Import all models so SQLAlchemy can find relationships
from . import orders
from . import order_details
from . import sandwiches
from . import resources
from . import recipes
from . import reviews
from . import promocodes

# This ensures all models are loaded when testing