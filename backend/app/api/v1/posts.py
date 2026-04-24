from fastapi import APIRouter, HTTPException, status

router = APIRouter(prefix="/posts", tags=["posts"])

def _raise_post_error(exc: Exception) -> None:
    if isinstance(exc, PostNotFoundError):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")

@router.get("")
async def list_posts() -> dict[str, list[object]]:
    return {"items": []}

@router.get("/{id}")
async def get_post(id: int) -> dict[str, object]:
    return {"id": id, "title": "Sample Post", "content": "This is a sample post."}