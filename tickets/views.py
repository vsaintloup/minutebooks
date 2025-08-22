from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser
from django.http import FileResponse
from django.utils import timezone
from rest_framework import viewsets, permissions, status
from rest_framework.authentication import SessionAuthentication
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from orgs.models import Membership
from .models import Ticket, TicketAttachment
from .serializers import TicketSerializer, TicketCreateSerializer

class IsAuthenticated(permissions.IsAuthenticated):
    pass

def _user_org_ids(user):
    if user.is_staff or user.is_superuser:
        return None  # accès global
    return list(Membership.objects.filter(user=user, is_active=True).values_list("org_id", flat=True))

class TicketViewSet(viewsets.ModelViewSet):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = Ticket.objects.select_related("org", "corp", "created_by", "assigned_to")
        org_ids = _user_org_ids(self.request.user)
        if org_ids is None:
            return qs
        return qs.filter(org_id__in=org_ids)

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return TicketCreateSerializer
        return TicketSerializer

    def perform_create(self, serializer):
        user = self.request.user
        org = serializer.validated_data["org"]
        # Contrôle d’accès : membre actif de l’org ou staff
        if not (user.is_staff or Membership.objects.filter(user=user, org=org, is_active=True).exists()):
            raise PermissionDenied("Vous n'êtes pas membre de cette organisation.")
        ticket = serializer.save(created_by=user, status=Ticket.Status.OPEN)
        # On renvoie la représentation complète
        self._created_ticket = ticket

    def create(self, request, *args, **kwargs):
        resp = super().create(request, *args, **kwargs)
        # Représentation complète (serializer de lecture)
        ticket = getattr(self, "_created_ticket", None)
        if ticket:
            data = TicketSerializer(ticket, context={"request": request}).data
            return Response(data, status=status.HTTP_201_CREATED)
        return resp

    def perform_update(self, serializer):
        # Par défaut, on n'autorise la modif que pour staff/superuser
        user = self.request.user
        if not (user.is_staff or user.is_superuser):
            raise PermissionDenied("Seul le personnel peut modifier un ticket.")
        instance = serializer.save()
        if instance.status == Ticket.Status.DONE and instance.closed_at is None:
            instance.close()

    def _check_member(self, user, org):
        return (
            user.is_staff or user.is_superuser
            or Membership.objects.filter(user=user, org=org, is_active=True).exists()
        )

    def _get_attachment(self, ticket, att_id):
        return ticket.attachments.filter(pk=att_id, is_deleted=False).first()

    @action(detail=True, methods=["get", "post"], url_path="attachments",
            parser_classes=[MultiPartParser, FormParser])
    def attachments(self, request, pk=None):
        ticket = self.get_object()
        if not self._check_member(request.user, ticket.org):
            raise PermissionDenied("Accès refusé.")

        if request.method == "GET":
            qs = ticket.attachments.filter(is_deleted=False).order_by("-created_at")
            data = TicketAttachmentSerializer(qs, many=True, context={"request": request}).data
            return Response(data, status=200)

        f = request.FILES.get("file")
        if not f:
            return Response({"detail": 'Aucun fichier "file" fourni.'}, status=400)
        from django.conf import settings
        max_size = getattr(settings, "MAX_UPLOAD_SIZE", 25 * 1024 * 1024)
        if f.size > max_size:
            return Response({"detail": f"Fichier trop volumineux (> {max_size} octets)."}, status=413)

        att = TicketAttachment.objects.create(
            ticket=ticket,
            file=f,
            original_name=getattr(f, "name", ""),
            content_type=getattr(f, "content_type", ""),
            size=f.size or 0,
            uploaded_by=request.user,
        )
        data = TicketAttachmentSerializer(att, context={"request": request}).data
        return Response(data, status=201)

    @action(detail=True, methods=["delete"], url_path=r"attachments/(?P<att_id>[^/.]+)")
    def delete_attachment(self, request, pk=None, att_id=None):
        ticket = self.get_object()
        if not self._check_member(request.user, ticket.org):
            raise PermissionDenied("Accès refusé.")
        att = self._get_attachment(ticket, att_id)
        if not att:
            return Response({"detail": "Pièce jointe introuvable."}, status=404)
        att.is_deleted = True
        att.deleted_at = timezone.now()
        att.save(update_fields=["is_deleted", "deleted_at"])
        return Response(status=204)

    @action(detail=True, methods=["get"], url_path=r"attachments/(?P<att_id>[^/.]+)/download")
    def download_attachment(self, request, pk=None, att_id=None):
        ticket = self.get_object()
        if not self._check_member(request.user, ticket.org):
            raise PermissionDenied("Accès refusé.")
        att = self._get_attachment(ticket, att_id)
        if not att or not att.file:
            return Response({"detail": "Pièce jointe introuvable."}, status=404)
        # Streaming avec contrôle d’accès (dev). En prod, préférer X-Accel-Redirect / presigned URL S3.
        fh = att.file.open("rb")
        resp = FileResponse(fh, content_type=(att.content_type or "application/octet-stream"))
        filename = att.original_name or att.file.name.rsplit("/", 1)[-1]
        resp["Content-Disposition"] = f'attachment; filename="{filename}"'
        return resp

    @action(detail=True, methods=["post"], url_path=r"attachments/(?P<att_id>[^/.]+)/promote")
    def promote_attachment(self, request, pk=None, att_id=None):
        ticket = self.get_object()
        if not self._check_member(request.user, ticket.org):
            raise PermissionDenied("Accès refusé.")
        att = self._get_attachment(ticket, att_id)
        if not att:
            return Response({"detail": "Pièce jointe introuvable."}, status=404)
        if not ticket.corp_id:
            return Response({"detail": "Ce ticket n'est lié à aucune corporation."}, status=400)

        # Création d’un Document (app documents)
        from documents.models import Document
        doc = Document.objects.create(
            corp_id=ticket.corp_id,
            category="other",
            title=att.original_name or "Pièce jointe",
            file=att.file,  # même fichier; si tu veux dupliquer, gère-le ici
            language="fr",
            uploaded_by=request.user if request.user.is_authenticated else None,
            sha256=getattr(att, "sha256", ""),
        )
        return Response({"document_id": doc.id, "title": doc.title}, status=201)
