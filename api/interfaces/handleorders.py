import json
import logging

from django.http import JsonResponse
from django.urls import path
from django.views.decorators.csrf import csrf_exempt

from api.interfaces.decorator import auth_required
from api.models import Order, Customer

logger = logging.getLogger(__name__)

class OrdersManager:
    @csrf_exempt
    @auth_required
    def create_order(self, request):
        try:
            data = json.loads(request.body)
            customer_id = data.get("customer_id", "")
            item = data.get("item", "")
            amount = data.get("amount", 0)
            status = data.get("status", "pending")

            if not customer_id:
                return JsonResponse({"error": "Customer ID is required"}, status=400)
            if not item:
                return JsonResponse({"error": "Item is required"}, status=400)
            if not amount:
                return JsonResponse({"error": "Amount is required"}, status=400)

            customer = Customer.objects.filter(id=customer_id).first()

            # Create order in the database
            order = Order.objects.create(
                customer=customer,
                item=item,
                amount=amount,
                status=status
            )
            return JsonResponse({"message": "Order created successfully", "order_id": str(order.id)}, status=201)
        except Exception as ex:
            logger.exception("Error creating order: %s", ex)
            return JsonResponse({"error": str(ex)}, status=500)

    @csrf_exempt
    @auth_required
    def get_order(self, request, order_id):
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
    def get_all_orders(self, request):
        try:
            orders = Order.objects.all().values("id", "customer__id", "item", "amount", "status", "date_created")
            return JsonResponse({"orders": list(orders)}, status=200)
        except Exception as ex:
            logger.exception("Error retrieving all orders: %s", ex)
            return JsonResponse({"error": str(ex)}, status=500)

    @csrf_exempt
    def get_customer_orders(self, request, customer_id):
        try:
            orders = Order.objects.filter(
                customer__id=customer_id).values("id", "item", "amount", "status", "date_created")
            return JsonResponse({"orders": list(orders)}, status=200)
        except Exception as ex:
            logger.exception("Error retrieving customer orders: %s", ex)
            return JsonResponse({"error": str(ex)}, status=500)

    @csrf_exempt
    @auth_required
    def update_order(self, request, order_id):
        try:
            data = json.loads(request.body)
            item = data.get("item", None)
            status = data.get("status", None)
            amount = data.get("amount", None)

            order = Order.objects.get(id=order_id)

            if item:
                order.item = item
            if status:
                order.status = status
            if amount:
                order.amount = amount
            order.save()

            return JsonResponse({"message": "Order updated successfully"}, status=200)
        except Order.DoesNotExist:
            return JsonResponse({"error": "Order not found"}, status=404)
        except Exception as ex:
            logger.exception("Error updating order: %s", ex)
            return JsonResponse({"error": str(ex)}, status=500)

    @csrf_exempt
    @auth_required
    def delete_order(self, request, order_id):
        try:
            order = Order.objects.get(id=order_id)
            order.delete()
            return JsonResponse({"message": "Order deleted successfully"}, status=200)
        except Order.DoesNotExist:
            return JsonResponse({"error": "Order not found"}, status=404)
        except Exception as ex:
            logger.exception("Error deleting order: %s", ex)
            return JsonResponse({"error": str(ex)}, status=500)


urlpatterns = [
    path('orders/create/', OrdersManager().create_order, name='create_order'),
    path('orders/<str:order_id>/', OrdersManager().get_order, name='get_order'),
    path('orders/', OrdersManager().get_all_orders, name='get_all_orders'),
    path('orders/customer/<str:customer_id>/', OrdersManager().get_customer_orders, name='get_customer_orders'),
    path('orders/update/<str:order_id>/', OrdersManager().update_order, name='update_order'),
    path('orders/delete/<str:order_id>/', OrdersManager().delete_order, name='delete_order'),
]