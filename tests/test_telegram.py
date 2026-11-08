from src.models import Product
from src.notifier.telegram import TelegramNotifier


def test_telegram_message_escapes_product_name_and_url():
    notifier = TelegramNotifier("token", "chat")
    product = Product(
        'Hot Wheels <Skyline> & GT-R', 179, 'https://blinkit.com/item?a=1&b="x"',
        "Blinkit", availability="In Stock"
    )
    message = notifier._format_message(product)
    assert "&lt;Skyline&gt;" in message
    assert "&amp; GT-R" in message
    assert '&amp;b=&quot;x&quot;' in message
