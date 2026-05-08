from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from sqlmodel import Session, select
from typing import List, Optional
from datetime import datetime
import time
from pydantic import BaseModel

from ..database import get_session_context
from ..security import get_current_user
from ..models.user import User
from ..models.workspace import WorkspaceFolder
from ..models.document import Document
from ..utils.logging_util import log_api_call, log_error
from ..scheduler import scheduler, process_single_folder

router = APIRouter()
security = HTTPBearer()

class FolderCreate(BaseModel):
    name: str
    scheduled_for: Optional[datetime] = None

class FolderScheduleUpdate(BaseModel):
    scheduled_for: Optional[datetime] = None
    target_language: Optional[str] = "Turkmen"

class FolderSequentialProcess(BaseModel):
    target_language: Optional[str] = "Turkmen"

class FolderResponse(BaseModel):
    id: int
    name: str
    created_at: datetime
    scheduled_for: Optional[datetime]
    status: str
    document_count: int

@router.get("/", response_model=List[FolderResponse])
def get_folders(
    current_user=Depends(get_current_user),
    session: Session = Depends(get_session_context)
):
    """Get all workspace folders for user"""
    try:
        folders = session.exec(
            select(WorkspaceFolder).where(WorkspaceFolder.user_id == current_user.id).order_by(WorkspaceFolder.created_at.desc())
        ).all()
        
        result = []
        for f in folders:
            doc_count = len(session.exec(select(Document).where(Document.folder_id == f.id)).all())
            result.append(FolderResponse(
                id=f.id,
                name=f.name,
                created_at=f.created_at,
                scheduled_for=f.scheduled_for,
                status=f.status,
                document_count=doc_count
            ))
        return result
    except Exception as e:
        log_error("get_folders", e, current_user.id)
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/", response_model=FolderResponse)
def create_folder(
    folder: FolderCreate,
    current_user=Depends(get_current_user),
    session: Session = Depends(get_session_context)
):
    """Create a new workspace folder"""
    try:
        new_folder = WorkspaceFolder(
            user_id=current_user.id,
            name=folder.name,
            scheduled_for=folder.scheduled_for,
            status="pending"
        )
        session.add(new_folder)
        session.commit()
        session.refresh(new_folder)
        
        if new_folder.scheduled_for and new_folder.scheduled_for > datetime.utcnow():
            job_id = f"process_folder_{new_folder.id}"
            scheduler.add_job(
                process_single_folder,
                trigger="date",
                run_date=new_folder.scheduled_for,
                args=[new_folder.id],
                id=job_id,
                replace_existing=True,
                misfire_grace_time=3600
            )
        
        return FolderResponse(
            id=new_folder.id,
            name=new_folder.name,
            created_at=new_folder.created_at,
            scheduled_for=new_folder.scheduled_for,
            status=new_folder.status,
            document_count=0
        )
    except Exception as e:
        log_error("create_folder", e, current_user.id)
        raise HTTPException(status_code=500, detail="Internal server error")

@router.delete("/{folder_id}")
def delete_folder(
    folder_id: int,
    current_user=Depends(get_current_user),
    session: Session = Depends(get_session_context)
):
    """Delete folder and its documents"""
    folder = session.exec(select(WorkspaceFolder).where(WorkspaceFolder.id == folder_id, WorkspaceFolder.user_id == current_user.id)).first()
    if not folder:
        raise HTTPException(status_code=404, detail="Folder not found")
        
    try:
        docs = session.exec(select(Document).where(Document.folder_id == folder_id)).all()
        for d in docs:
            session.delete(d)
        
        session.delete(folder)
        session.commit()
        return {"message": "Folder deleted successfully"}
    except Exception as e:
        log_error("delete_folder", e, current_user.id)
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/{folder_id}")
def get_folder_details(
    folder_id: int,
    current_user=Depends(get_current_user),
    session: Session = Depends(get_session_context)
):
    """Get folder details and its documents"""
    folder = session.exec(select(WorkspaceFolder).where(WorkspaceFolder.id == folder_id, WorkspaceFolder.user_id == current_user.id)).first()
    if not folder:
        raise HTTPException(status_code=404, detail="Folder not found")
        
    docs = session.exec(select(Document).where(Document.folder_id == folder_id)).all()
    
    return {
        "folder": {
            "id": folder.id,
            "name": folder.name,
            "created_at": folder.created_at,
            "scheduled_for": folder.scheduled_for,
            "status": folder.status
        },
        "documents": [
            {
                "id": d.id,
                "filename": d.filename,
                "status": d.status,
                "submitted_at": d.submitted_at,
                "completed_at": d.completed_at,
                "error_message": d.error_message,
                "has_output": bool(d.output_filepath),
                "target_language": d.target_language
            } for d in docs
        ]
    }

