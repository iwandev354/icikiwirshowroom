from django import template

register = template.Library()


@register.filter
def rupiah(nilai):
    """12500000 -> 'Rp 12.500.000'"""
    try:
        n = int(nilai)
    except (TypeError, ValueError):
        return nilai
    return "Rp " + f"{n:,}".replace(",", ".")
