from django.core.management.base import BaseCommand
from documents.models import Document

class Command(BaseCommand):
    help = "Calcule sha256 et content_type pour les documents manquants"

    def handle(self, *args, **options):
        qs = Document.objects.all()
        updated = 0
        for doc in qs:
            dirty = False
            if doc.file and (not doc.sha256 or not doc.content_type):
                old_sha, old_ct = doc.sha256, doc.content_type
                doc.sha256 = doc._compute_sha256() or doc.sha256
                doc.content_type = doc._sniff_content_type() or doc.content_type
                if doc.sha256 != old_sha or doc.content_type != old_ct:
                    doc.save(update_fields=["sha256", "content_type"])
                    updated += 1
                    self.stdout.write(f"✓ {doc.id}  sha256={doc.sha256[:8]}…  ct={doc.content_type}")
        self.stdout.write(self.style.SUCCESS(f"Terminé. {updated} document(s) mis à jour."))
