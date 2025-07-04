# Shophive

Shophive is a feature-rich e-commerce platform built with **Django**, designed as a practice and learning tool to demonstrate core e-commerce functionalities. It offers a robust and flexible shopping experience with features like product management, dynamic checkout, order tracking, and more. The platform is hosted on AWS with a PostgreSQL database for scalable data management, making it suitable for learning and prototyping advanced e-commerce workflows.

## Live Site

[https://shophive.net.in/](https://shophive.net.in/)

## Features

### User Features
- **User Authentication**: Secure sign-up, login, logout, and Google OAuth integration for seamless access.
- **Product Browsing**: Browse products by categories, view detailed product pages with variants (e.g., size, color), and use search functionality.
- **Wishlist**: Add or remove products dynamically using AJAX, with toggle functionality for intuitive user interaction.
- **Checkout**: 
  - Apply discount coupons and wallet payments.
  - Manage addresses via an AJAX-powered modal to preserve form state (payment method, coupon, wallet).
  - Select shipping or billing addresses with primary address support.
- **Order Management**: Track order status, cancel orders post-delivery, and view order history.
- **Returns**: Request returns for specific items, with admin approval workflow.

### Admin Features
- **Product Management**: Add, edit, delete, and restore products using soft-delete to prevent data loss.
- **Sales Reporting**: Generate and filter sales reports by date, with export options in PDF and Excel formats.
- **Notifications**: Send actionable notifications to users (e.g., order updates, promotions) with clickable links.

### Technical Features
- **PostgreSQL Database**: Hosted on AWS RDS for high performance and scalability.
- **Dynamic Pricing**: Supports sale prices, discount coupons, and wallet deductions for flexible pricing.
- **Wallet System**: Manage user wallets for payments and refunds, integrated with checkout.
- **Responsive Design**: Built with Bootstrap for mobile and desktop compatibility.
- **AJAX**: Enables dynamic updates for wishlist toggling, address addition, and cart interactions without page reloads.
- **Soft-Delete**: Prevents accidental data loss with reversible deletion for products and other entities.

## Technologies Used
- **Backend**: Django 4.x
- **Frontend**: Bootstrap 5, jQuery 3.7.1 (for AJAX), Zooming.js (for product image zoom)
- **Database**: PostgreSQL (Hosted on AWS RDS)
- **Hosting**: AWS EC2 with Gunicorn and Nginx
- **Version Control**: GitHub
- **Other Libraries**: Django humanize for formatting, ReportLab for PDF generation

## Prerequisites
To set up and run Shophive locally, ensure you have the following installed:
- Python 3.8+
- PostgreSQL 13+
- Git
- Virtualenv (recommended)
- AWS CLI (optional, for deployment)
- Node.js (optional, for managing frontend assets if extended)

## Setup Instructions

### 1. Clone the Repository
```bash
git clone https://github.com/<your-username>/shophive.git
cd shophive
```

### 2. Set Up a Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure PostgreSQL Database
1. Install PostgreSQL and create a database:
   ```bash
   psql -U postgres
   CREATE DATABASE shophive;
   ```
2. Update `settings.py` with your database credentials:
   ```python
   DATABASES = {
       'default': {
           'ENGINE': 'django.db.backends.postgresql',
           'NAME': 'shophive',
           'USER': 'your_postgres_user',
           'PASSWORD': 'your_postgres_password',
           'HOST': 'localhost',
           'PORT': '5432',
       }
   }
   ```

### 5. Set Up Environment Variables
Create a `.env` file in the project root for sensitive settings:
```
DATABASE_URL=postgres://your_postgres_user:your_postgres_password@localhost:5432/shophive
SECRET_KEY=your_django_secret_key
DEBUG=True
```

Install `python-decouple` and update `settings.py` to use `.env`:
```bash
pip install python-decouple
```
```python
from decouple import config
SECRET_KEY = config('SECRET_KEY')
DEBUG = config('DEBUG', default=False, cast=bool)
DATABASES['default'] = config('DATABASE_URL')
```

### 6. Run Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### 7. Collect Static Files
```bash
python manage.py collectstatic
```

### 8. Create a Superuser
```bash
python manage.py createsuperuser
```

### 9. Run the Development Server
```bash
python manage.py runserver
```
Access the site at `http://localhost:8000` and the admin panel at `http://localhost:8000/admin`.