@router.post("/{folder_id}/schedule")
def schedule_folder(
    folder_id: int,
    data: FolderScheduleUpdate,
    current_user=Depends(get_current_user),
    session: Session = Depends(get_session_context)
):
    """Schedule a folder for translation or start immediately"""
    folder = session.exec(select(WorkspaceFolder).where(WorkspaceFolder.id == folder_id, WorkspaceFolder.user_id == current_user.id)).first()
    if not folder:
        raise HTTPException(status_code=404, detail="Folder not found")
    
    target_language = data.target_language or "Turkmen"
    
    folder.scheduled_for = data.scheduled_for
    folder.status = "pending"
    session.add(folder)
    session.commit()
    
    if not folder.scheduled_for or folder.scheduled_for <= datetime.utcnow():
        # Load all pending/failed docs (also allow re-running completed if new language differs)
        docs = session.exec(
            select(Document).where(
                Document.folder_id == folder_id,
                Document.status.in_(["pending", "failed", "completed"])
            )
        ).all()
        
        if not docs:
            return {"message": "No documents to translate", "scheduled_for": None}
        
        # Import the helper to claim keys before spawning threads
        from ..utils.safe_translator import _claim_api_key_index
        from ..utils.api_key_manager import get_all_active_translation_api_keys
        
        api_keys = get_all_active_translation_api_keys(session) or []
        
        for doc in docs:
            # Update language on the document record
            doc.target_language = target_language
            doc.status = "pending"
            doc.error_message = None
            session.add(doc)
        session.commit()
        
        # Assign each document a unique API key index BEFORE spawning threads
        for doc in docs:
            session.refresh(doc)
            if api_keys:
                key_idx = _claim_api_key_index(api_keys)
            else:
                key_idx = None
            thread = Thread(
                target=process_translation_background,
                args=(doc.id, key_idx, target_language)
            )
            thread.start()
    else:
        job_id = f"process_folder_{folder.id}"
        scheduler.add_job(
            process_single_folder,
            trigger="date",
            run_date=folder.scheduled_for,
            args=[folder.id, target_language],
            id=job_id,
            replace_existing=True,
            misfire_grace_time=3600
        )
        
    return {"message": "Folder scheduled successfully", "scheduled_for": folder.scheduled_for}

@router.post("/document/{document_id}/retry")
def retry_document(
    document_id: int,
    current_user=Depends(get_current_user),
    session: Session = Depends(get_session_context)
):
    """Retry a single document translation (any status - forced retry)"""
    document = session.exec(select(Document).where(Document.id == document_id, Document.user_id == current_user.id)).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    was_pending = document.status == "pending"
    document.status = "pending"
    document.error_message = None
    session.add(document)
    session.commit()
    
    thread = Thread(target=process_translation_background, args=(document.id,))
    thread.start()
    
    return {"message": "Translation retried successfully", "was_pending": was_pending}

from fastapi import UploadFile, File, Form
from ..config import settings
from ..security import validate_file_extension
from ..utils.document_validator import validate_document_image
from ..utils.logging_util import log_security_event, log_database_operation, log_translation_process
from ..crud.pricing_crud import get_usage_record as get_usage, increment_usage_count
from ..models.pricing_models import UserSubscription, PricingPlan
import os
from pathlib import Path
from threading import Thread
from ..utils.safe_translator import process_translation_background
import zipfile
import tempfile
from fastapi.responses import FileResponse, StreamingResponse
import io

DAILY_LIMIT = 500

