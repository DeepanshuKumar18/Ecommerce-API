from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List
from datetime import timedelta

from . import crud, models, schemas
from .database import Local_Session, engine
from .auth import (
    create_access_token,
    get_current_user,
    get_current_admin,
    get_current_seller,
    get_current_admin_or_seller,
)

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Mini E-Commerce API", version="0.1.0")


def get_db():
    db = Local_Session()
    try:
        yield db
    finally:
        db.close()


@app.get("/", tags=["Public"], summary="Home Page")
def home():
    return {"Message": "Welcome To Mini E-Commerce FastAPI Tutorial"}


@app.post(
    "/users/",
    response_model=schemas.User,
    status_code=201,
    tags=["Public"],
    summary="Signup",
)
def signup(user: schemas.UserCreate, db: Session = Depends(get_db)):
    if crud.get_user_by_email(db, email=user.email):
        raise HTTPException(status_code=400, detail="Email already registered")
    return crud.Signup(db=db, user=user)


@app.post("/login", response_model=schemas.Token, tags=["Public"], summary="Login")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    user = crud.get_user_by_email(db, email=form_data.username)
    if not user or not crud.verify_password(form_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    token = create_access_token(
        data={"user_id": user.id, "email": user.email, "role": user.role},
        expires_delta=timedelta(minutes=60),
    )
    return {"access_token": token, "token_type": "bearer"}


@app.get(
    "/categories/",
    response_model=List[schemas.Category],
    tags=["Public"],
    summary="List Categories",
)
def get_categories(db: Session = Depends(get_db)):
    return crud.get_categories(db)


@app.get(
    "/products/category/{category_id}",
    response_model=List[schemas.Product],
    tags=["Public"],
    summary="List Products by Category",
)
def list_products_by_category(category_id: int, db: Session = Depends(get_db)):
    products = crud.get_products_by_category(db, category_id=category_id)
    if not products:
        raise HTTPException(status_code=404, detail="No products found for this category")
    return products


@app.get(
    "/products/",
    response_model=List[schemas.Product],
    tags=["Public"],
    summary="List All Products",
)
def list_products(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_products(db, skip=skip, limit=limit)


@app.get(
    "/products/{product_id}",
    response_model=schemas.Product,
    tags=["Public"],
    summary="View Product Details",
)
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = crud.get_product(db, product_id=product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


# User
@app.get("/me", response_model=schemas.User, tags=["User"], summary="View My Profile")
def read_me(current_user: models.User = Depends(get_current_user)):
    return current_user


@app.put(
    "/users/", response_model=schemas.User, tags=["User"], summary="Update My Profile"
)
def update_user(
    update: schemas.UserUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    db_user = crud.get_user(db, user_id=current_user.id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    return crud.update_user(db, user=db_user, update=update)


@app.delete(
    "/users/", response_model=schemas.User, tags=["User"], summary="Delete My Account"
)
def delete_own_account(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    db_user = crud.del_user(db, user_id=current_user.id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


# Addresses
@app.get(
    "/addresses/",
    response_model=List[schemas.Address],
    tags=["User"],
    summary="List My Addresses",
)
def list_addresses(
    db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)
):
    return crud.get_addresses(db, user_id=current_user.id)


@app.post(
    "/addresses/", response_model=schemas.Address, tags=["User"], summary="Add Address"
)
def add_address(
    address: schemas.AddressCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return crud.create_address(db, user_id=current_user.id, address=address)


@app.put(
    "/addresses/update",
    response_model=schemas.Address,
    tags=["User"],
    summary="Update Address",
)
def update_address(
    update: schemas.AddressUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    db_address = crud.get_address(db, user_id=current_user.id)
    if not db_address:
        raise HTTPException(status_code=404, detail="Address not found")
    return crud.update_address(db=db, db_address=db_address, update=update)


# Cart
@app.get("/cart/", response_model=schemas.Cart, tags=["User"], summary="Get cart")
def get_cart(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    cart = crud.get_cart(db, user_id=current_user.id)
    if not cart:
        cart = crud.create_cart(db, user_id=current_user.id)
    return cart

@app.post("/cart/items", response_model=schemas.CartItem, tags=["User"], summary="Add item to cart")
def add_item_to_cart(item: schemas.CartItemBase, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    cart = crud.get_cart(db, user_id=current_user.id)
    if not cart:
        cart = crud.create_cart(db, user_id=current_user.id)
    try:
        return crud.add_cart_item(db, cart_id=cart.id, item=item)
    except ValueError as e:
        msg = str(e).lower()
        if "not found" in msg:
            raise HTTPException(status_code=404, detail=str(e))
        if "insufficient" in msg:
            raise HTTPException(status_code=400, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))

@app.put("/cart/items/{cart_item_id}", response_model=schemas.CartItem, tags=["User"], summary="Update quantity of a cart item")
def update_cart_item(cart_item_id: int, quantity: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    item = crud.update_cart_item(db, cart_item_id=cart_item_id, quantity=quantity)
    if not item:
        raise HTTPException(status_code=404, detail="Cart item not found")
    if item.cart.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not allowed to modify this item")
    return item

@app.delete("/cart/items/{cart_item_id}", tags=["User"], summary="Remove an item from the cart")
def delete_cart_item(cart_item_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    item = db.query(models.CartItem).filter(models.CartItem.id == cart_item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Cart item not found")
    cart = db.query(models.Cart).filter(models.Cart.id == item.cart_id).first()
    if not cart:
        raise HTTPException(status_code=404, detail="Cart not found")
    if cart.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not allowed to delete this item")

    # Step 4: Delete the item safely
    deleted = crud.remove_cart_item(db, cart_item_id=cart_item_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Cart item not found")

    return {"message": "Cart Item Deleted Successfully"}


# ORDERS 

@app.post("/orders/", response_model=schemas.Order, tags=["User"], summary="Create an order from the cart")
def create_order_from_cart(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    try:
        return crud.create_order_from_cart_for_user(db=db, user_id=current_user.id)
    except ValueError as e:
        msg = str(e).lower()
        # Map resource-not-found errors to 404, empty cart to 400
        if "not found" in msg:
            raise HTTPException(status_code=404, detail=str(e))
        if "empty" in msg:
            raise HTTPException(status_code=400, detail=str(e))
        # fallback
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/orders/", response_model=List[schemas.Order], tags=["User"], summary="List orders for current user")
def get_orders(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    return crud.get_orders(db, user_id=current_user.id)

@app.get("/orders/detail/{order_id}", response_model=schemas.Order, tags=["User"], summary="Get order detail")
def get_order(order_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    order = crud.get_order(db, order_id=order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not allowed to access this order")
    return order


# REVIEWS
@app.post(
    "/reviews/", response_model=schemas.ReviewResponse, status_code=201, tags=["User"]
)
def add_review(
    review: schemas.ReviewCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    try:
        return crud.create_review(db, user_id=current_user.id, review=review)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get(
    "/reviews/{product_id}", response_model=List[schemas.ReviewResponse], tags=["User"]
)
def get_reviews(product_id: int, db: Session = Depends(get_db)):
    return crud.get_reviews_for_product(db, product_id=product_id)


# Seller
@app.post(
    "/products/", response_model=schemas.Product, tags=["Seller"], summary="Add Product"
)
def create_product(
    product: schemas.ProductBase,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_seller),
):
    return crud.create_product(
        db,
        product=product,
        seller_id=current_user.id if current_user.role == "seller" else None,
    )
    # return crud.create_product(db, product=product, seller_id=current_user.id)


@app.get(
    "/seller/products/",
    response_model=List[schemas.Product],
    tags=["Seller"],
    summary="List My Products",
)
def seller_get_products(
    db: Session = Depends(get_db), seller: models.User = Depends(get_current_seller)
):
    return crud.get_products_by_seller(db, seller_id=seller.id)


@app.put(
    "/seller/products/{product_id}",
    response_model=schemas.Product,
    tags=["Seller"],
    summary="Update Product",
)
def seller_update_product(
    product_id: int,
    product_update: schemas.ProductBase,
    db: Session = Depends(get_db),
    seller: models.User = Depends(get_current_seller),
):
    updated = crud.update_product(
        db,
        product_id=product_id,
        update=product_update,
        seller_id=seller.id if seller.role == "seller" else None,
    )
    if not updated:
        raise HTTPException(
            status_code=404, detail="Product not found or not authorized"
        )
    return updated

    # return crud.update_product(db, product_id=product_id, update=product_update, seller_id=seller.id)


@app.delete("/seller/products/{product_id}", tags=["Seller"], summary="Delete Product")
def seller_delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    seller: models.User = Depends(get_current_seller),
):
    deleted = crud.delete_product(
        db, product_id=product_id, user_id=seller.id, user_role=seller.role
    )
    if not deleted:
        raise HTTPException(
            status_code=404, detail="Product not found or not authorized"
        )
    return {"message": "Product deleted successfully"}


# Admin
@app.get(
    "/users/",
    response_model=List[schemas.User],
    tags=["Admin"],
    summary="View All Users",
)
def read_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_admin),
):
    return crud.get_users(db, skip=skip, limit=limit)


@app.put(
    "/admin/users/{user_id}/role",
    response_model=schemas.User,
    tags=["Admin"],
    summary="Update User Role",
)
def admin_update_user_role(
    user_id: int,
    update: schemas.UserUpdate,
    db: Session = Depends(get_db),
    admin: models.User = Depends(get_current_admin),
):
    db_user = crud.get_user(db, user_id=user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    if update.role not in ["customer", "seller", "admin"]:
        raise HTTPException(status_code=400, detail="Invalid role")
    return crud.update_user(db, user=db_user, update=update)


@app.delete(
    "/users/{user_id}",
    response_model=schemas.User,
    tags=["Admin"],
    summary="Delete Any User",
)
def admin_delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin: models.User = Depends(get_current_admin),
):
    db_user = crud.del_user(db, user_id=user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user
