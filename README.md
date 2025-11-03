
# E-Commerce API

## Overview
This repository contains the ER diagram and database design for a typical e-commerce platform.  
The design includes users, products, orders, payments, shipping, and additional optional features like wishlist, coupons, and audit logs.

## ER Diagram
- ![ER Diagram Image](https://github.com/DeepanshuKumar18/Ecommerce-API/blob/main/ER%20%20Diagram.drawio.png)

## Core Entities
- Users
- Admin
- Categories
- Products
- Orders
- Order_Items
- Cart & Cart_Items
- Payments
- Shipping
- Reviews
- Inventory
- Optional: Coupons, Wishlist, Audit_Log

## Relationships
- One-to-Many (1:M): Category → Products, User → Orders, Order → Order_Items
- Many-to-Many (M:N): Users ↔ Products via Cart_Items/Order_Items/Wishlist
- One-to-One (1:1): Order → Payment, Order → Shipping, Product → Inventory

## Tools Used
- ER Diagram: [draw.io]
- Database: PostgreSQL
- Backend: FastAPI, SQLAlchemy
