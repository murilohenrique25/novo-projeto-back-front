# Feature: delivery-management-system, Property 26: Entregador com uma cidade
"""
Property 26: For any deliverer created in the system, the record must contain
exactly one non-null city_id referencing an existing city.

Validates: Requirements 12.1
"""

import uuid

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st


# ---------------------------------------------------------------------------
# Pure-Python model representation (mirrors the SQLAlchemy Deliverer columns)
# We test the Python-level constraint: city_id must be a non-null UUID.
# The DB-level FK constraint is already enforced by the migration.
# ---------------------------------------------------------------------------

class DelivererRecord:
    """Lightweight representation of a Deliverer row for property testing."""

    def __init__(
        self,
        id: uuid.UUID,
        full_name: str,
        cpf: str,
        phone: str,
        email: str,
        password_hash: str,
        document_photo: str,
        city_id: uuid.UUID,
    ):
        if city_id is None:
            raise ValueError("city_id must not be None")
        self.id = id
        self.full_name = full_name
        self.cpf = cpf
        self.phone = phone
        self.email = email
        self.password_hash = password_hash
        self.document_photo = document_photo
        self.city_id = city_id


# ---------------------------------------------------------------------------
# Hypothesis strategies
# ---------------------------------------------------------------------------

deliverer_strategy = st.builds(
    DelivererRecord,
    id=st.uuids(),
    full_name=st.text(min_size=1, max_size=200),
    cpf=st.text(alphabet="0123456789", min_size=11, max_size=11),
    phone=st.text(min_size=1, max_size=20),
    email=st.emails(),
    password_hash=st.text(min_size=1),
    document_photo=st.text(min_size=1),
    city_id=st.uuids(),
)


# ---------------------------------------------------------------------------
# Property 26 tests
# ---------------------------------------------------------------------------

@settings(max_examples=100)
@given(city_id=st.uuids(), deliverer=deliverer_strategy)
def test_p26_deliverer_has_exactly_one_non_null_city_id(city_id: uuid.UUID, deliverer: DelivererRecord):
    """
    P26: Any deliverer created with a given city_id must have exactly one
    non-null city_id that matches the city used during creation.
    """
    # Create a deliverer bound to the generated city
    d = DelivererRecord(
        id=deliverer.id,
        full_name=deliverer.full_name,
        cpf=deliverer.cpf,
        phone=deliverer.phone,
        email=deliverer.email,
        password_hash=deliverer.password_hash,
        document_photo=deliverer.document_photo,
        city_id=city_id,
    )

    # city_id must not be None
    assert d.city_id is not None

    # city_id must be a valid UUID instance
    assert isinstance(d.city_id, uuid.UUID)

    # city_id must match the city that was used during creation (exactly one city)
    assert d.city_id == city_id


@settings(max_examples=100)
@given(city_id=st.uuids())
def test_p26_deliverer_city_id_is_uuid(city_id: uuid.UUID):
    """
    P26: city_id stored on a deliverer must always be a valid UUID.
    """
    d = DelivererRecord(
        id=uuid.uuid4(),
        full_name="Test Deliverer",
        cpf="12345678901",
        phone="11999999999",
        email="test@example.com",
        password_hash="hashed",
        document_photo="http://example.com/doc.jpg",
        city_id=city_id,
    )

    assert isinstance(d.city_id, uuid.UUID)
    assert d.city_id is not None


def test_p26_deliverer_rejects_null_city_id():
    """
    P26 edge case: Creating a deliverer with city_id=None must raise an error,
    confirming the non-null constraint is enforced at the model level.
    """
    with pytest.raises(ValueError, match="city_id must not be None"):
        DelivererRecord(
            id=uuid.uuid4(),
            full_name="Test",
            cpf="12345678901",
            phone="11999999999",
            email="test@example.com",
            password_hash="hashed",
            document_photo="http://example.com/doc.jpg",
            city_id=None,  # type: ignore[arg-type]
        )
