"""
app/services/resource_service.py

Business logic for the Resource Management module.

Responsibilities
----------------
- Full CRUD (create, read, update, soft-delete)
- Allocate a resource to a disaster (status → allocated)
- Release a resource from a disaster (status → available)
- List with filtering, keyword search, sorting, and pagination
- Transaction rollback on all write failures

Supported resource types (validated at schema level, stored as free-text)
--------------------------------------------------------------------------
food | water | medicine | blankets | vehicles | fuel | medical_kit | generator

Filtering
---------
- resource_type : substring match
- status        : exact ResourceStatus enum match
- location      : substring match
- disaster_id   : match assigned_disaster FK

Search
------
Keyword across resource_type and location (case-insensitive LIKE).

Sorting
-------
- newest       (created_at DESC, default)
- oldest       (created_at ASC)
- type         (resource_type ASC)
- status       (status ASC)
- quantity     (quantity DESC)

All queries use SQLAlchemy 2.0 select() API.
Soft-delete enforced via is_deleted filter on every read.
"""

from __future__ import annotations

import logging
from typing import Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.enums import ResourceStatus
from app.models.resource import Resource
from app.schemas.resource import ResourceCreate, ResourceUpdate

logger = logging.getLogger("app.services.resource_service")

# ---------------------------------------------------------------------------
# Allowed resource type values — validated in service to give clear errors
# ---------------------------------------------------------------------------
ALLOWED_RESOURCE_TYPES: frozenset[str] = frozenset(
    {
        "food",
        "food_packet",
        "water",
        "drinking_water",
        "medicine",
        "blankets",
        "vehicles",
        "rescue_boat",
        "fuel",
        "medical_kit",
        "generator",
    }
)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _get_or_404(db: Session, resource_id: UUID) -> Resource:
    """Load a non-deleted Resource by UUID, or raise HTTP 404."""
    stmt = (
        select(Resource)
        .where(Resource.id == resource_id)
        .where(Resource.is_deleted.is_(False))
    )
    obj = db.execute(stmt).scalar_one_or_none()
    if obj is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Resource with id '{resource_id}' not found.",
        )
    return obj


def _validate_resource_type(resource_type: str) -> str:
    """
    Normalise to lowercase and validate against the allowed type set.

    Raises HTTP 422 for unknown types so callers receive a clear message
    instead of a generic constraint error from the database.
    """
    normalised = resource_type.strip().lower()
    if normalised not in ALLOWED_RESOURCE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                f"Invalid resource_type '{resource_type}'. "
                f"Allowed values: {', '.join(sorted(ALLOWED_RESOURCE_TYPES))}."
            ),
        )
    return normalised


def _apply_filters(
    stmt,
    resource_type: Optional[str],
    filter_status: Optional[ResourceStatus],
    location: Optional[str],
    disaster_id: Optional[UUID],
    search: Optional[str],
):
    """Apply all optional query filters to a select statement."""
    if resource_type:
        stmt = stmt.where(Resource.resource_type.ilike(f"%{resource_type}%"))
    if filter_status:
        stmt = stmt.where(Resource.status == filter_status)
    if location:
        stmt = stmt.where(Resource.location.ilike(f"%{location}%"))
    if disaster_id:
        stmt = stmt.where(Resource.assigned_disaster == disaster_id)
    if search:
        term = f"%{search}%"
        stmt = stmt.where(
            or_(
                Resource.resource_type.ilike(term),
                Resource.location.ilike(term),
            )
        )
    return stmt


def _resolve_sort(sort_by: str):
    """Return the ORDER BY expression(s) for the requested sort_by value."""
    _map = {
        "newest": (Resource.created_at.desc(),),
        "oldest": (Resource.created_at.asc(),),
        "type": (Resource.resource_type.asc(), Resource.created_at.desc()),
        "status": (Resource.status.asc(), Resource.created_at.desc()),
        "quantity": (Resource.quantity.desc(), Resource.created_at.desc()),
    }
    return _map.get(sort_by, (Resource.created_at.desc(),))


# ---------------------------------------------------------------------------
# CRUD
# ---------------------------------------------------------------------------


def create_resource(db: Session, data: ResourceCreate) -> Resource:
    """
    Create and persist a new Resource record.

    Args:
        db:   Active database session.
        data: Validated ResourceCreate payload.

    Returns:
        The newly created Resource ORM instance.

    Raises:
        HTTPException 422: Unknown resource_type.
        HTTPException 500: Database write failure.
    """
    normalised_type = _validate_resource_type(data.resource_type)

    resource = Resource(
        resource_type=normalised_type,
        quantity=data.quantity,
        available_quantity=data.available_quantity,
        location=data.location,
        status=data.status,
        assigned_disaster=data.assigned_disaster,
    )
    try:
        db.add(resource)
        db.commit()
        db.refresh(resource)
    except Exception as exc:
        db.rollback()
        logger.exception("Failed to create resource: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create resource record. Please try again.",
        ) from exc

    logger.info(
        "Resource created: id=%s type=%s qty=%s",
        resource.id,
        resource.resource_type,
        resource.quantity,
    )
    return resource


