"""Tests for documents app models."""

import pytest

from apps.documents.models import Document

pytestmark = pytest.mark.django_db


class TestDocument:
    def test_create_document(self, user, building):
        doc = Document.objects.create(
            title="Test Document",
            description="A sample description",
            document_type=Document.DocumentType.CONTRACT,
            building=building,
            uploaded_by=user,
        )
        assert doc.title == "Test Document"
        assert doc.description == "A sample description"
        assert doc.document_type == Document.DocumentType.CONTRACT
        assert doc.uploaded_by == user
        assert doc.created_at is not None
        assert doc.updated_at is not None

    def test_document_str(self, user, building):
        doc = Document.objects.create(title="Contract 101", building=building, uploaded_by=user)
        assert str(doc) == "Contract 101"

    def test_ordering_by_created_at(self, user, building):
        doc1 = Document.objects.create(title="First", building=building, uploaded_by=user)
        doc2 = Document.objects.create(title="Second", building=building, uploaded_by=user)
        docs = list(Document.objects.all())
        assert docs[0] == doc2
        assert docs[1] == doc1

    def test_uploaded_by_nullable(self, building):
        doc = Document.objects.create(title="Anonymous Upload", building=building)
        assert doc.uploaded_by is None

    def test_related_name_building(self, building, user):
        doc = Document.objects.create(title="Building Doc", building=building, uploaded_by=user)
        assert building.documents.count() == 1
        assert building.documents.first() == doc

    def test_related_name_apartment(self, apartment, user):
        doc = Document.objects.create(title="Apartment Doc", apartment=apartment, uploaded_by=user)
        assert apartment.documents.count() == 1
        assert apartment.documents.first() == doc

    def test_related_name_resident(self, resident, user):
        doc = Document.objects.create(title="Resident Doc", resident=resident, uploaded_by=user)
        assert resident.documents.count() == 1
        assert resident.documents.first() == doc

    def test_related_name_user(self, user, building):
        doc = Document.objects.create(title="User Upload", building=building, uploaded_by=user)
        assert user.uploaded_documents.count() == 1
        assert user.uploaded_documents.first() == doc

    def test_document_type_choices(self):
        assert Document.DocumentType.CONTRACT == "contract"
        assert Document.DocumentType.PROTOCOL == "protocol"
        assert Document.DocumentType.RECEIPT == "receipt"
        assert Document.DocumentType.ACT == "act"
        assert Document.DocumentType.OTHER == "other"
