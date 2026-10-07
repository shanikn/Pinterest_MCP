# shared helpers for Pinterest's paged list endpoints
MAX_PAGE_SIZE = 250


def check_page_size(page_size: int) -> int:
    if not 1 <= page_size <= MAX_PAGE_SIZE:
        raise ValueError(f"page_size must be between 1 and {MAX_PAGE_SIZE}, got {page_size}.")
    return page_size
