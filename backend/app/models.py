from django.db import models
from django.contrib.auth.models import User


class Transaction(models.Model):
    creditor = models.ForeignKey(
        User,
        related_name='transactions_given',
        on_delete=models.CASCADE)

    debtor = models.ForeignKey(
        User,
        related_name='transactions_received',
        on_delete=models.CASCADE)

    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.debtor.username} owes {self.creditor.username} ${self.amount}'
