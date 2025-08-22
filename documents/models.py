from django.db import models
from django.conf import settings
from corps.models import Corporation
import hashlib
import mimetypes

try:
    import magic  # python-magic (libmagic)
except Exception:  # pragma: no cover
    magic = None

class Document(models.Model):
    class Category(models.TextChoices):
        ARTICLES = "ARTICLES", "Statuts/Articles"
        BYLAWS = "BYLAWS", "Règlement intérieur"
        RESOLUTION_SH = "RES_SH", "Résolution des actionnaires"
        RESOLUTION_BD = "RES_BD", "Résolution du CA"
        CERTIFICATE = "CERT", "Certificat d'actions"
        OTHER = "OTHER", "Autre"

    corp = models.ForeignKey(Corporation, on_delete=models.CASCADE, related_name="documents")
    category = models.CharField(max_length=20, choices=Category.choices)
    title = models.CharField(max_length=255)
    file = models.FileField(upload_to="docs/%Y/%m/%d/")
    language = models.CharField(max_length=5, default="fr")
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    sha256 = models.CharField(max_length=64, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    content_type = models.CharField(max_length=120, blank=True)  # ← AJOUT

    def _compute_sha256(self):
        if not self.file:
            return ""
        pos = self.file.tell() if hasattr(self.file, "tell") else 0
        try:
            if hasattr(self.file, "seek"):
                self.file.seek(0)
            h = hashlib.sha256()
            for chunk in iter(lambda: self.file.read(8192), b""):
                h.update(chunk)
            return h.hexdigest()
        finally:
            if hasattr(self.file, "seek"):
                self.file.seek(pos)

    def _sniff_content_type(self):
        if not self.file:
            return ""
        # 1) libmagic (meilleur)
        if magic:
            pos = self.file.tell() if hasattr(self.file, "tell") else 0
            try:
                if hasattr(self.file, "seek"):
                    self.file.seek(0)
                m = magic.Magic(mime=True)
                ctype = m.from_buffer(self.file.read(8192))
                if ctype:
                    return ctype
            except Exception:
                pass
            finally:
                if hasattr(self.file, "seek"):
                    self.file.seek(pos)
        # 2) mimetypes (fallback)
        ctype, _ = mimetypes.guess_type(self.file.name)
        return ctype or "application/octet-stream"

    def save(self, *args, **kwargs):
        # Calcule/complete si manquant (ou si file changé)
        if self.file and (not self.sha256 or not self.content_type):
            self.sha256 = self._compute_sha256() or self.sha256
            self.content_type = self._sniff_content_type() or self.content_type
        super().save(*args, **kwargs)
