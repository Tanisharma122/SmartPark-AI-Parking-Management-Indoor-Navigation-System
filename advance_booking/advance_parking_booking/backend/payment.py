import time

def process_payment(amount, method="Razorpay"):
    """
    Simulates payment processing.
    Returns transaction ID if successful.
    """
    # Simulate API latency
    time.sleep(1.5)
    return f"TXN_{method.upper()}_{int(time.time())}"
