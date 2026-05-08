import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from sqlmodel import Session, select
from datetime import datetime
from threading import Thread

from .database import engine
from .models.workspace import WorkspaceFolder
from .models.document import Document
from .utils.safe_translator import process_translation_background
from .utils.logging_util import log_error

logger = logging.getLogger(__name__)

def process_single_folder(folder_id: int, target_language: str = "Turkmen"):
    """Process a single folder at its scheduled time"""
    with Session(engine) as session:
        try:
            folder = session.get(WorkspaceFolder, folder_id)
            if not folder or folder.status != "pending":
                logger.info(f"Folder {folder_id} is deleted or already processed.")
                return
                
            logger.info(f"Starting scheduled translation for folder {folder.id} (language={target_language})")
            folder.status = "processing"
            session.add(folder)
            session.commit()
            
            docs = session.exec(select(Document).where(
                Document.folder_id == folder.id,
                Document.status.in_(["pending", "failed"])
            )).all()
            
            # Update language on all documents
            for doc in docs:
                doc.target_language = target_language
                session.add(doc)
            session.commit()

            # Import key-claim helper and load available keys
            from .utils.safe_translator import _claim_api_key_index
            from .utils.api_key_manager import get_all_active_translation_api_keys
            api_keys = get_all_active_translation_api_keys(session) or []
            
            # Assign each doc a unique key BEFORE spawning threads
            for doc in docs:
                session.refresh(doc)
                key_idx = _claim_api_key_index(api_keys) if api_keys else None
                thread = Thread(
                    target=process_translation_background,
                    args=(doc.id, key_idx, target_language)
                )
                thread.start()
                
        except Exception as e:
            logger.error(f"Error processing scheduled folder {folder_id}: {e}")
            session.rollback()
        
jobstores = {
    'default': SQLAlchemyJobStore(engine=engine)
}
scheduler = BackgroundScheduler(jobstores=jobstores)

def start_scheduler():
    if not scheduler.running:
        scheduler.start()
        logger.info("Background scheduler started")

def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown()
        logger.info("Background scheduler stopped")
