"""Support session for managing customer interactions"""

from typing import Dict, List, Optional


class OrderItem:
    """Represents an item in the customer's cart"""

    def __init__(self, product_type: str, product_name: str, quantity: int, notes: str = ""):
        self.product_type = product_type
        self.product_name = product_name
        self.quantity = quantity
        self.notes = notes

    def __str__(self):
        base = f"{self.product_type}: {self.product_name} x {self.quantity}"
        if self.notes:
            base += f" (Notes: {self.notes})"
        return base


class SupportSession:
    """Main support session class for customer interactions"""

    def __init__(self, customer_phone: str = "", customer_name: str = ""):
        self.customer_phone = customer_phone
        self.customer_name = customer_name
        self.cart: List[OrderItem] = []
        self.last_product_category: Optional[str] = None

    def add_to_cart(self, product_type: str, product_name: str, quantity: int, notes: str = "") -> bool:
        """Add an item to the cart"""
        if quantity <= 0:
            return False

        # Check if item already exists in cart
        for item in self.cart:
            if item.product_type == product_type and item.product_name == product_name:
                item.quantity += quantity
                if notes:
                    item.notes = notes if not item.notes else f"{item.notes}; {notes}"
                return True

        # Add new item
        self.cart.append(OrderItem(product_type, product_name, quantity, notes))
        return True

    def view_cart(self) -> str:
        """View all items in the cart"""
        if not self.cart:
            return "Your cart is empty. Feel free to ask about our products!"

        lines = ["🛒 **Your Current Order:**\n"]
        divider = "─" * 21
        for i, item in enumerate(self.cart, 1):
            lines.append(divider)
            lines.append(f"📦 **{i}. {item.product_type} — {item.product_name}**")
            lines.append(f"   • Qty: **{item.quantity}**")
            if item.notes:
                lines.append(f"   • 📝 {item.notes}")
        lines.append(divider)

        total_items = len(self.cart)
        total_qty = sum(item.quantity for item in self.cart)
        lines.append(f"\n**{total_items} item{'s' if total_items != 1 else ''}**  |  **Total qty: {total_qty}**")

        return "\n".join(lines)

    def clear_cart(self):
        """Clear all items from cart"""
        self.cart = []

    def get_checkout_summary(self) -> str:
        """Generate checkout summary"""
        if not self.cart:
            return "Your cart is empty. Please add items before checking out."

        display_name = self.customer_name if self.customer_name else "CUSTOMER"
        summary = f"**ORDER SUMMARY FOR {display_name.upper()}**\n\n"
        summary += "=" * 50 + "\n\n"

        for i, item in enumerate(self.cart, 1):
            summary += f"{i}. {item}\n"

        summary += "\n" + "=" * 50 + "\n\n"
        summary += f"**Total Items:** {len(self.cart)}\n"
        summary += f"**Total Quantity:** {sum(item.quantity for item in self.cart)}\n\n"

        summary += "**NEXT STEPS:**\n\n"
        summary += "Thank you for your interest in Kavacch! 🎉\n\n"
        summary += "Our team will contact you shortly with:\n"
        summary += "   • Detailed pricing for your order\n"
        summary += "   • Available customization options\n"
        summary += "   • Delivery timeline\n"
        summary += "   • Any additional information you may need\n\n"
        summary += "**Contact Information:**\n"
        summary += "   📞 9106845371\n"
        summary += "   📞 7600337948\n\n"
        summary += "We look forward to serving you!\n"
        summary += "- Kavacch Team"

        return summary

    def remove_from_cart(self, index: int) -> bool:
        """Remove item from cart by index (1-based)"""
        if 0 < index <= len(self.cart):
            self.cart.pop(index - 1)
            return True
        return False
