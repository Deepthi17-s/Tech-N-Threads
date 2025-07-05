from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from carts.models import CartItem 
from .forms import OrderForm
import datetime 
from .models import Order, Payment, OrderProduct 
import json 
from store.models import Product
from django.views.decorators.csrf import csrf_exempt


# -------------------------------
# 💳 Payment (MetaMask or PayPal or Razorpay)
# -------------------------------
@csrf_exempt
def payments(request):
    try:
        body = json.loads(request.body)
        print("💥 payments() called with:", body)

        tx_hash = body.get("txHash")              # ✅ for MetaMask
        payment_method = body.get("payment_method", "MetaMask")
        order_number = body.get("orderID")
        amount_paid = body.get("amount")
        status = body.get("status", "Completed")

        if not tx_hash or not order_number or not amount_paid:
            return JsonResponse({"message": "Missing required fields"}, status=400)

        # ✅ Get the pending order
        order = Order.objects.get(user=request.user, is_ordered=False, order_number=order_number)
        print("✅ Order found:", order.order_number)

        # ✅ Save the payment info
        payment = Payment.objects.create(
            user=request.user,
            payment_id=tx_hash,
            payment_method=payment_method,
            amount_paid=amount_paid,
            status=status
        )
        print("💳 Payment saved:", payment.payment_id)

        # ✅ Link payment and mark order complete
        order.payment = payment
        order.is_ordered = True
        order.status = "Completed"
        order.save()
        print("📦 Order marked as ordered")

        # ✅ Move cart items to OrderProduct
        cart_items = CartItem.objects.filter(user=request.user)
        print("🛒 Cart Items Count:", cart_items.count())

        for item in cart_items:
            orderproduct = OrderProduct.objects.create(
                order=order,
                payment=payment,
                user=request.user,
                product=item.product,
                quantity=item.quantity,
                product_price=item.product.price,
                ordered=True,
            )
            orderproduct.variations.set(item.variations.all())
            orderproduct.save()

            # 🔁 Reduce product stock
            product = item.product
            product.stock -= item.quantity
            product.save()
            print(f"📉 Stock updated: {product.product_name} → {product.stock}")

        # 🧹 Clear the cart
        cart_items.delete()
        print("🧹 Cart cleared")

        return JsonResponse({"message": "Payment successful"})

    except Exception as e:
        print("❌ Error in payments():", e)
        return JsonResponse({"message": f"Error: {str(e)}"}, status=500)


# -------------------------------
# 🛒 Place Order View
# -------------------------------
def place_order(request, total=0, quantity=0):
    current_user = request.user
    cart_items = CartItem.objects.filter(user=current_user)
    cart_count = cart_items.count()
    if cart_count <= 0:
        return redirect('store')

    grand_total = 0
    tax = 0
    for cart_item in cart_items:
        total += (cart_item.product.price * cart_item.quantity)
        quantity += cart_item.quantity
    tax = (2 * total) / 100
    grand_total = total + tax    

    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            data = Order()
            data.user = current_user
            data.first_name = form.cleaned_data['first_name']
            data.last_name = form.cleaned_data['last_name']
            data.phone = form.cleaned_data['phone']
            data.email = form.cleaned_data['email']
            data.address_line_1 = form.cleaned_data['address_line_1']
            data.address_line_2 = form.cleaned_data['address_line_2']
            data.country = form.cleaned_data['country']
            data.state = form.cleaned_data['state']
            data.city = form.cleaned_data['city']
            data.order_note = form.cleaned_data['order_note']
            data.order_total = grand_total
            data.tax = tax
            data.ip = request.META.get('REMOTE_ADDR')
            data.save()

            # Generate order number 
            current_date = datetime.date.today().strftime("%Y%m%d")
            data.order_number = current_date + str(data.id)
            data.save()

            print("📦 Order placed:", data.order_number)

            order = Order.objects.get(user=current_user, is_ordered=False, order_number=data.order_number)
            context = {
                'order': order,
                'cart_items': cart_items,
                'total': total,
                'tax': tax,
                'grand_total': grand_total,
            }
            return render(request, 'orders/payments.html', context)
        else:
            print("❌ Order form invalid")
            return redirect('checkout')


# -------------------------------
# 📄 Order Confirmation Page
# -------------------------------
def order_complete(request):
    order_number = request.GET.get('order_number')
    order = get_object_or_404(Order, order_number=order_number, is_ordered=True)
    context = {
        'order': order,
    }
    return render(request, 'orders/order_complete.html', context)

            