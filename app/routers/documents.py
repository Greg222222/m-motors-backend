import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.deps import get_current_user
from app.models import Dossier, Document, Role, User
from app.schemas import DocumentOut

router = APIRouter(prefix="/documents", tags=["documents"])

ALLOWED_CONTENT_TYPES = {"application/pdf", "image/jpeg", "image/png"}


def _get_accessible_dossier(dossier_id: int, db: Session, user: User) -> Dossier:
    """A dossier is visible to its owner (client) or to any admin (back-office review)."""
    query = db.query(Dossier).filter(Dossier.id == dossier_id)
    if user.role != Role.admin:
        query = query.filter(Dossier.user_id == user.id)
    dossier = query.first()
    if dossier is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dossier not found")
    return dossier


@router.post("/{dossier_id}", response_model=DocumentOut, status_code=status.HTTP_201_CREATED)
def upload_document(
    dossier_id: int,
    file: UploadFile,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """US-02: client uploads a supporting document (PDF/JPG/PNG, max 5 Mo)."""
    dossier = db.query(Dossier).filter(Dossier.id == dossier_id, Dossier.user_id == user.id).first()
    if dossier is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dossier not found")

    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail="Unsupported file type")

    contents = file.file.read()
    max_bytes = settings.max_upload_size_mb * 1024 * 1024
    if len(contents) > max_bytes:
        raise HTTPException(status_code=status.HTTP_413_CONTENT_TOO_LARGE, detail="File too large")

    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)
    stored_name = f"{uuid.uuid4().hex}_{Path(file.filename or 'document').name}"
    stored_path = upload_dir / stored_name
    stored_path.write_bytes(contents)

    document = Document(
        dossier_id=dossier.id,
        filename=file.filename or stored_name,
        stored_path=str(stored_path),
        content_type=file.content_type,
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    return document


@router.get("/{dossier_id}", response_model=list[DocumentOut])
def list_documents(
    dossier_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    """US-03 (client) / US-06 (back-office): list the documents of a dossier.

    Visible to the dossier's owner, or to any admin reviewing it.
    """
    dossier = _get_accessible_dossier(dossier_id, db, user)
    return db.query(Document).filter(Document.dossier_id == dossier.id).order_by(Document.id).all()


@router.get("/{dossier_id}/{document_id}/file")
def download_document(
    dossier_id: int,
    document_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """US-06: back-office needs to actually open a document to decide on a dossier."""
    dossier = _get_accessible_dossier(dossier_id, db, user)
    document = (
        db.query(Document)
        .filter(Document.id == document_id, Document.dossier_id == dossier.id)
        .first()
    )
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    path = Path(document.stored_path)
    if not path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File missing from storage")
    return FileResponse(path, media_type=document.content_type, filename=document.filename)
