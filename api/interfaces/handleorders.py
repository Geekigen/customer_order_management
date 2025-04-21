import json
import logging

from django.http import JsonResponse
from django.urls import path
from django.views.decorators.csrf import csrf_exempt
from api.interfaces.jwttokens import login_required
from api.interfaces.smsnotify import SendSms
from api.models import Order, Customer

logger = logging.getLogger(__name__)

class OrdersManager:
    """
    Orders management interface.
    """
    @csrf_exempt
    @login_required
    def create_order(self, request):
        """
        Attempts to create an order.
        @param request: The Django HTTP request received.
        @type request: HttpRequest
        @response with the details.
        """
        try:
            if request.method != "POST":
                return JsonResponse({"error": "Invalid request method,kindly use POST Request"}, status=405)
            data = json.loads(request.body)
            customer_code = data.get("customer_code", "")
            item = data.get("item", "")
            amount = data.get("amount", 0)
            status = "Pending"

            if not customer_code:
                return JsonResponse({"error": "Customer code is required"}, status=400)
            if not item:
                return JsonResponse({"error": "Item is required"}, status=400)
            if not amount:
                return JsonResponse({"error": "Amount is required"}, status=400)

            customer = Customer.objects.filter(code=customer_code).first()

            # Create order in the database
            order = Order.objects.create(
                customer=customer,
                item=item,
                amount=amount,
                status=status
            )
            afrika_feedback = SendSms().send(customer.user.phone_number, f"Dear {customer.name}, your order for {item} has been created successfully. Order ID: {order.id}. Amount: {amount}. Status: {status}. Thank you for your business.")
            return JsonResponse({"message": "Order created successfully", "order_id": str(order.id),"Sms message status":afrika_feedback}, status=201)
        except Exception as ex:
            logger.exception("Error creating order: %s", ex)
            return JsonResponse({"error": str(ex)}, status=500)

    @csrf_exempt
    @login_required
    def get_order(self, request, order_id):
        """
        query an order by ID.
        @param request: The Django HTTP request received.
        @type request: HttpRequest
        @param order_id: The ID of the order to retrieve.
        @type order_id: str
        """
        try:
            order = Order.objects.get(id=order_id)
            order_data = {
                "id": str(order.id),
                "customer_id": str(order.customer.id),
                "item": order.item,
                "amount": order.amount,
                "status": order.status,
                "date_created": order.date_created.isoformat()
            }
            return JsonResponse({"order": order_data}, status=200)
        except Order.DoesNotExist:
            return JsonResponse({"error": "Order not found"}, status=404)
        except Exception as ex:
            logger.exception("Error retrieving order: %s", ex)
            return JsonResponse({"error": str(ex)}, status=500)

    @csrf_exempt
    @login_required
    def get_all_orders(self, request):
        """
        Attempts to get all orders.
        @param request: The Django HTTP request received.
        """
        try:
            orders = Order.objects.all().values("id", "customer__id", "item", "amount", "status", "date_created")
            return JsonResponse({"orders": list(orders)}, status=200)
        except Exception as ex:
            logger.exception("Error retrieving all orders: %s", ex)
            return JsonResponse({"error": str(ex)}, status=500)

    @csrf_exempt
    @login_required
    def get_customer_orders(self, request):
        """
        Attempts to get orders for a specific customer.
        @param request: The Django HTTP request received.

        """
        try:
            if request.method != "POST":
                return JsonResponse({"error": "Invalid request method, kindly use POST Request"}, status=405)
            data = json.loads(request.body)
            customer_code = data.get("customer_code", "")
            if not customer_code:
                return JsonResponse({"error": "Customer code is required"}, status=400)
            customer = Customer.objects.filter(code=customer_code).first()
            if not customer:
                return JsonResponse({"error": "Customer not found"}, status=404)
            orders = Order.objects.filter(
                customer=customer).values("id", "item", "amount", "status", "date_created")
            return JsonResponse({"orders": list(orders)}, status=200)
        except Exception as ex:
            logger.exception("Error retrieving customer orders: %s", ex)
            return JsonResponse({"error": str(ex)}, status=500)

    @csrf_exempt
    @login_required
    def confirm_order(self, request):
        """
        Attempts to confirm an order by ID.
        @param request: The Django HTTP request received.
        @type request: HttpRequest
        @param order_id: The ID of the order to confirm.
        @type order_id: str
        """
        try:
            if request.method != "POST":
                return JsonResponse({"error": "Invalid request method, kindly use POST Request"}, status=405)
            data = json.loads(request.body)
            order_id = data.get("order_id", "")
            if not order_id:
                return JsonResponse({"error": "Order ID is required"}, status=400)
            customer_code = data.get("customer_code", "")
            if not customer_code:
                return JsonResponse({"error": "Customer code is required"}, status=400)
            customer = Customer.objects.filter(code=customer_code).first()
            if not customer:
                return JsonResponse({"error": "Customer not found"}, status=404)
            order = Order.objects.get(id=order_id, customer=customer)
            if order.status != "Pending":
                return JsonResponse({"error": "Order cannot be confirmed"}, status=400)
            order.status = "Confirmed"
            order.save()
            return JsonResponse({"message": "Order confirmed successfully"}, status=200)
        except Order.DoesNotExist:
            return JsonResponse({"error": "Order not found"}, status=404)
        except Exception as ex:
            logger.exception("Error confirming order: %s", ex)
            return JsonResponse({"error": str(ex)}, status=500)





urlpatterns = [
    path('create/', OrdersManager().create_order, name='create_order'),
    path('<str:order_id>/', OrdersManager().get_order, name='get_order'),
    path('', OrdersManager().get_all_orders, name='get_all_orders'),
    path('customer/all-orders/', OrdersManager().get_customer_orders, name='get_customer_orders'),
    path('customer-order/confirm/', OrdersManager().confirm_order, name='confirm_order'),

]