from fastapi import APIRouter

router = APIRouter(prefix="/users", tags=["users"])

@router.get("")
async def list_user() -> dict[str, list[object]]:
    return {"items": []}

@router.post("/add")
async def add_user() -> dict[str, str]:
    return {"message": "User added successfully"}