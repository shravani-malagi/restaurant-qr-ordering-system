from django.contrib import admin
from django.utils.html import format_html

from .models import (
    Restaurant,
    Category,
    MenuItem,
    Table,
    TableSession,
    Order,
    OrderItem
)


@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):

    list_display = (
        "image_preview",
        "name",
        "category",
        "price",
        "is_veg",
        "available",
    )

    list_filter = (
        "category",
        "is_veg",
        "available",
    )

    search_fields = (
        "name",
        "description",
    )

    def image_preview(self, obj):

        if obj.image:
            return format_html(
                '<img src="{}" width="60" height="60" style="border-radius:8px;object-fit:cover;" />',
                obj.image.url
            )

        return "No Image"

    image_preview.short_description = "Image"


admin.site.register(Restaurant)
admin.site.register(Category)
admin.site.register(Table)
admin.site.register(TableSession)
admin.site.register(Order)
admin.site.register(OrderItem)