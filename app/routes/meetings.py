import json
from fastapi import APIRouter, Depends, HTTPException, Request, Form, BackgroundTasks
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlalchemy.orm import Session
from app.models.database import get_db
from app.models.meeting import Meeting, MeetingMinute
from app.models.user import User
from app.services.auth_service import decode_access_token
from app.services.bot_service import join_and_record_meeting
from app.services.transcriber import transcribe_audio
from app.services.summarizer import summarize_transcript
from app.templates import templates

router = APIRouter(prefix="/meetings", tags=["meetings"])


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    user_id = int(payload.get("sub"))
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


async def process_meeting(meeting_id: int, meet_link: str, title: str):
    """Background task: join meeting, capture audio, transcribe, summarize."""
    from app.models.database import SessionLocal

    session = SessionLocal()

    async def status_cb(mid, status):
        meeting = session.query(Meeting).filter(Meeting.id == mid).first()
        if meeting:
            meeting.status = status
            session.commit()

    try:
        # Step 1: Join and record
        audio_path = await join_and_record_meeting(
            meeting_id, meet_link, title, status_cb
        )

        if not audio_path:
            session.close()
            return

        meeting = session.query(Meeting).filter(Meeting.id == meeting_id).first()
        if meeting:
            meeting.audio_path = audio_path
            meeting.status = "transcribing"
            session.commit()

        # Step 2: Transcribe
        transcript = transcribe_audio(audio_path)
        transcript_path = audio_path.replace(".wav", ".txt")
        with open(transcript_path, "w", encoding="utf-8") as f:
            f.write(transcript)

        if meeting:
            meeting.transcript_path = transcript_path
            meeting.status = "summarizing"
            session.commit()

        # Step 3: Summarize with LLM
        result = await summarize_transcript(title, transcript)

        # Step 4: Save minutes
        minute = MeetingMinute(
            meeting_id=meeting_id,
            summary=result["summary"],
            action_items=result["action_items"],
            pending_questions=result["pending_questions"],
            raw_transcript=transcript,
        )
        session.add(minute)

        if meeting:
            meeting.status = "completed"
        session.commit()

    except Exception as e:
        meeting = session.query(Meeting).filter(Meeting.id == meeting_id).first()
        if meeting:
            meeting.status = "failed"
            session.commit()
    finally:
        session.close()


@router.post("")
async def create_meeting(
    request: Request,
    background_tasks: BackgroundTasks,
    title: str = Form(...),
    meet_link: str = Form(...),
    db: Session = Depends(get_db),
):
    user = get_current_user(request, db)

    meeting = Meeting(
        user_id=user.id,
        title=title,
        meet_link=meet_link,
        status="pending",
    )
    db.add(meeting)
    db.commit()
    db.refresh(meeting)

    # Trigger background processing
    background_tasks.add_task(
        process_meeting,
        meeting.id,
        meet_link,
        title,
    )

    return RedirectResponse(url=f"/meetings/{meeting.id}", status_code=302)


@router.get("/{meeting_id}")
async def view_meeting(
    request: Request,
    meeting_id: int,
    db: Session = Depends(get_db),
):
    user = get_current_user(request, db)
    meeting = (
        db.query(Meeting)
        .filter(Meeting.id == meeting_id, Meeting.user_id == user.id)
        .first()
    )
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    return templates.TemplateResponse(
        "meeting_detail.html",
        {"request": request, "user": user, "meeting": meeting},
    )
