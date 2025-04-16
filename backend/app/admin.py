from django.contrib import admin
from .models import Transaction

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('debtor', 'creditor', 'amount', 'created_at')
    search_fields = ('debtor__username', 'creditor__username', 'description')
    list_filter = ('created_at',)
