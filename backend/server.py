from fastapi import FastAPI
from models.order import Order
from models.product import Product

from agent.agent import interpret_and_call_tools

app = FastAPI()

# Fake database
products = {
    "iphone": {"name": "iPhone 15", "price": 999},
    "ipad": {"name": "iPad Air", "price": 799}
}

orders = {
    "1001": {"product": "iphone", "status": "shipped"},
    "1002": {"product": "ipad", "status": "processing"}
}


@app.get("/")
def root():
    return {"message": "AI Agent E-commerce Backend"}


@app.get("/products")
def get_products():
    return products


@app.get("/order/{order_id}")
def get_order(order_id: str):
    if order_id not in orders:
        return {"error": "order not found"}

    return orders[order_id]


@app.post("/order")
def create_order(order: Order):
    order_id = str(len(orders) + 1001)

    orders[order_id] = {
        "product": order.product,
        "status": "processing"
    }

    return {"order_id": order_id}


@app.post("/order/{order_id}/cancel")
def cancel_order(order_id: str):
    if order_id not in orders:
        return {"error": "order not found"}

    orders[order_id]["status"] = "cancelled"

    return {"message": "order cancelled"}


# ------------------------
# AI Agent Endpoint
# ------------------------

@app.post("/agent")
def run_agent(query: str):
    result = interpret_and_call_tools(query)
    return result