@router.post("/{folder_id}/upload")
def upload_documents_to_folder(
    folder_id: int,
    files: List[UploadFile] = File(...),
    target_language: str = Form("Turkmen"),
    current_user=Depends(get_current_user),
    session: Session = Depends(get_session_context)
):
    """Upload multiple documents to a workspace folder"""
    folder = session.exec(select(WorkspaceFolder).where(WorkspaceFolder.id == folder_id, WorkspaceFolder.user_id == current_user.id)).first()
    if not folder:
        raise HTTPException(status_code=404, detail="Folder not found")

    today = datetime.utcnow().date()
    start_of_day = datetime.combine(today, datetime.min.time())
    user_docs_today = len(session.exec(select(Document).where(Document.user_id == current_user.id, Document.submitted_at >= start_of_day)).all())
    
    if user_docs_today + len(files) > DAILY_LIMIT:
        raise HTTPException(status_code=403, detail=f"Daily translation limit exceeded or not enough quota for {len(files)} files.")

    usage_record = get_usage(session, current_user.id)
    plan_usage = usage_record.translation_count if usage_record else 0
    subscription = session.exec(select(UserSubscription).where(UserSubscription.user_id == current_user.id, UserSubscription.status == "active").order_by(UserSubscription.created_at.desc())).first()
    
    if subscription:
        plan = session.exec(select(PricingPlan).where(PricingPlan.id == subscription.pricing_plan_id)).first()
        if plan and plan_usage + len(files) > plan.max_translation_count:
            raise HTTPException(status_code=403, detail="Plan translation limit exceeded.")
    else:
        raise HTTPException(status_code=403, detail="No active pricing plan.")

    upload_dir = Path("uploads")
    upload_dir.mkdir(exist_ok=True)
    
    uploaded_docs = []
    
    for file in files:
        if not validate_file_extension(file.filename):
            continue
            
        unique_filename = f"{current_user.id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{file.filename}"
        file_path = upload_dir / unique_filename
        
        with open(file_path, "wb") as f:
            f.write(file.file.read())
            
        if validate_document_image(file_path) == "REJECT_NOT_A_DOCUMENT":
            os.remove(file_path)
            continue
            
        document = Document(
            user_id=current_user.id,
            folder_id=folder.id,
            filename=file.filename,
            filepath=str(file_path),
            status="pending",
            submitted_at=datetime.utcnow(),
            target_language=target_language
        )
        session.add(document)
        uploaded_docs.append(document)
        increment_usage_count(session, current_user.id)

    session.commit()
    for doc in uploaded_docs:
        session.refresh(doc)
        log_database_operation("create", "document", doc.id, current_user.id, True, None)
        log_translation_process(doc.id, current_user.id, doc.filename, target_language, "pending")
        
        log_translation_process(doc.id, current_user.id, doc.filename, target_language, "pending")
        
    return {"message": f"Successfully uploaded {len(uploaded_docs)} documents", "uploaded_count": len(uploaded_docs)}

