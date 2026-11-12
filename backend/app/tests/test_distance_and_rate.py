"""
Unit tests for distance.py (haversine_km) and rate_calculator.py (select_rate, get_fee_for_company).

Validates: Requirements 10.2, 11.2, 11.3, 11.4
"""

import asyncio
import uuid
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services.distance import haversine_km


# ---------------------------------------------------------------------------
# haversine_km tests
# ---------------------------------------------------------------------------

def test_haversine_same_point_is_zero():
    assert haversine_km(0.0, 0.0, 0.0, 0.0) == 0.0


def test_haversine_known_distance_sao_paulo_rio():
    # São Paulo: -23.5505, -46.6333  /  Rio de Janeiro: -22.9068, -43.1729
    # Known distance ≈ 357 km
    dist = haversine_km(-23.5505, -46.6333, -22.9068, -43.1729)
    assert abs(dist - 357.0) < 5.0


def test_haversine_precision_under_100m():
    # Two points ~1 km apart in São Paulo
    lat1, lng1 = -23.5505, -46.6333
    lat2, lng2 = -23.5595, -46.6333  # ~1 km south
    dist = haversine_km(lat1, lng1, lat2, lng2)
    assert abs(dist - 1.001) < 0.1


def test_haversine_symmetry():
    lat1, lng1 = -23.5505, -46.6333
    lat2, lng2 = -22.9068, -43.1729
    assert haversine_km(lat1, lng1, lat2, lng2) == pytest.approx(haversine_km(lat2, lng2, lat1, lng1))


def test_haversine_returns_float():
    result = haversine_km(0.0, 0.0, 1.0, 1.0)
    assert isinstance(result, float)


def test_haversine_equator_one_degree_longitude():
    dist = haversine_km(0.0, 0.0, 0.0, 1.0)
    assert abs(dist - 111.2) < 0.2


# ---------------------------------------------------------------------------
# select_rate tests
# ---------------------------------------------------------------------------

def _make_rate(min_r, max_r, fee):
    return SimpleNamespace(
        min_radius_km=Decimal(str(min_r)),
        max_radius_km=Decimal(str(max_r)),
        fee=Decimal(str(fee)),
    )


def test_select_rate_returns_matching_fee():
    from app.services.rate_calculator import select_rate

    rates = [_make_rate(0, 5, 10.00), _make_rate(5, 15, 20.00), _make_rate(15, 30, 35.00)]
    assert select_rate(3.0, rates) == Decimal("10.00")
    assert select_rate(10.0, rates) == Decimal("20.00")
    assert select_rate(20.0, rates) == Decimal("35.00")


def test_select_rate_boundary_inclusive():
    from app.services.rate_calculator import select_rate

    rates = [_make_rate(0, 5, 10.00), _make_rate(5, 15, 20.00)]
    # Exact boundary values must match
    assert select_rate(0.0, rates) == Decimal("10.00")
    assert select_rate(5.0, rates) == Decimal("10.00")  # min of second range, but also max of first
    assert select_rate(15.0, rates) == Decimal("20.00")


def test_select_rate_raises_422_when_no_match():
    from fastapi import HTTPException
    from app.services.rate_calculator import select_rate

    rates = [_make_rate(0, 5, 10.00)]
    with pytest.raises(HTTPException) as exc_info:
        select_rate(10.0, rates)
    assert exc_info.value.status_code == 422
    assert exc_info.value.detail["error"] == "DISTANCE_OUT_OF_COVERAGE"


def test_select_rate_empty_rates_raises_422():
    from fastapi import HTTPException
    from app.services.rate_calculator import select_rate

    with pytest.raises(HTTPException) as exc_info:
        select_rate(5.0, [])
    assert exc_info.value.status_code == 422
    assert exc_info.value.detail["error"] == "DISTANCE_OUT_OF_COVERAGE"


# ---------------------------------------------------------------------------
# get_fee_for_company tests (mocked AsyncSession)
# ---------------------------------------------------------------------------

def test_get_fee_for_company_returns_fee():
    from app.services.rate_calculator import get_fee_for_company

    async def _run():
        company_id = uuid.uuid4()
        rate = _make_rate(0, 10, 15.00)

        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [rate]
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        mock_db = AsyncMock()
        mock_db.execute.return_value = mock_result

        fee = await get_fee_for_company(company_id, 5.0, mock_db)
        assert fee == Decimal("15.00")

    asyncio.run(_run())


def test_get_fee_for_company_raises_when_out_of_coverage():
    from fastapi import HTTPException
    from app.services.rate_calculator import get_fee_for_company

    async def _run():
        company_id = uuid.uuid4()
        rate = _make_rate(0, 5, 10.00)

        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [rate]
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        mock_db = AsyncMock()
        mock_db.execute.return_value = mock_result

        with pytest.raises(HTTPException) as exc_info:
            await get_fee_for_company(company_id, 50.0, mock_db)
        assert exc_info.value.status_code == 422
        assert exc_info.value.detail["error"] == "DISTANCE_OUT_OF_COVERAGE"

    asyncio.run(_run())


# ---------------------------------------------------------------------------
# calculate_fee tests (backward-compat, mocked AsyncSession)
# ---------------------------------------------------------------------------

def test_calculate_fee_returns_fee_and_distance():
    from app.services.rate_calculator import calculate_fee

    async def _run():
        company_id = uuid.uuid4()
        rate = _make_rate(0, 10, 15.00)

        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [rate]
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        mock_db = AsyncMock()
        mock_db.execute.return_value = mock_result

        fee, distance_km = await calculate_fee(
            company_id=company_id,
            pickup_lat=-23.5505,
            pickup_lng=-46.6333,
            dest_lat=-23.5595,
            dest_lng=-46.6333,
            db=mock_db,
        )

        assert fee == Decimal("15.00")
        assert isinstance(distance_km, Decimal)
        assert distance_km > Decimal("0")

    asyncio.run(_run())


def test_calculate_fee_raises_422_when_no_rate():
    from fastapi import HTTPException
    from app.services.rate_calculator import calculate_fee

    async def _run():
        company_id = uuid.uuid4()

        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        mock_db = AsyncMock()
        mock_db.execute.return_value = mock_result

        with pytest.raises(HTTPException) as exc_info:
            await calculate_fee(
                company_id=company_id,
                pickup_lat=-23.5505,
                pickup_lng=-46.6333,
                dest_lat=-22.9068,
                dest_lng=-43.1729,
                db=mock_db,
            )

        assert exc_info.value.status_code == 422
        assert exc_info.value.detail["error"] == "DISTANCE_OUT_OF_COVERAGE"

    asyncio.run(_run())
