from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.security import HTTPBearer
from sqlmodel import Session, select
from sqlalchemy import func
from ..database import get_session_context
from ..security import get_current_user
from ..models.user import User
from ..models.document import Document
from ..models.pricing_models import UserSubscription, PricingPlan
from ..utils.safe_translator import SafeTranslator
from ..utils.document_validator import validate_document_image
from ..config import settings
from ..utils.logging_util import log_api_call, log_translation_process, log_database_operation, log_error, log_security_event
import tempfile
import os
from pathlib import Path
from datetime import datetime

router = APIRouter()
security = HTTPBearer()

DAILY_LIMIT = 500

@router.post("/upload")
def upload_document_for_translation(
    file: UploadFile = File(...),
    target_language: str = Form("Turkmen"),
    current_user=Depends(get_current_user),
    session: Session = Depends(get_session_context)
):
    """Upload a document for translation"""
    try:
        log_api_call("/translate/upload", "POST", current_user.id, {
            "filename": file.filename,
            "target_language": target_language,
            "file_size": getattr(file, 'size', 'unknown')
        }, 200)
        
        today = datetime.utcnow().date()
        start_of_day = datetime.combine(today, datetime.min.time())
        
        user_docs_today_result = session.exec(
            select(Document).where(
                Document.user_id == current_user.id,
                Document.submitted_at >= start_of_day
            )
        ).all()
        user_docs_today = len(user_docs_today_result)
        
        if user_docs_today >= DAILY_LIMIT:
            log_security_event("translation_limit_exceeded", current_user.id, None, {
                "current_usage": user_docs_today,
                "max_allowed": DAILY_LIMIT
            })
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Daily translation limit exceeded ({DAILY_LIMIT}/day)"
            )
        
        from ..crud.pricing_crud import get_usage_record as get_usage, increment_usage_count
        usage_record = get_usage(session, current_user.id)
        plan_usage = usage_record.translation_count if usage_record else 0
        
        subscription = session.exec(
            select(UserSubscription).where(
                UserSubscription.user_id == current_user.id,
                UserSubscription.status == "active"
            ).order_by(UserSubscription.created_at.desc())
        ).first()
        
        if subscription:
            plan = session.exec(
                select(PricingPlan).where(PricingPlan.id == subscription.pricing_plan_id)
            ).first()
            if plan and plan_usage >= plan.max_translation_count:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Plan translation limit exceeded. You've used {plan_usage}/{plan.max_translation_count} total translations. Please upgrade your plan."
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No active pricing plan. Please select a plan and wait for admin approval."
            )
        
        from ..security import validate_file_extension
        if not validate_file_extension(file.filename):
            log_security_event("invalid_file_type", current_user.id, None, {
                "filename": file.filename,
                "allowed_types": settings.ALLOWED_FILE_EXTENSIONS
            })
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File type not allowed. Allowed types: {', '.join(settings.ALLOWED_FILE_EXTENSIONS)}"
            )
        
        if hasattr(file, 'size') and file.size > settings.MAX_FILE_SIZE:
            log_security_event("file_too_large", current_user.id, None, {
                "file_size": file.size,
                "max_size": settings.MAX_FILE_SIZE
            })
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File too large. Maximum size: {settings.MAX_FILE_SIZE} bytes"
            )
        
        upload_dir = Path("uploads")
        upload_dir.mkdir(exist_ok=True)
        
        unique_filename = f"{current_user.id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{file.filename}"
        file_path = upload_dir / unique_filename
        
        with open(file_path, "wb") as f:
            f.write(file.file.read())
        
        validation_result = validate_document_image(file_path)
        if validation_result == "REJECT_NOT_A_DOCUMENT":
            os.remove(file_path)
            log_security_event("invalid_document_uploaded", current_user.id, None, {
                "filename": file.filename,
                "validation_result": validation_result
            })
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file does not appear to be a valid document with readable text. Only documents with substantial readable text are accepted."
            )
        
        document = Document(
            user_id=current_user.id,
            filename=file.filename,
            filepath=str(file_path),
            status="pending",
            submitted_at=datetime.utcnow(),
            target_language=target_language
        )
        
        session.add(document)
        session.commit()
        session.refresh(document)
        
        increment_usage_count(session, current_user.id)
        
        log_database_operation("create", "document", document.id, current_user.id, True, None)
        log_translation_process(document.id, current_user.id, file.filename, target_language, "pending")
        
        from threading import Thread
        from ..utils.safe_translator import process_translation_background
        
        thread = Thread(target=process_translation_background, args=(document.id,))
        thread.start()
        
        return {
            "message": "Document uploaded successfully",
            "document_id": document.id,
            "status": document.status
        }
    except Exception as e:
        log_error("upload_document_for_translation", e, current_user.id, {
            "filename": file.filename if file else "unknown",
            "target_language": target_language
        })
        raise

@router.get("/status/{document_id}")
def get_translation_status(
    document_id: int, 
    current_user=Depends(get_current_user), 
    session: Session = Depends(get_session_context)
):
    """Get translation status for a document"""
    document = session.exec(
        select(Document).where(
            Document.id == document_id,
            Document.user_id == current_user.id
        )
    ).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    return {
        "id": document.id,
        "filename": document.filename,
        "status": document.status,
        "submitted_at": document.submitted_at,
        "completed_at": document.completed_at,
        "output_filepath": document.output_filepath,
        "error_message": document.error_message
    }

@router.get("/download/{document_id}")
def download_translated_document(
    document_id: int, 
    current_user=Depends(get_current_user), 
    session: Session = Depends(get_session_context)
):
    """Download translated document"""
    document = session.exec(
        select(Document).where(
            Document.id == document_id,
            Document.user_id == current_user.id,
            Document.status == "completed"
        )
    ).first()
    
    if not document or not document.output_filepath:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Translated document not found or not ready"
        )
    
    from fastapi.responses import FileResponse
    
    file_path = Path(document.output_filepath)
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Translated file not found on disk"
        )
    
    return FileResponse(
        path=file_path,
        filename=file_path.name,
        media_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    )