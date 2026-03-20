from pydantic import BaseModel

class Order(BaseModel):
    id: str
    product: str
    status: str