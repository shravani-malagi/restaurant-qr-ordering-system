from django.shortcuts import render, redirect
from .models import (
    Restaurant,
    Category,
    MenuItem,
    Table,
    TableSession,
    Order,
    OrderItem,
)
from django.utils import timezone
from django.shortcuts import get_object_or_404, redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Q

def welcome(request, table_id):

    restaurant = Restaurant.objects.first()

    table = Table.objects.get(id=table_id)
    if table.status == "Occupied":
        return render(request, "menu/table_occupied.html", {
         "table": table
    })

    if request.method == "POST":

        customer_name = request.POST["customer_name"]
        mobile_number = request.POST["mobile_number"]
        if not mobile_number.isdigit() or len(mobile_number) != 10:
            return render(request, "menu/welcome.html", {
                "restaurant": restaurant,
                "table": table,
                "error": "Please enter a valid 10-digit mobile number."
        })

        session = TableSession.objects.create(
            table=table,
            customer_name=customer_name,
            mobile_number=mobile_number
        )
        table.status = "Occupied"
        table.save()

        request.session["session_id"] = session.id

        return redirect("home")

    return render(request, "menu/welcome.html", {
        "restaurant": restaurant,
        "table": table
    })

def home(request):

    search = request.GET.get("search", "")

    categories = Category.objects.prefetch_related("menuitem_set")

    if search:

        categories = Category.objects.prefetch_related(
            "menuitem_set"
        )

        for category in categories:
            category.filtered_items = category.menuitem_set.filter(
                name__icontains=search
            )

    else:

        categories = Category.objects.all()

        for category in categories:
            category.filtered_items = category.menuitem_set.all()

    session_id = request.session.get("session_id")

    customer_name = ""

    if session_id:

        session = get_object_or_404(TableSession, id=session_id)

        if session.status == "Closed":
            request.session.flush()
            return redirect("welcome", table_id=session.table.id)

        customer_name = session.customer_name

    return render(request, "menu/menu.html", {
        "categories": categories,
        "customer_name": customer_name,
        "search": search
    })

def add_to_cart(request, item_id):

    session_id = request.session.get("session_id")

    if not session_id:
        return redirect("home")

    session = get_object_or_404(TableSession, id=session_id)

    if session.status == "Closed":
        request.session.flush()
        return redirect("welcome", table_id=session.table.id)

    cart = request.session.get("cart", {})

    item_id = str(item_id)

    if item_id in cart:
        cart[item_id] += 1
    else:
        cart[item_id] = 1

    request.session["cart"] = cart

    return redirect("home")

def current_order(request):

    cart = request.session.get('cart', {})

    cart_items = []
    total = 0

    for item_id, quantity in cart.items():

        item = MenuItem.objects.get(id=item_id)

        subtotal = item.price * quantity

        total += subtotal

        cart_items.append({
            'item': item,
            'quantity': quantity,
            'subtotal': subtotal
        })

    return render(request, 'menu/current_order.html',
                  {
                      'cart_items': cart_items,
                      'total': total
                  })

def checkout(request):

    cart = request.session.get("cart", {})

    session_id = request.session.get("session_id")

    session = TableSession.objects.get(id=session_id)

    total = 0

    for item_id, quantity in cart.items():

        item = MenuItem.objects.get(id=item_id)

        total += item.price * quantity

    return render(request, "menu/checkout.html", {
        "total": total,
        "table": session.table.table_number,
        "customer_name": session.customer_name
    })

def remove_from_cart(request, item_id):

    cart = request.session.get('cart', {})

    item_id = str(item_id)

    if item_id in cart:

        del cart[item_id]

    request.session['cart'] = cart

    return redirect('current_order')

def increase_quantity(request, item_id):

    cart = request.session.get('cart', {})

    item_id = str(item_id)

    if item_id in cart:
        cart[item_id] += 1

    request.session['cart'] = cart

    return redirect('current_order')

def decrease_quantity(request, item_id):

    cart = request.session.get('cart', {})

    item_id = str(item_id)

    if item_id in cart:

        if cart[item_id] > 1:
            cart[item_id] -= 1
        else:
            del cart[item_id]

    request.session['cart'] = cart

    return redirect('current_order')

def place_order(request):

    if request.method == "POST":

        session_id = request.session.get("session_id")
        session = get_object_or_404(TableSession, id=session_id)

        cart = request.session.get("cart", {})

        # Prevent placing an empty order
        if not cart:
            return redirect("home")

        total = 0

        for item_id, quantity in cart.items():

            item = MenuItem.objects.get(id=item_id)

            total += item.price * quantity

        order = Order.objects.create(
            session=session,
            total_amount=total,
            status="Pending"
        )

        for item_id, quantity in cart.items():

            item = MenuItem.objects.get(id=item_id)

            OrderItem.objects.create(
                order=order,
                menu_item=item,
                quantity=quantity
            )

        # Clear the cart after successful order placement
        request.session["cart"] = {}

        return redirect("success")

    return redirect("home")

