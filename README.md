# Customer Order Service

Hello,

I've developed a customer order service using Python and Django. It allows users to sign up and log in via OpenID OAuth, while administrators can log in via an API.

**Key Features:**

* Users can be registered as customers.
* Customers can place orders.
* The application is deployed on an AWS EC2 instance.
* A CI/CD pipeline was implemented using Terraform, Ansible, GitHub Actions, and Docker.

You can access the application via this public IP address: [http://54.169.156.141:8000](http://54.169.156.141:8000). Feel free to log in using a Google, Facebook, or GitHub account.

The HTTP part of the application is accessible at the above address. The API collection can be accessed via this Postman link: [https://www.postman.com/winter-spaceship-85249/workspace/savanna-test/collection/27137771-55169650-7c52-46b5-99d5-e063796463e6?action=share&creator=27137771](https://www.postman.com/winter-spaceship-85249/workspace/savanna-test/collection/27137771-55169650-7c52-46b5-99d5-e063796463e6?action=share&creator=27137771)

**API Logic Flow:**

1.  **Admin Registration:** Administrators register by providing the API key: "123456721". Upon successful registration, a token is provided and must be included in all subsequent requests as an "Authorization: Bearer" token.
2.  **Token Refresh:** If the token expires, administrators can log in to obtain a new one.
3.  **User Lookup:** Administrators can retrieve information about registered users.
4.  **Phone Number Addition:** Since OAuth providers may not provide phone numbers, there's an option to add a phone number to existing user accounts.
5.  **Customer Creation:** Administrators can create customer profiles from user accounts.
6.  **Customer and Order Management:** Administrators can:
    * View all customers via the API.
    * Create orders for customers.
    * When an order is created, the customer receives an SMS notification via the "Africas Talking" service.
7.  **Order Confirmation (Mock):** Administrators can simulate a user confirming receipt of an order.
8.  **Order Details Retrieval:** Administrators can retrieve the details of a specific order by providing the order's UUID.
9.  **User Order History:** Administrators can retrieve all orders associated with a specific customer by providing the customer's ID.

**Note:** In this context, "customer" refers to the user.

**API Endpoints**

The base URL is: [http://54.169.156.141:8000/](http://54.169.156.141:8000/)

**ADMIN REGISTER (POST)**

```bash
curl --location 'http://54.169.156.141:8000/api/auth/admin-register/' \
--data-raw '{
    "email":"blabla@gmail.com",
    "phone_number":"+25471232435",
    "password":"////.///Rono123",
    "api_key":"123456721"
}'
```

**ADMIN LOGIN (POST)**

```bash
curl --location 'http://54.169.156.141:8000/api/auth/login/' \
--data '{
    "email":"",
    "password":"",
    "api_key":"123456721"
}'
```

**LOOKUP ALL USERS (POST)**

```bash
curl --location 'http://54.169.156.141:8000/api/lookup/all-users/' \
--data '{
    "page":"1",
    "per_page":"10"
}'
```

**ADD PHONE NUMBER TO A USER (POST)**

```bash
curl --location 'http://54.169.156.141:8000/api/auth/add-user-number/' \
--data '{
    "user_id":"14e10dbc-8953-40c8-b15b-21adb6324805",
    "phone_number":"+254719485369"
}'
```

**CREATE CUSTOMER FROM A USER (POST)**

```bash
curl --location 'http://54.169.156.141:8000/api/auth/create-customer/' \
--data '{
    "user_id":"14e10dbc-8953-40c8-b15b-21adb6324805"
}'
```

**LOOKUP ALL CUSTOMERS (GET)**

```bash
curl http://54.169.156.141:8000/api/lookup/all-customers/
```

**CREATE ORDER (POST)**

```bash
curl --location 'http://54.169.156.141:8000/api/orders/create/' \
--data '{
    "customer_code":"BHTMCDOO",
    "item":"Mango",
    "amount":"420"
}'
```

**GET ORDER (GET)**

```bash
curl http://54.169.156.141:8000/api/orders/ae5bbacb-0e4e-45c9-8e42-0bac18307021/
```

**MOCK USER RECEIVING ORDER (POST)**

```bash
curl --location 'http://54.169.156.141:8000/api/orders/customer-order/confirm/' \
--data '{
    "customer_code":"BHTMCDOO",
    "order_id":"ae5bbacb-0e4e-45c9-8e42-0bac18307021"
}'
```

**SEE ALL ORDERS (POST)**

```bash
curl --location 'http://54.169.156.141:8000/api/orders/all-orders/' \
--data '{
    "customer_code":"BHTMCDOO"
}'
```

**SEE ALL USER ORDERS (POST)**

```bash
curl --location 'http://54.169.156.141:8000/api/orders/customer/all-orders/' \
--data '{
    "customer_code":"BHTMCDOO"
}'
```

For easier testing, please refer to my Postman collection via the provided link.

Thank you.