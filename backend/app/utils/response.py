"""
app/utils/response.py

Standardised API response envelope helpers.

All API responses are wrapped in a consistent envelope so that clients
always receive a predictable JSON structure:

    {
        "success": true | false,
        "message": "Human-readable description",
        "data": { ... } | null,
        "errors": null | [ ... ]
    }
"""

from typing import Any

from fastapi.responses import JSONResponse


def success_response(
    data: Any = None,
    message: str = "Request processed successfully.",
    status_code: int = 200,
) -> JSONResponse:
    """
    Build a standardised success JSON response.

    Args:
        data: The payload to return inside the envelope.
        message: A human-readable success message.
        status_code: HTTP status code (default 200).

    Returns:
        FastAPI JSONResponse with the standard envelope.
    """
    return JSONResponse(
        status_code=status_code,
        content={
            "success": True,
            "message": message,
            "data": data,
            "errors": None,
        },
    )


def error_response(
    message: str = "An unexpected error occurred.",
    errors: list[Any] | None = None,
    status_code: int = 400,
) -> JSONResponse:
    """
    Build a standardised error JSON response.

    Args:
        message: A human-readable error summary.
        errors: Optional list of detailed error objects.
        status_code: HTTP status code (default 400).

    Returns:
        FastAPI JSONResponse with the standard envelope.
    """
    return JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "message": message,
            "data": None,
            "errors": errors or [],
        },
    )


def paginated_response(
    data: list[Any],
    total: int,
    page: int,
    page_size: int,
    message: str = "Data retrieved successfully.",
    status_code: int = 200,
) -> JSONResponse:
    """
    Build a standardised paginated success response.

    Args:
        data: The current page's list of items.
        total: Total number of items across all pages.
        page: Current page number (1-indexed).
        page_size: Number of items per page.
        message: A human-readable success message.
        status_code: HTTP status code (default 200).

    Returns:
        FastAPI JSONResponse with pagination metadata in the envelope.
    """
    total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0
    return JSONResponse(
        status_code=status_code,
        content={
            "success": True,
            "message": message,
            "data": data,
            "errors": None,
            "pagination": {
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages,
            },
        },
    )
