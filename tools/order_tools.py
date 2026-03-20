import requests

BASE_URL = "http://127.0.0.1:8000"


def get_products():
    """Get all products"""
    response = requests.get(f"{BASE_URL}/products")
    return response.json()


def get_order(order_id: str):
    """Get order status"""
    response = requests.get(f"{BASE_URL}/order/{order_id}")
    return response.json()


def create_order(product: str):
    """Create a new order"""
    data = {
        "id": "temp",
        "product": product,
        "status": "processing"
    }

    response = requests.post(f"{BASE_URL}/order", json=data)
    return response.json()


def cancel_order(order_id: str):
    """Cancel an order"""
    response = requests.post(f"{BASE_URL}/order/{order_id}/cancel")
    return response.json()