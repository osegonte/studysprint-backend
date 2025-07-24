"""
StudySprint 4.0 - Custom Exceptions
Application-specific exception classes
"""
from fastapi import HTTPException
from typing import Any, Dict, Optional


class StudySprintHTTPException(HTTPException):
    """Base HTTP exception for StudySprint"""
    
    def __init__(
        self,
        status_code: int,
        detail: str,
        headers: Optional[Dict[str, Any]] = None,
        error_code: Optional[str] = None
    ):
        super().__init__(status_code=status_code, detail=detail, headers=headers)
        self.error_code = error_code


class ValidationException(StudySprintHTTPException):
    """Validation error - 422"""
    
    def __init__(self, detail: str, field: Optional[str] = None):
        super().__init__(
            status_code=422,
            detail=detail,
            error_code="VALIDATION_ERROR"
        )
        self.field = field


class NotFoundException(StudySprintHTTPException):
    """Resource not found - 404"""
    
    def __init__(self, resource: str, identifier: Any):
        super().__init__(
            status_code=404,
            detail=f"{resource} with ID {identifier} not found",
            error_code="NOT_FOUND"
        )


class ConflictException(StudySprintHTTPException):
    """Resource conflict - 409"""
    
    def __init__(self, detail: str):
        super().__init__(
            status_code=409,
            detail=detail,
            error_code="CONFLICT"
        )


class FileUploadException(StudySprintHTTPException):
    """File upload error - 400"""
    
    def __init__(self, detail: str):
        super().__init__(
            status_code=400,
            detail=detail,
            error_code="FILE_UPLOAD_ERROR"
        )


class SessionException(StudySprintHTTPException):
    """Session-related error - 400"""
    
    def __init__(self, detail: str):
        super().__init__(
            status_code=400,
            detail=detail,
            error_code="SESSION_ERROR"
        )
