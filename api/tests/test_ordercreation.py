import pytest
from unittest.mock import Mock, patch
from api.controllers import orders as order_controller
from api.models.orders import Order
from api.schemas.orders import OrderCreate
from fastapi import HTTPException


class TestOrderCreation:
    """Unit tests for order creation functionality"""

    @pytest.fixture
    def mock_db_session(self):
        """Mock database session"""
        db = Mock()
        return db

    @pytest.fixture
    def valid_order_data(self):
        """Valid order data for testing"""
        return OrderCreate(
            customer_name="John Doe",
            phone="555-0123",
            address="123 Main St",
            order_type="delivery",
            description="Test order"
        )

    @pytest.fixture
    def takeout_order_data(self):
        """Takeout order (no address needed)"""
        return OrderCreate(
            customer_name="Jane Smith",
            phone="555-0456",
            order_type="takeout",
            description="Takeout order"
        )

    def test_create_order_success(self, mock_db_session, valid_order_data):
        """Test successful order creation with all required fields"""
        # Setup
        mock_db_session.add.return_value = None
        mock_db_session.commit.return_value = None
        mock_db_session.refresh.return_value = None

        # Execute
        with patch('uuid.uuid4') as mock_uuid:
            mock_uuid.return_value.hex = 'abc123defg456789'
            result = order_controller.create(mock_db_session, valid_order_data)

        # Verify
        assert result is not None
        assert result.customer_name == "John Doe"
        assert result.phone == "555-0123"
        assert result.address == "123 Main St"
        assert result.order_type == "delivery"
        assert result.status == "received"  # Default status
        assert result.payment_status == "pending"  # Default payment status
        assert result.total_amount == 0.00  # Default total
        assert result.tracking_number.startswith("ORD-")

        # Verify database calls
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()
        mock_db_session.refresh.assert_called_once()

    def test_create_takeout_order(self, mock_db_session, takeout_order_data):
        """Test takeout order creation (address not required)"""
        # Setup
        mock_db_session.add.return_value = None
        mock_db_session.commit.return_value = None
        mock_db_session.refresh.return_value = None

        # Execute
        result = order_controller.create(mock_db_session, takeout_order_data)

        # Verify
        assert result is not None
        assert result.customer_name == "Jane Smith"
        assert result.order_type == "takeout"
        assert result.address is None  # No address for takeout
        assert result.status == "received"

    def test_tracking_number_uniqueness(self, mock_db_session, valid_order_data):
        """Test that tracking numbers are unique"""
        # Setup
        mock_db_session.add.return_value = None
        mock_db_session.commit.return_value = None
        mock_db_session.refresh.return_value = None

        # Execute - Create two orders
        with patch('uuid.uuid4') as mock_uuid:
            mock_uuid.return_value.hex = 'first123456789'
            order1 = order_controller.create(mock_db_session, valid_order_data)

            mock_uuid.return_value.hex = 'second987654321'
            order2 = order_controller.create(mock_db_session, valid_order_data)

        # Verify
        assert order1.tracking_number != order2.tracking_number
        assert order1.tracking_number.startswith("ORD-")
        assert order2.tracking_number.startswith("ORD-")

    def test_create_order_database_error(self, mock_db_session, valid_order_data):
        """Test handling of database errors during order creation"""
        # Setup - Mock database error
        from sqlalchemy.exc import SQLAlchemyError
        mock_db_session.add.side_effect = SQLAlchemyError("Database connection failed", None, None)

        # Execute & Verify
        with pytest.raises(HTTPException) as exc_info:
            order_controller.create(mock_db_session, valid_order_data)

        assert exc_info.value.status_code == 400

    def test_order_defaults(self, mock_db_session, valid_order_data):
        """Test that proper defaults are set for new orders"""
        # Setup
        mock_db_session.add.return_value = None
        mock_db_session.commit.return_value = None
        mock_db_session.refresh.return_value = None

        # Execute
        result = order_controller.create(mock_db_session, valid_order_data)

        # Verify defaults
        assert result.status == "received"
        assert result.payment_status == "pending"
        assert result.total_amount == 0.00
        assert result.tracking_number is not None
        assert len(result.tracking_number) > 8  # Should have ORD- prefix + UUID

    @pytest.mark.parametrize("order_type,address", [
        ("delivery", "123 Main St"),
        ("takeout", None),
        ("delivery", "456 Oak Ave"),
        ("takeout", ""),  # Empty address for takeout is OK
    ])
    def test_order_types_and_addresses(self, mock_db_session, order_type, address):
        """Test different combinations of order types and addresses"""
        # Setup
        mock_db_session.add.return_value = None
        mock_db_session.commit.return_value = None
        mock_db_session.refresh.return_value = None

        order_data = OrderCreate(
            customer_name="Test Customer",
            phone="555-9999",
            address=address,
            order_type=order_type
        )

        # Execute
        result = order_controller.create(mock_db_session, order_data)

        # Verify
        assert result.order_type == order_type
        assert result.address == address
