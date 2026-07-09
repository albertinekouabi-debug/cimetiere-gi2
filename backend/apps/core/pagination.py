from ninja import Schema
from typing import TypeVar

T = TypeVar("T")


class PagedResponse(Schema):
    """Réponse paginée simple pour les listes volumineuses."""
    count: int
    page: int
    page_size: int
    results: list


def paginate_queryset(qs, page: int = 1, page_size: int = 20):
    page = max(page, 1)
    page_size = min(max(page_size, 1), 100)
    start = (page - 1) * page_size
    end = start + page_size
    return {
        "count": qs.count(),
        "page": page,
        "page_size": page_size,
        "results": list(qs[start:end]),
    }
