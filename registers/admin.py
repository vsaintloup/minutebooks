from django.contrib import admin
from .models import ShareClass, ShareIssuance, ShareTransfer, ShareRedemption, ShareCertificate

@admin.register(ShareClass)
class ShareClassAdmin(admin.ModelAdmin):
    list_display = ("corp", "name", "par_value", "is_voting", "is_redeemable", "is_retractable", "id")
    list_filter = ("corp", "is_voting", "is_redeemable", "is_retractable")
    search_fields = ("name", "corp__legal_name")
    autocomplete_fields = ["corp"]

@admin.register(ShareIssuance)
class ShareIssuanceAdmin(admin.ModelAdmin):
    list_display = ("corp", "share_class", "occurred_on", "to_holder", "quantity", "consideration", "id")
    list_filter = ("corp", "share_class")
    search_fields = ("corp__legal_name",)
    autocomplete_fields = ["corp", "share_class", "to_holder"]

@admin.register(ShareTransfer)
class ShareTransferAdmin(admin.ModelAdmin):
    list_display = ("corp", "occurred_on", "from_holder", "to_holder", "share_class", "quantity", "consideration", "id")
    list_filter = ("corp", "share_class")
    search_fields = ("corp__legal_name",)
    autocomplete_fields = ["corp", "share_class", "from_holder", "to_holder"]

@admin.register(ShareRedemption)
class ShareRedemptionAdmin(admin.ModelAdmin):
    list_display = ("corp", "occurred_on", "share_class", "from_holder", "quantity", "id")
    list_filter = ("corp", "share_class")
    search_fields = ("corp__legal_name",)
    autocomplete_fields = ["corp", "share_class", "from_holder"]

@admin.register(ShareCertificate)
class ShareCertificateAdmin(admin.ModelAdmin):
    list_display = ("corp", "number", "share_class", "holder", "quantity", "issued_on", "cancelled_on", "id")
    list_filter = ("corp", "share_class", "cancelled_on")
    search_fields = ("number", "corp__legal_name",)
    autocomplete_fields = ["corp", "share_class", "holder"]
