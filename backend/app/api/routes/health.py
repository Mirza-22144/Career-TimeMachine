from fastapi import APIRouter

# Small router just for the health check.
router = APIRouter()


@router.get("/health")
def health():
    """Return a simple ok status. Used to check the server is running."""
    return {"status": "ok"}
