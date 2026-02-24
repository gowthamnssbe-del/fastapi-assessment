"""
User Management Endpoints
Admin-only endpoints for user management
"""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ...db.database import get_db
from ...models.schemas import UserResponse, UserUpdate
from ...models.user import UserRole
from ...services.user_service import UserService
from ...utils.auth import get_current_admin_user, get_current_user
from ...models.user import User

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("", response_model=list[UserResponse])
async def get_users(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Get all users (Admin only)
    
    Args:
        db: Database session
        current_user: Current admin user
    
    Returns:
        List of all users
    """
    from sqlalchemy import select
    
    result = await db.execute(
        select(User).where(User.is_deleted == False)
    )
    users = result.scalars().all()
    
    return [
        UserResponse(
            id=u.id,
            email=u.email,
            username=u.username,
            role=u.role.value,
            is_active=u.is_active,
            created_at=u.created_at,
            updated_at=u.updated_at
        )
        for u in users
    ]


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get user by ID
    
    Regular users can only view their own profile.
    Admins can view any profile.
    
    Args:
        user_id: User UUID
        db: Database session
        current_user: Current user
    
    Returns:
        User data
    
    Raises:
        HTTPException: If user not found or not authorized
    """
    # Check authorization
    if current_user.role != UserRole.ADMIN and str(current_user.id) != str(user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this user"
        )
    
    user = await UserService.get_user_by_id(db, str(user_id))
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserResponse(
        id=user.id,
        email=user.email,
        username=user.username,
        role=user.role.value,
        is_active=user.is_active,
        created_at=user.created_at,
        updated_at=user.updated_at
    )


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: UUID,
    update_data: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update user
    
    Regular users can only update their own profile.
    Admins can update any profile.
    
    Args:
        user_id: User UUID
        update_data: Update data
        db: Database session
        current_user: Current user
    
    Returns:
        Updated user
    
    Raises:
        HTTPException: If user not found or not authorized
    """
    # Check authorization
    if current_user.role != UserRole.ADMIN and str(current_user.id) != str(user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this user"
        )
    
    user = await UserService.get_user_by_id(db, str(user_id))
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    updated_user = await UserService.update_user(db, user, update_data)
    
    return UserResponse(
        id=updated_user.id,
        email=updated_user.email,
        username=updated_user.username,
        role=updated_user.role.value,
        is_active=updated_user.is_active,
        created_at=updated_user.created_at,
        updated_at=updated_user.updated_at
    )


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Soft delete user (Admin only)
    
    Args:
        user_id: User UUID
        db: Database session
        current_user: Current admin user
    
    Raises:
        HTTPException: If user not found
    """
    user = await UserService.get_user_by_id(db, str(user_id))
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    await UserService.delete_user(db, user)
    
    return None


@router.put("/{user_id}/role", response_model=UserResponse)
async def update_user_role(
    user_id: UUID,
    role: UserRole,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Update user role (Admin only)
    
    Args:
        user_id: User UUID
        role: New role
        db: Database session
        current_user: Current admin user
    
    Returns:
        Updated user
    
    Raises:
        HTTPException: If user not found
    """
    user = await UserService.get_user_by_id(db, str(user_id))
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    updated_user = await UserService.update_role(db, user, role)
    
    return UserResponse(
        id=updated_user.id,
        email=updated_user.email,
        username=updated_user.username,
        role=updated_user.role.value,
        is_active=updated_user.is_active,
        created_at=updated_user.created_at,
        updated_at=updated_user.updated_at
    )
