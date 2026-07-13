class InvalidWebhookError(Exception):
    """Raised when Stripe cannot authenticate or decode a webhook payload."""
