import ssl

from django.core.mail.backends.smtp import EmailBackend as SMTPBackend


class InsecureSMTPBackend(SMTPBackend):
    """SMTP backend that skips certificate verification (dev only)."""

    def open(self):
        self.ssl_context = ssl.create_default_context()
        self.ssl_context.check_hostname = False
        self.ssl_context.verify_mode = ssl.CERT_NONE
        return super().open()
