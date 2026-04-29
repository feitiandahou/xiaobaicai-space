from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    code: str = Field(..., description="Stable error code")
    detail: str = Field(..., description="Human-readable error message")


class ValidationErrorItem(BaseModel):
    loc: list[str | int] = Field(default_factory=list)
    msg: str
    type: str


class ValidationErrorResponse(ErrorResponse):
    errors: list[ValidationErrorItem] = Field(default_factory=list)