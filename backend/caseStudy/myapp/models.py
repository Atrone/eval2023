from django.db import models


class Address(models.Model):
    address = models.CharField(max_length=200)
    total_received = models.PositiveBigIntegerField()
    total_sent = models.PositiveBigIntegerField()
    balance = models.BigIntegerField()
    unconfirmed_balance = models.BigIntegerField()
    final_balance = models.BigIntegerField()
    n_tx = models.PositiveIntegerField()
    unconfirmed_n_tx = models.PositiveIntegerField()
    final_n_tx = models.PositiveIntegerField()
    tx_url = models.URLField(blank=True)

    # Timestamp
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.address