def get_resource_by_id(db: Session, resource_id: UUID) -> Resource:
    """
    Retrieve a single non-deleted Resource by UUID.

    Args:
        db:          Active database session.
        resource_id: UUID of the resource to fetch.

    Returns:
        The matching Resource ORM instance.

    Raises:
        HTTPException 404: Resource not found or soft-deleted.
    """
    return _get_or_404(db, resource_id)


def list_resources(
    db: Session,
    resource_type: Optional[str] = None,
    filter_status: Optional[ResourceStatus] = None,
    location: Optional[str] = None,
    disaster_id: Optional[UUID] = None,
    search: Optional[str] = None,
    sort_by: str = "newest",
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[Resource], int]:
    """
    Return a filtered, searched, sorted, and paginated list of resources.

    Args:
        db:           Active database session.
        resource_type: Substring filter on resource_type.
        filter_status: Exact match on ResourceStatus.
        location:     Substring filter on location.
        disaster_id:  Filter to resources assigned to this disaster UUID.
        search:       Keyword search across resource_type and location.
        sort_by:      newest | oldest | type | status | quantity.
        page:         1-indexed page number.
        page_size:    Results per page (capped at MAX_PAGE_SIZE by router).

    Returns:
        (list of Resource ORM objects, total matching count)
    """
    base = select(Resource).where(Resource.is_deleted.is_(False))
    base = _apply_filters(
        base,
        resource_type=resource_type,
        filter_status=filter_status,
        location=location,
        disaster_id=disaster_id,
        search=search,
    )

    count_stmt = select(func.count()).select_from(base.subquery())
    total: int = db.execute(count_stmt).scalar_one()

    order_exprs = _resolve_sort(sort_by)
    items_stmt = (
        base.order_by(*order_exprs)
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    resources = list(db.execute(items_stmt).scalars().all())
    return resources, total


def update_resource(
    db: Session,
    resource_id: UUID,
    data: ResourceUpdate,
) -> Resource:
    """
    Partially update a Resource record.

    Only fields explicitly included in the request body are modified.
    Validates resource_type when it is being changed.

    Args:
        db:          Active database session.
        resource_id: UUID of the resource to update.
        data:        Validated ResourceUpdate payload.

    Returns:
        The updated Resource ORM instance.

    Raises:
        HTTPException 404: Resource not found.
        HTTPException 422: Invalid resource_type value.
        HTTPException 500: Database write failure.
    """
    resource = _get_or_404(db, resource_id)
    update_data = data.model_dump(exclude_unset=True)

    if "resource_type" in update_data:
        update_data["resource_type"] = _validate_resource_type(
            update_data["resource_type"]
        )

    # Cross-field quantity guard: if both are present in the patch, check invariant
    new_qty = update_data.get("quantity", resource.quantity)
    new_avail = update_data.get("available_quantity", resource.available_quantity)
    if new_avail > new_qty:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                f"available_quantity ({new_avail}) cannot exceed "
                f"quantity ({new_qty})."
            ),
        )

    for field, value in update_data.items():
        setattr(resource, field, value)

    try:
        db.commit()
        db.refresh(resource)
    except Exception as exc:
        db.rollback()
        logger.exception("Failed to update resource %s: %s", resource_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update resource record. Please try again.",
        ) from exc

    logger.info("Resource updated: id=%s", resource.id)
    return resource


def delete_resource(db: Session, resource_id: UUID) -> None:
    """
    Soft-delete a Resource by setting is_deleted = True.

    Cannot delete a resource that is currently allocated (status = ALLOCATED
    or IN_TRANSIT) — it must be released first.

    Args:
        db:          Active database session.
        resource_id: UUID of the resource to soft-delete.

    Raises:
        HTTPException 400: Resource is currently allocated or in-transit.
        HTTPException 404: Resource not found.
        HTTPException 500: Database write failure.
    """
    resource = _get_or_404(db, resource_id)

    if resource.status in (ResourceStatus.ALLOCATED, ResourceStatus.IN_TRANSIT):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Cannot delete resource '{resource_id}' while its status is "
                f"'{resource.status.value}'. Release it first."
            ),
        )

    resource.is_deleted = True
    try:
        db.commit()
    except Exception as exc:
        db.rollback()
        logger.exception("Failed to delete resource %s: %s", resource_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete resource record. Please try again.",
        ) from exc

    logger.info("Resource soft-deleted: id=%s", resource_id)


