from pathlib import Path
from django.conf import settings
from django.http import HttpResponse, Http404
from django.utils.timezone import now

from rest_framework import viewsets, permissions
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.decorators import action

from .models import Document
from .serializers import DocumentSerializer
from orgs.models import Membership
from corps.models import Corporation
from django.db.models import QuerySet

from rest_framework import permissions

class IsOrgMember(permissions.BasePermission):
    # Laisse passer tout utilisateur authentifié (l'affichage du formulaire POST reste possible)
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    # Pour les objets (retrieve/delete), on garde la vérification fine
    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser:
            return True
        from orgs.models import Membership
        return Membership.objects.filter(org=obj.corp.org, user=request.user, is_active=True).exists()


class DocumentViewSet(viewsets.ModelViewSet):
    serializer_class = DocumentSerializer
    permission_classes = [permissions.IsAuthenticated, IsOrgMember]
    parser_classes = [MultiPartParser, FormParser]

    def get_queryset(self) -> QuerySet:
        org_ids = Membership.objects.filter(user=self.request.user, is_active=True)\
                                    .values_list("org_id", flat=True)
        return Document.objects.filter(corp__org_id__in=org_ids).order_by("-created_at")

    def perform_create(self, serializer):
        corp = serializer.validated_data["corp"]
        user = self.request.user
        if not user.is_superuser and not Membership.objects.filter(org=corp.org, user=user, is_active=True).exists():
            raise PermissionDenied("Vous devez être membre actif de l'organisation de cette société.")
        serializer.save(uploaded_by=user)

    @action(detail=False, methods=["get"], url_path=r"generate/org-initial/(?P<corp_id>\d+)")
    def generate_org_initial(self, request, corp_id=None):
        try:
            corp = Corporation.objects.select_related("org", "registered_office").get(id=corp_id)
        except Corporation.DoesNotExist:
            raise Http404("Corporation not found")
        if not Membership.objects.filter(org=corp.org, user=request.user, is_active=True).exists():
            return HttpResponse(status=403)

        from docxtpl import DocxTemplate
        tpl = DocxTemplate(str((Path(settings.BASE_DIR) / "templates" / "docx" / "org_initial_fr.docx")))
        context = {
            "corp": {
                "legal_name": corp.legal_name,
                "jurisdiction": corp.jurisdiction,
                "incorporation_number": corp.incorporation_number or "",
                "business_number": corp.business_number or "",
            },
            "date": now().date().strftime("%Y-%m-%d"),
            "address": str(corp.registered_office) if corp.registered_office else "",
        }
        tpl.render(context)
        filename = f"resolution_organisation_{corp.id}.docx"
        response = HttpResponse(content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        tpl.save(response)
        return response