@router.post("/{folder_id}/upload-zip")
def upload_zip_to_folder(
    folder_id: int,
    file: UploadFile = File(...),
    target_language: str = Form("Turkmen"),
    current_user=Depends(get_current_user),
    session: Session = Depends(get_session_context)
):
    """Upload a ZIP file containing images to a workspace folder"""
    folder = session.exec(select(WorkspaceFolder).where(WorkspaceFolder.id == folder_id, WorkspaceFolder.user_id == current_user.id)).first()
    if not folder:
        raise HTTPException(status_code=404, detail="Folder not found")

    if not file.filename.lower().endswith('.zip'):
        raise HTTPException(status_code=400, detail="Only ZIP files are accepted")

    import zipfile
    import io as zipio
    
    zip_contents = file.file.read()
    try:
        zf = zipfile.ZipFile(io.BytesIO(zip_contents))
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid ZIP file")

    allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.tiff', '.tif']
    
    today = datetime.utcnow().date()
    start_of_day = datetime.combine(today, datetime.min.time())
    user_docs_today = len(session.exec(select(Document).where(Document.user_id == current_user.id, Document.submitted_at >= start_of_day)).all())
    
    file_list = zf.namelist()
    valid_image_files = [f for f in file_list if any(f.lower().endswith(ext) for ext in allowed_extensions) and not f.endswith('/') and not f.endswith('\\')]
    
    if user_docs_today + len(valid_image_files) > DAILY_LIMIT:
        raise HTTPException(status_code=403, detail=f"Daily translation limit exceeded. You have {user_docs_today}/{DAILY_LIMIT} today, ZIP has {len(valid_image_files)} files.")

    usage_record = get_usage(session, current_user.id)
    plan_usage = usage_record.translation_count if usage_record else 0
    subscription = session.exec(select(UserSubscription).where(UserSubscription.user_id == current_user.id, UserSubscription.status == "active").order_by(UserSubscription.created_at.desc())).first()
    
    if subscription:
        plan = session.exec(select(PricingPlan).where(PricingPlan.id == subscription.pricing_plan_id)).first()
        if plan and plan_usage + len(valid_image_files) > plan.max_translation_count:
            raise HTTPException(status_code=403, detail="Plan translation limit exceeded.")
    else:
        raise HTTPException(status_code=403, detail="No active pricing plan.")

    upload_dir = Path("uploads")
    upload_dir.mkdir(exist_ok=True)
    
    uploaded_docs = []
    skipped_files = []
    
    for filename in valid_image_files:
        try:
            file_data = zf.read(filename)
            if len(file_data) > settings.MAX_FILE_SIZE:
                skipped_files.append({"filename": filename, "reason": "file too large"})
                continue
            
            unique_filename = f"{current_user.id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{Path(filename).name}"
            file_path = upload_dir / unique_filename
            
            with open(file_path, "wb") as f:
                f.write(file_data)
            
            if validate_document_image(file_path) == "REJECT_NOT_A_DOCUMENT":
                os.remove(file_path)
                skipped_files.append({"filename": filename, "reason": "not a valid document image"})
                continue
            
            document = Document(
                user_id=current_user.id,
                folder_id=folder.id,
                filename=Path(filename).name,
                filepath=str(file_path),
                status="pending",
                submitted_at=datetime.utcnow(),
                target_language=target_language
            )
            session.add(document)
            uploaded_docs.append(document)
            increment_usage_count(session, current_user.id)
        except Exception as e:
            skipped_files.append({"filename": filename, "reason": str(e)})
            continue

    session.commit()
    for doc in uploaded_docs:
        session.refresh(doc)
        log_database_operation("create", "document", doc.id, current_user.id, True, None)
        log_translation_process(doc.id, current_user.id, doc.filename, target_language, "pending")
    
    return {
        "message": f"Extracted {len(uploaded_docs)} images from ZIP",
        "uploaded_count": len(uploaded_docs),
        "uploaded": [{"id": doc.id, "filename": doc.filename, "status": doc.status} for doc in uploaded_docs],
        "skipped": skipped_files
    }

@router.post("/{folder_id}/process-sequential")
def process_folder_sequential(
    folder_id: int,
    data: FolderSequentialProcess,
    current_user=Depends(get_current_user),
    session: Session = Depends(get_session_context)
):
    """Process documents in folder sequentially (one at a time with 4min timeout)"""
    folder = session.exec(select(WorkspaceFolder).where(WorkspaceFolder.id == folder_id, WorkspaceFolder.user_id == current_user.id)).first()
    if not folder:
        raise HTTPException(status_code=404, detail="Folder not found")
    
    target_language = data.target_language or "Turkmen"
    
    docs = session.exec(
        select(Document).where(
            Document.folder_id == folder_id,
            Document.status.in_(["pending", "failed"])
        ).order_by(Document.submitted_at)
    ).all()
    
    if not docs:
        return {"message": "No pending documents to translate", "total_documents": 0}
    
    from ..utils.safe_translator import _claim_api_key_index
    from ..utils.api_key_manager import get_all_active_translation_api_keys
    api_keys = get_all_active_translation_api_keys(session) or []
    
    folder.status = "processing"
    session.add(folder)
    session.commit()
    
    results = {
        "completed": 0,
        "failed": 0,
        "pending": 0,
        "total": len(docs)
    }
    
    current_doc_info = None
    
    for doc in docs:
        doc.target_language = target_language
        doc.status = "processing"
        doc.error_message = None
        session.add(doc)
        session.commit()
        
        key_idx = _claim_api_key_index(api_keys) if api_keys else None
        
        thread = Thread(target=process_translation_background, args=(doc.id, key_idx, target_language))
        thread.start()
        
        current_doc_info = {"id": doc.id, "filename": doc.filename, "status": "processing"}
        
        max_wait_time = 240
        poll_interval = 10
        elapsed = 0
        doc_completed = False
        
        while elapsed < max_wait_time:
            time.sleep(poll_interval)
            elapsed += poll_interval
            
            session.expire(doc)
            session.refresh(doc)
            
            if doc.status == "completed":
                results["completed"] += 1
                doc_completed = True
                break
            elif doc.status == "failed":
                results["failed"] += 1
                doc_completed = True
                break
        
        if not doc_completed:
            doc.status = "failed"
            doc.error_message = "Translation timed out after 4 minutes"
            session.add(doc)
            session.commit()
            results["failed"] += 1
    
    results["pending"] = len([d for d in docs if d.status in ("pending", "processing")])
    
    if doc_completed or results["failed"] > 0:
        if results["pending"] == 0 and results["failed"] == 0:
            folder.status = "completed"
        elif results["completed"] > 0 and results["failed"] > 0:
            folder.status = "completed"
        elif results["completed"] > 0:
            folder.status = "processing"
        else:
            folder.status = "failed"
        session.add(folder)
        session.commit()
    
    return {
        "message": "Sequential processing complete",
        "total_documents": results["total"],
        "completed": results["completed"],
        "failed": results["failed"],
        "pending": results["pending"],
        "current_document": current_doc_info
    }