# ---------------------------------------------------------------------------
# Allocation operations
# ---------------------------------------------------------------------------


def allocate_resource(
    db: Session,
    resource_id: UUID,
    disaster_id: UUID,
    quantity_to_allocate: int,
) -> Resource:
    """
    Allocate a quantity of a resource to a specific disaster.

    Business rules
    --------------
    - Resource must currently be AVAILABLE.
    - quantity_to_allocate must be > 0 and ≤ available_quantity.
    - After allocation, available_quantity is decremented by quantity_to_allocate.
    - If available_quantity reaches 0 the status is set to ALLOCATED.
    - assigned_disaster is set to the provided disaster UUID.

    Args:
        db:                   Active database session.
        resource_id:          UUID of the resource to allocate.
        disaster_id:          UUID of the target disaster event.
        quantity_to_allocate: How many units to allocate (must be ≥ 1).

    Returns:
        The updated Resource ORM instance.

    Raises:
        HTTPException 400: Invalid quantity, insufficient stock, or wrong status.
        HTTPException 404: Resource not found.
        HTTPException 500: Database write failure.
    """
    resource = _get_or_404(db, resource_id)

    if resource.status not in (ResourceStatus.AVAILABLE, ResourceStatus.ALLOCATED):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Resource '{resource_id}' cannot be allocated from its current "
                f"status '{resource.status.value}'. "
                "Only 'available' or partially 'allocated' resources can be allocated."
            ),
        )

    if quantity_to_allocate <= 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="quantity_to_allocate must be a positive integer (≥ 1).",
        )

    if quantity_to_allocate > resource.available_quantity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Requested quantity {quantity_to_allocate} exceeds "
                f"available stock {resource.available_quantity} "
                f"for resource '{resource_id}'."
            ),
        )

    resource.available_quantity -= quantity_to_allocate
    resource.assigned_disaster = disaster_id
    resource.status = (
        ResourceStatus.AVAILABLE
        if resource.available_quantity > 0
        else ResourceStatus.ALLOCATED
    )

    try:
        db.commit()
        db.refresh(resource)
    except Exception as exc:
        db.rollback()
        logger.exception(
            "Failed to allocate resource %s to disaster %s: %s",
            resource_id, disaster_id, exc,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to allocate resource. Please try again.",
        ) from exc

    logger.info(
        "Resource allocated: id=%s qty=%s disaster=%s remaining=%s",
        resource.id,
        quantity_to_allocate,
        disaster_id,
        resource.available_quantity,
    )
    return resource


def release_resource(
    db: Session,
    resource_id: UUID,
    quantity_to_release: int,
) -> Resource:
    """
    Release a previously allocated quantity back into available stock.

    Business rules
    --------------
    - Resource must currently be ALLOCATED or IN_TRANSIT.
    - quantity_to_release must be > 0 and ≤ (quantity − available_quantity).
    - available_quantity is incremented by quantity_to_release.
    - If available_quantity equals quantity, status reverts to AVAILABLE and
      assigned_disaster is cleared.
    - Otherwise status remains ALLOCATED.

    Args:
        db:                  Active database session.
        resource_id:         UUID of the resource to release.
        quantity_to_release: How many units to release back into stock.

    Returns:
        The updated Resource ORM instance.

    Raises:
        HTTPException 400: Invalid quantity or wrong status.
        HTTPException 404: Resource not found.
        HTTPException 500: Database write failure.
    """
    resource = _get_or_404(db, resource_id)

    if resource.status not in (ResourceStatus.ALLOCATED, ResourceStatus.IN_TRANSIT):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Resource '{resource_id}' is not currently allocated "
                f"(status: '{resource.status.value}'). Nothing to release."
            ),
        )

    if quantity_to_release <= 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="quantity_to_release must be a positive integer (≥ 1).",
        )

    allocated_qty = resource.quantity - resource.available_quantity
    if quantity_to_release > allocated_qty:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Cannot release {quantity_to_release} units — only "
                f"{allocated_qty} units are currently allocated "
                f"for resource '{resource_id}'."
            ),
        )

    resource.available_quantity += quantity_to_release

    if resource.available_quantity >= resource.quantity:
        resource.available_quantity = resource.quantity
        resource.status = ResourceStatus.AVAILABLE
        resource.assigned_disaster = None
    else:
        resource.status = ResourceStatus.ALLOCATED

    try:
        db.commit()
        db.refresh(resource)
    except Exception as exc:
        db.rollback()
        logger.exception("Failed to release resource %s: %s", resource_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to release resource. Please try again.",
        ) from exc

    logger.info(
        "Resource released: id=%s qty_released=%s new_available=%s status=%s",
        resource.id,
        quantity_to_release,
        resource.available_quantity,
        resource.status.value,
    )
    return resource
