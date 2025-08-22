from django.db import models
from corps.models import Corporation, Party

class ShareClass(models.Model):
    corp = models.ForeignKey(Corporation, on_delete=models.CASCADE, related_name="share_classes")
    name = models.CharField(max_length=50)  # p.ex. Classe A
    description = models.TextField(blank=True)
    par_value = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    is_voting = models.BooleanField(default=True)
    is_redeemable = models.BooleanField(default=False)
    is_retractable = models.BooleanField(default=False)
    transfer_restrictions = models.TextField(blank=True)

class ShareCertificate(models.Model):
    corp = models.ForeignKey(Corporation, on_delete=models.CASCADE, related_name="certificates")
    share_class = models.ForeignKey(ShareClass, on_delete=models.PROTECT)
    number = models.CharField(max_length=30)  # No. de certificat
    holder = models.ForeignKey(Party, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField()
    issued_on = models.DateField()
    cancelled_on = models.DateField(null=True, blank=True)
    reason_cancelled = models.CharField(max_length=200, blank=True)

class ShareIssuance(models.Model):
    corp = models.ForeignKey(Corporation, on_delete=models.CASCADE)
    share_class = models.ForeignKey(ShareClass, on_delete=models.PROTECT)
    to_holder = models.ForeignKey(Party, on_delete=models.PROTECT, related_name="issuances")
    quantity = models.PositiveIntegerField()
    consideration = models.CharField(max_length=255, blank=True)
    resolution_ref = models.CharField(max_length=255, blank=True)
    occurred_on = models.DateField()

class ShareTransfer(models.Model):
    corp = models.ForeignKey(Corporation, on_delete=models.CASCADE)
    share_class = models.ForeignKey(ShareClass, on_delete=models.PROTECT)
    from_holder = models.ForeignKey(Party, on_delete=models.PROTECT, related_name="transfers_out")
    to_holder = models.ForeignKey(Party, on_delete=models.PROTECT, related_name="transfers_in")
    quantity = models.PositiveIntegerField()
    occurred_on = models.DateField()
    consideration = models.CharField(max_length=255, blank=True)

class ShareRedemption(models.Model):
    corp = models.ForeignKey(Corporation, on_delete=models.CASCADE)
    share_class = models.ForeignKey(ShareClass, on_delete=models.PROTECT)
    from_holder = models.ForeignKey(Party, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField()
    occurred_on = models.DateField()

# Utilitaire: cap table (agrégation ORM)
from django.db.models import Sum

def compute_cap_table(corp: Corporation):
    """Retourne { (holder_id, class_id): qty } en tenant compte émissions, transferts, rachats."""
    result = {}
    # Issuances
    for row in (ShareIssuance.objects
                .filter(corp=corp)
                .values("to_holder", "share_class")
                .annotate(qty=Sum("quantity"))):
        result[(row["to_holder"], row["share_class"])] = result.get((row["to_holder"], row["share_class"]), 0) + row["qty"]
    # Transfers out
    for row in (ShareTransfer.objects
                .filter(corp=corp)
                .values("from_holder", "share_class")
                .annotate(qty=Sum("quantity"))):
        key = (row["from_holder"], row["share_class"])
        result[key] = result.get(key, 0) - row["qty"]
    # Transfers in
    for row in (ShareTransfer.objects
                .filter(corp=corp)
                .values("to_holder", "share_class")
                .annotate(qty=Sum("quantity"))):
        key = (row["to_holder"], row["share_class"])
        result[key] = result.get(key, 0) + row["qty"]
    # Redemptions
    for row in (ShareRedemption.objects
                .filter(corp=corp)
                .values("from_holder", "share_class")
                .annotate(qty=Sum("quantity"))):
        key = (row["from_holder"], row["share_class"])
        result[key] = result.get(key, 0) - row["qty"]
    return result
