"""
Standard API Response Models and Utilities

Provides consistent response formatting across all API endpoints.
"""

from typing import Any, List, Optional, Dict
from rest_framework.response import Response
from rest_framework import status as http_status


class APIResponse:
    """
    Standard API response model for all endpoints.
    
    Attributes:
        page_no (int): Current page number (1-based)
        page_size (int): Number of items per page
        data (List[Any]): Response data payload
        is_success (bool): Whether the operation was successful
        message (str): Status message or error message
    """
    
    def __init__(
        self,
        data: Any = None,
        is_success: bool = True,
        message: str = "",
        page_no: Optional[int] = None,
        page_size: Optional[int] = None,
        total_record: Optional[int] = None,
    ):
        self.page_no = page_no
        self.page_size = page_size
        self.total_record = total_record
        self.data = data if data is not None else []
        self.is_success = is_success
        self.message = message

    def to_dict(self) -> Dict:
        """Converts response to dictionary format."""
        response_dict = {
            "IsSuccess": self.is_success,
            "Message": self.message,
            "Data": self.data,
        }
        
        # Only include pagination fields if provided
        if self.page_no is not None:
            response_dict["PageNo"] = self.page_no
        if self.page_size is not None:
            response_dict["PageSize"] = self.page_size
        if self.total_record is not None:
            response_dict["TotalRecord"] = self.total_record
            response_dict["TotalPages"] = (self.total_record + self.page_size - 1) // self.page_size
            
        return response_dict

    def to_response(self, status_code: int = http_status.HTTP_200_OK) -> Response:
        """
        Converts response to DRF Response object.
        
        Args:
            status_code: HTTP status code (default: 200 OK)
            
        Returns:
            rest_framework.response.Response
        """
        return Response(self.to_dict(), status=status_code)


# ============ Helper Functions ============

def api_response_success(
    data: Any = None,
    message: str = "Success",
    page_no: Optional[int] = None,
    page_size: Optional[int] = None,
    status_code: int = http_status.HTTP_200_OK,
) -> Response:
    """
    Creates a successful API response.
    
    Args:
        data: Response payload (list or dict)
        message: Success message
        page_no: Page number (optional)
        page_size: Page size (optional)
        status_code: HTTP status code
        
    Returns:
        DRF Response with success data
    """
    response = APIResponse(
        data=data,
        is_success=True,
        message=message,
        page_no=page_no,
        page_size=page_size,
    )
    return response.to_response(status_code)


def api_response_error(
    message: str = "Error",
    data: Any = None,
    status_code: int = http_status.HTTP_400_BAD_REQUEST,
) -> Response:
    """
    Creates an error API response.
    
    Args:
        message: Error message
        data: Additional error details (optional)
        status_code: HTTP status code
        
    Returns:
        DRF Response with error data
    """
    response = APIResponse(
        data=data,
        is_success=False,
        message=message,
    )
    return response.to_response(status_code)


def api_response_paginated(
    data: List[Any],
    page_no: int,
    page_size: int,
    message: str = "Success",
    total_record: Optional[int] = None,
    status_code: int = http_status.HTTP_200_OK,
) -> Response:
    """
    Creates a paginated API response.
    
    Args:
        data: List of items for this page
        page_no: Current page number
        page_size: Items per page
        message: Success message
        total_record: Total number of records (optional)
        status_code: HTTP status code
        
    Returns:
        DRF Response with paginated data
    """
    response = APIResponse(
        data=data,
        is_success=True,
        message=message,
        page_no=page_no,
        page_size=page_size,
        total_record=total_record,
    )
    return response.to_response(status_code)


# ============ Response Format Reference ============

"""
Success Response (GET single record):
{
    "IsSuccess": true,
    "Message": "Success",
    "Data": {
        "id": 1,
        "email": "user@example.com",
        "created_at": "2026-01-20T10:30:00Z"
    }
}

Success Response (GET list without pagination):
{
    "IsSuccess": true,
    "Message": "Success",
    "Data": [
        {"id": 1, "email": "user1@example.com"},
        {"id": 2, "email": "user2@example.com"}
    ]
}

Success Response (GET list with pagination):
{
    "PageNo": 1,
    "PageSize": 10,
    "IsSuccess": true,
    "Message": "Success",
    "Data": [
        {"id": 1, "email": "user1@example.com"},
        {"id": 2, "email": "user2@example.com"}
    ]
}

Error Response:
{
    "IsSuccess": false,
    "Message": "Invalid email or password",
    "Data": null
}
"""
