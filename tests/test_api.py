from fastapi.testclient import TestClient
from backend.server import app

client = TestClient(app)


def test_get_products():
    response = client.get("/products")
    assert response.status_code == 200
    assert "iphone" in response.json()


def test_get_order():
    response = client.get("/order/1001")
    assert response.status_code == 200
    assert "product" in response.json()


def test_create_order():
    new_order = {
        "id": "2001",
        "product": "iphone",
        "status": "processing"
    }

    response = client.post("/order", json=new_order)
    assert response.status_code == 200
    assert "order_id" in response.json()


def test_cancel_order():
    response = client.post("/order/1001/cancel")
    assert response.status_code == 200
    assert response.json()["message"] == "order cancelled"