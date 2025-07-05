from django.shortcuts import render
from store.models import Product

# -------------------------------
# 🏠 Home View
# -------------------------------
def home(request):
    products = Product.objects.all().filter(is_available=True)
    context = {
        'products': products,
    }
    return render(request, 'home.html', context)

# -------------------------------
# 💸 MetaMask Payment Verification View
# -------------------------------
import time
import json
import requests
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from orders.models import Order, Payment
from accounts.models import Account  # Optional, for future enhancements

# 🔐 Etherscan Sepolia API key
ETHERSCAN_API_KEY = '1YHPXDJKAZSKCSB5ATB7HSWNJUXENIZWWD'

@csrf_exempt
def verify_tx(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            tx_hash = data.get("txHash")
            wallet_address = data.get("user")
            order_number = data.get("orderID")
            amount = data.get("amount")

            if not tx_hash or not wallet_address or not order_number:
                return JsonResponse({"message": "Missing required fields"}, status=400)

            # 🔁 Retry loop: Check transaction confirmation up to 5 times
            confirmed = False
            for attempt in range(5):
                url = (
                    f"https://api-sepolia.etherscan.io/api"
                    f"?module=transaction&action=gettxreceiptstatus"
                    f"&txhash={tx_hash}&apikey={ETHERSCAN_API_KEY}"
                )
                response = requests.get(url)
                result = response.json()

                if result.get("status") == "1" and result["result"].get("status") == "1":
                    confirmed = True
                    break  # ✅ Transaction confirmed

                time.sleep(5)  # ⏱️ Wait 5 seconds before next check

            if not confirmed:
                return JsonResponse({"message": "Transaction not confirmed ❌"}, status=400)

            # ✅ If confirmed: store payment and update order
            try:
                order = Order.objects.get(order_number=order_number, is_ordered=False)

                payment = Payment.objects.create(
                    user=order.user,
                    payment_id=tx_hash,
                    payment_method="MetaMask",
                    amount_paid=amount,
                    status="Completed"
                )

                order.payment = payment
                order.is_ordered = True
                order.status = "Completed"
                order.save()

                return JsonResponse({"message": "Payment verified ✅"})

            except Order.DoesNotExist:
                return JsonResponse({"message": "Order not found"}, status=404)

        except json.JSONDecodeError:
            return JsonResponse({"message": "Invalid JSON"}, status=400)
        except Exception as e:
            return JsonResponse({"message": f"Server error: {str(e)}"}, status=500)

    return JsonResponse({"message": "Invalid request method"}, status=405)
