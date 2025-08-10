from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
from uuid import uuid4

app = FastAPI(title="Orders & Inventory API", version="1.0")

# Models
class Product(BaseModel):
    id: str
    name: str
    price: float
    stock: int

class ProductCreate(BaseModel):
    name: str
    price: float
    stock: int

class Order(BaseModel):
    id: str
    product_id: str
    quantity: int
    total_price: float
    status: str

class OrderCreate(BaseModel):
    product_id: str
    quantity: int

# In-memory storage
products: List[Product] = []
orders: List[Order] = []

# CRUD for Products
@app.post("/products", response_model=Product)
def create_product(prod: ProductCreate):
    new_prod = Product(id=str(uuid4()), **prod.dict())
    products.append(new_prod)
    return new_prod

@app.get("/products", response_model=List[Product])
def list_products():
    return products

@app.get("/products/{product_id}", response_model=Product)
def get_product(product_id: str):
    for prod in products:
        if prod.id == product_id:
            return prod
    raise HTTPException(status_code=404, detail="Product not found")

@app.put("/products/{product_id}", response_model=Product)
def update_product(product_id: str, prod_update: ProductCreate):
    for idx, prod in enumerate(products):
        if prod.id == product_id:
            updated = prod.copy(update=prod_update.dict())
            products[idx] = updated
            return updated
    raise HTTPException(status_code=404, detail="Product not found")

@app.delete("/products/{product_id}")
def delete_product(product_id: str):
    for idx, prod in enumerate(products):
        if prod.id == product_id:
            del products[idx]
            return {"message": "Product deleted"}
    raise HTTPException(status_code=404, detail="Product not found")

# Orders
@app.post("/orders", response_model=Order)
def create_order(order_req: OrderCreate):
    product = next((p for p in products if p.id == order_req.product_id), None)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    if product.stock < order_req.quantity:
        raise HTTPException(status_code=400, detail="Insufficient stock")

    product.stock -= order_req.quantity
    new_order = Order(
        id=str(uuid4()),
        product_id=product.id,
        quantity=order_req.quantity,
        total_price=product.price * order_req.quantity,
        status="pending"
    )
    orders.append(new_order)
    return new_order

@app.get("/orders", response_model=List[Order])
def list_orders():
    return orders

@app.post("/webhook/payment")
def mark_as_paid(order_id: str):
    order = next((o for o in orders if o.id == order_id), None)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    order.status = "paid"
    return {"message": "Order marked as paid"}