def my_orders(request):

    session_id = request.session.get("session_id")

    session = TableSession.objects.get(id=session_id)

    orders = Order.objects.filter(session=session).prefetch_related("items__menu_item").order_by("created_at")

    return render(request, "menu/my_orders.html", {
        "orders": orders
    })

def success(request):

    session_id = request.session.get("session_id")

    session = get_object_or_404(TableSession, id=session_id)

    latest_order = (
        Order.objects
        .filter(session=session)
        .order_by("-created_at")
        .first()
    )

    return render(request, "menu/success.html", {
        "order": latest_order
    })

def request_bill(request):

    session_id = request.session.get("session_id")

    if not session_id:
        return redirect("home")

    session = get_object_or_404(TableSession, id=session_id)

    orders = (
        Order.objects
        .filter(session=session)
        .prefetch_related("items__menu_item")
        .order_by("created_at")
    )

    if not orders.exists():
        return render(request, "menu/request_bill.html", {
            "orders": orders,
            "session": session,
            "grand_total": 0,
            "error": "No orders have been placed yet."
        })

    grand_total = 0

    for order in orders:

        for item in order.items.all():

            item.amount = item.menu_item.price * item.quantity

        grand_total += order.total_amount

    return render(request, "menu/request_bill.html", {
        "orders": orders,
        "session": session,
        "grand_total": grand_total
    })

def payment(request):

    session_id = request.session.get("session_id")

    if not session_id:
        return redirect("home")

    session = get_object_or_404(TableSession, id=session_id)

    # If already paid, go back to welcome page
    if session.is_paid:
        return redirect("welcome", table_id=session.table.id)

    orders = Order.objects.filter(session=session)

    total = sum(order.total_amount for order in orders)

    if request.method == "POST":

        # Close the dining session
        session.is_paid = True
        session.status = "Closed"
        session.closed_at = timezone.now()
        session.save()

        # Make the table available again
        table = session.table
        table.status = "Available"
        table.save()

        # Store table id before clearing session
        table_id = table.id

        # Clear customer session
        request.session.flush()

        # Show thank you page
        return redirect("thank_you", table_id=table_id)

    return render(request, "menu/payment.html", {
        "total": total
    })
def thank_you(request, table_id):

    return render(
        request,
        "menu/thank_you.html",
        {
            "table_id": table_id
        }
    )

@staff_member_required
def admin_orders(request):
    search = request.GET.get("search", "")

    orders = (
        Order.objects
        .filter(status__in=["Pending", "Preparing"])
        .select_related("session__table")
        .prefetch_related("items__menu_item")
        .order_by("-created_at")
    )

    if search:
        orders = orders.filter(
            Q(session__customer_name__icontains=search) |
            Q(session__mobile_number__icontains=search) |
            Q(session__table__table_number__icontains=search)
        )

    return render(request, "menu/admin_orders.html", {
        "orders": orders,
        "pending_count": orders.filter(status="Pending").count(),
        "preparing_count": orders.filter(status="Preparing").count(),
        "served_count": Order.objects.filter(status="Served").count(),
        "total_orders": Order.objects.count(),
        "search": search,
    })

@staff_member_required
def served_orders_history(request):
    search = request.GET.get("search", "")

    orders = (
        Order.objects
        .filter(status="Served")
        .select_related("session__table")
        .prefetch_related("items__menu_item")
        .order_by("-created_at")
    )

    if search:
        orders = orders.filter(
            Q(session__customer_name__icontains=search) |
            Q(session__mobile_number__icontains=search) |
            Q(session__table__table_number__icontains=search)
        )

    return render(request, "menu/served_orders.html", {
        "orders": orders,
        "search": search,
    })

@staff_member_required
def update_order_item_status(request, item_id, status):
    item = get_object_or_404(OrderItem, id=item_id)

    if status not in ["Pending", "Preparing", "Served"]:
        return redirect("admin_orders")

    item.status = status
    item.save()

    order = item.order

    items = order.items.all()

    if items.filter(status="Pending").exists():
        if items.filter(status="Preparing").exists():
            order.status = "Preparing"
        else:
            order.status = "Pending"
    else:
        if items.filter(status="Preparing").exists():
            order.status = "Preparing"
        else:
            order.status = "Served"

    order.save()

    return redirect("admin_orders")