@router.get("/{folder_id}/status-details")
def get_folder_status_details(
    folder_id: int,
    current_user=Depends(get_current_user),
    session: Session = Depends(get_session_context)
):
    """Get detailed status of all documents in folder"""
    folder = session.exec(select(WorkspaceFolder).where(WorkspaceFolder.id == folder_id, WorkspaceFolder.user_id == current_user.id)).first()
    if not folder:
        raise HTTPException(status_code=404, detail="Folder not found")
    
    docs = session.exec(select(Document).where(Document.folder_id == folder_id)).all()
    
    summary = {"completed": 0, "failed": 0, "processing": 0, "pending": 0}
    for d in docs:
        if d.status in summary:
            summary[d.status] += 1
    
    return {
        "folder": {"id": folder.id, "name": folder.name, "status": folder.status},
        "documents": [
            {
                "id": d.id,
                "filename": d.filename,
                "status": d.status,
                "submitted_at": d.submitted_at,
                "completed_at": d.completed_at,
                "error_message": d.error_message,
                "target_language": d.target_language
            } for d in docs
        ],
        "summary": summary
    }

@router.get("/{folder_id}/download")
def download_folder_zip(
    folder_id: int,
    current_user=Depends(get_current_user),
    session: Session = Depends(get_session_context)
):
    """Download all completed translations in this folder as a ZIP file"""
    folder = session.exec(select(WorkspaceFolder).where(WorkspaceFolder.id == folder_id, WorkspaceFolder.user_id == current_user.id)).first()
    if not folder:
        raise HTTPException(status_code=404, detail="Folder not found")

    # Get completed documents that have output files for this specific folder
    docs = session.exec(
        select(Document).where(
            Document.folder_id == folder_id, 
            Document.user_id == current_user.id,
            Document.status == "completed",
            Document.output_filepath.isnot(None)
        )
    ).all()
    
    # Filter to only include documents with existing output files
    valid_docs = []
    for doc in docs:
        if doc.output_filepath and Path(doc.output_filepath).exists():
            file_size = Path(doc.output_filepath).stat().st_size
            if file_size > 0:
                valid_docs.append(doc)
            else:
                print(f"[WARN] Skipping empty file: {doc.output_filepath} ({doc.filename})")
    
    if not docs:
        raise HTTPException(status_code=404, detail="No completed translations found in this folder. Documents may still be processing.")
    
    if not valid_docs:
        raise HTTPException(status_code=404, detail="Completed documents exist but output files are missing or empty. Please try processing the folder again.")

    # Create ZIP in memory - use original filename for better identification
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for doc in valid_docs:
            if doc.output_filepath and Path(doc.output_filepath).exists():
                # Use original filename without 'translated_' prefix for cleaner naming
                base_name = doc.filename.replace(Path(doc.filename).suffix, '')
                output_name = f"{base_name}_{doc.target_language}.docx"
                zipf.write(doc.output_filepath, arcname=f"translated/{output_name}")
    
    zip_buffer.seek(0)
    
    # Return as streaming response with explicit headers
    headers = {
        "Content-Disposition": f"attachment; filename=folder_{folder_id}_translations.zip",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, OPTIONS",
        "Access-Control-Allow-Headers": "*",
        "Access-Control-Expose-Headers": "Content-Disposition",
    }
    
    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers=headers
    )
