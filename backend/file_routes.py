from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Request, Response
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import uuid
import mimetypes
from datetime import datetime

from database import get_db, User, File as FileModel
from auth import decode_token, get_password_hash
from logging_service import log_action
from config import settings

router = APIRouter(prefix="/files", tags=["Files"])


async def get_current_user_from_token(token: str, db: Session) -> User:
    """Get current user from JWT token."""
    from auth import decode_token
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    payload = decode_token(token)
    if payload is None:
        raise credentials_exception
    
    if payload.get("type") != "access":
        raise credentials_exception
    
    user_id: int = payload.get("sub")
    if user_id is None:
        raise credentials_exception
    
    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None or not user.is_active:
        raise credentials_exception
    
    return user


def get_file_type(filename: str) -> str:
    """Determine if file is image or video based on extension."""
    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff', '.svg'}
    video_extensions = {'.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', '.m4v'}
    
    ext = os.path.splitext(filename)[1].lower()
    
    if ext in image_extensions:
        return 'image'
    elif ext in video_extensions:
        return 'video'
    else:
        # Try to detect using mimetypes
        mime_type, _ = mimetypes.guess_type(filename)
        if mime_type and mime_type.startswith('image'):
            return 'image'
        elif mime_type and mime_type.startswith('video'):
            return 'video'
        return 'other'


@router.post("/upload")
async def upload_files(
    files: List[UploadFile] = File(...),
    current_user: User = Depends(lambda: None),
    request: Request = None,
    db: Session = Depends(get_db)
):
    """Upload multiple files (images or videos)."""
    
    if len(files) > 15:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 15 files allowed per upload"
        )
    
    uploaded_files = []
    
    # Create upload directory if it doesn't exist
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    
    for file in files:
        # Check file size
        file_content = await file.read()
        file_size = len(file_content)
        
        if file_size > settings.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File {file.filename} exceeds maximum size limit"
            )
        
        # Determine file type
        file_type = get_file_type(file.filename)
        
        if file_type not in ['image', 'video']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File {file.filename} is not a supported image or video format"
            )
        
        # Generate unique filename
        file_extension = os.path.splitext(file.filename)[1]
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = os.path.join(settings.UPLOAD_DIR, unique_filename)
        
        # Save file
        with open(file_path, "wb") as buffer:
            buffer.write(file_content)
        
        # Create database record
        db_file = FileModel(
            filename=unique_filename,
            original_filename=file.filename,
            file_path=file_path,
            file_size=file_size,
            file_type=file_type,
            owner_id=current_user.id
        )
        
        db.add(db_file)
        uploaded_files.append(db_file)
    
    db.commit()
    
    for db_file in uploaded_files:
        db.refresh(db_file)
    
    # Log the action
    log_action(
        db=db,
        action="FILES_UPLOADED",
        user_id=current_user.id,
        entity_type="file",
        details=f"Uploaded {len(uploaded_files)} files",
        ip_address=request.client.host if request.client else None
    )
    
    return {
        "message": f"Successfully uploaded {len(uploaded_files)} files",
        "files": [
            {
                "id": f.id,
                "filename": f.original_filename,
                "file_type": f.file_type,
                "file_size": f.file_size,
                "uploaded_at": f.uploaded_at.isoformat()
            }
            for f in uploaded_files
        ]
    }


@router.get("/")
async def list_files(
    current_user: User = Depends(lambda: None),
    db: Session = Depends(get_db),
    file_type: Optional[str] = None
):
    """List all files for the current user."""
    query = db.query(FileModel).filter(FileModel.owner_id == current_user.id)
    
    if file_type:
        query = query.filter(FileModel.file_type == file_type)
    
    files = query.order_by(FileModel.uploaded_at.desc()).all()
    
    return {
        "files": [
            {
                "id": f.id,
                "filename": f.original_filename,
                "file_type": f.file_type,
                "file_size": f.file_size,
                "uploaded_at": f.uploaded_at.isoformat()
            }
            for f in files
        ]
    }


@router.get("/{file_id}")
async def get_file(
    file_id: int,
    current_user: User = Depends(lambda: None),
    db: Session = Depends(get_db),
    request: Request = None
):
    """Get/download a specific file."""
    file_record = db.query(FileModel).filter(
        FileModel.id == file_id,
        FileModel.owner_id == current_user.id
    ).first()
    
    if not file_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    if not os.path.exists(file_record.file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found on server"
        )
    
    # Log the action
    log_action(
        db=db,
        action="FILE_DOWNLOADED",
        user_id=current_user.id,
        entity_type="file",
        entity_id=file_id,
        details=f"Downloaded file {file_record.original_filename}",
        ip_address=request.client.host if request.client else None
    )
    
    # Return file content
    with open(file_record.file_path, "rb") as f:
        file_content = f.read()
    
    media_type, _ = mimetypes.guess_type(file_record.original_filename)
    
    headers = {
        "Content-Disposition": f'attachment; filename="{file_record.original_filename}"'
    }
    
    return Response(
        content=file_content,
        media_type=media_type or "application/octet-stream",
        headers=headers
    )


@router.get("/{file_id}/view")
async def view_file(
    file_id: int,
    current_user: User = Depends(lambda: None),
    db: Session = Depends(get_db),
    request: Request = None
):
    """View a specific file (for images and videos in browser)."""
    file_record = db.query(FileModel).filter(
        FileModel.id == file_id,
        FileModel.owner_id == current_user.id
    ).first()
    
    if not file_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    if not os.path.exists(file_record.file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found on server"
        )
    
    # Log the action
    log_action(
        db=db,
        action="FILE_VIEWED",
        user_id=current_user.id,
        entity_type="file",
        entity_id=file_id,
        details=f"Viewed file {file_record.original_filename}",
        ip_address=request.client.host if request.client else None
    )
    
    # Return file content for viewing
    with open(file_record.file_path, "rb") as f:
        file_content = f.read()
    
    media_type, _ = mimetypes.guess_type(file_record.original_filename)
    
    return Response(
        content=file_content,
        media_type=media_type or "application/octet-stream"
    )


@router.delete("/{file_id}")
async def delete_file(
    file_id: int,
    current_user: User = Depends(lambda: None),
    db: Session = Depends(get_db),
    request: Request = None
):
    """Delete a specific file."""
    file_record = db.query(FileModel).filter(
        FileModel.id == file_id,
        FileModel.owner_id == current_user.id
    ).first()
    
    if not file_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    # Delete file from disk
    if os.path.exists(file_record.file_path):
        os.remove(file_record.file_path)
    
    # Delete database record
    db.delete(file_record)
    db.commit()
    
    # Log the action
    log_action(
        db=db,
        action="FILE_DELETED",
        user_id=current_user.id,
        entity_type="file",
        entity_id=file_id,
        details=f"Deleted file {file_record.original_filename}",
        ip_address=request.client.host if request.client else None
    )
    
    return {"message": "File deleted successfully"}
