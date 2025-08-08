import pytest
from fastapi import status


def test_create_order_api_endpoint(client):
    """Test the actual API endpoint"""
    order_data = {
        "customer_name": "Jane Smith",
        "phone": "555-0456",
        "address": "456 Oak Ave",
        "order_type": "delivery",  # Changed to delivery since address provided
        "description": "API test order"
    }

    response = client.post("/orders/", json=order_data)

    # Debug output if test fails
    if response.status_code != 200:
        print(f"Error: {response.status_code}")
        print(f"Response: {response.text}")

    assert response.status_code == 200

    response_data = response.json()
    assert response_data["customer_name"] == "Jane Smith"
    assert response_data["phone"] == "555-0456"
    assert response_data["order_type"] == "delivery"
    assert "tracking_number" in response_data
    assert response_data["status"] == "received"


def test_create_takeout_order(client):
    """Test takeout order (no address required)"""
    order_data = {
        "customer_name": "John Takeout",
        "phone": "555-1234",
        "order_type": "takeout"
    }

    response = client.post("/orders/", json=order_data)
    assert response.status_code == 200

    response_data = response.json()
    assert response_data["order_type"] == "takeout"


def test_read_all_orders(client):
    """Test getting all orders"""
    response = client.get("/orders/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_track_order_by_tracking_number(client):
    """Test order tracking functionality"""
    # First create an order
    order_data = {
        "customer_name": "Track Test",
        "phone": "555-0789",
        "address": "789 Pine St",
        "order_type": "delivery"
    }

    create_response = client.post("/orders/", json=order_data)
    assert create_response.status_code == 200

    response_data = create_response.json()
    tracking_number = response_data["tracking_number"]

    # Now track it
    track_response = client.get(f"/orders/track/{tracking_number}")
    assert track_response.status_code == 200
    assert track_response.json()["customer_name"] == "Track Test"


def test_update_order_status(client):
    """Test staff updating order status"""
    # Create an order first
    order_data = {
        "customer_name": "Status Test",
        "phone": "555-1111",
        "order_type": "takeout"
    }

    create_response = client.post("/orders/", json=order_data)
    assert create_response.status_code == 200

    order_id = create_response.json()["id"]

    # Update status
    status_response = client.put(f"/orders/{order_id}/status?new_status=preparing")
    assert status_response.status_code == 200
    assert status_response.json()["status"] == "preparing"


def test_order_not_found(client):
    """Test getting non-existent order"""
    response = client.get("/orders/99999")
    assert response.status_code == 404