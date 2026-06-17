import math
import os
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, BackgroundTasks
from typing import List
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db
from app.models.evaluation import Evaluation
from app.schemas.evaluation import (
    EvaluationDetailResponse,
    EvaluationListResponse,
    EvaluationListItem,
    EvaluationStatusResponse,
    UploadResponse,
    ScoreDimensionResult,
)
from app.services.evaluator import run_evaluation

router = APIRouter(prefix="/evaluations", tags=["evaluations"])
settings = get_settings()

ALLOWED_EXTENSIONS = {"pdf", "ppt", "pptx"}
MAX_CONCURRENT = 3
MAX_BATCH = 5


@router.post("/upload", response_model=UploadResponse)
async def upload_evaluation(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    db: AsyncSession = Depends(get_db),
):
    if len(files) > MAX_BATCH:
        raise HTTPException(status_code=400, detail=f"最多同时上传 {MAX_BATCH} 个文件")

    processing_count = await db.scalar(
        select(func.count()).where(Evaluation.status == "processing")
    )
    if processing_count >= MAX_CONCURRENT:
        raise HTTPException(status_code=429, detail="当前评估任务过多，请稍后重试")

    os.makedirs(settings.upload_dir, exist_ok=True)
    saved_paths = []
    all_text_parts = []
    first_filename = None

    for file in files:
        ext = Path(file.filename or "").suffix.lstrip(".").lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(status_code=400, detail=f"不支持的文件格式 ({file.filename})，请上传 PDF、PPT 或 PPTX")

        content = await file.read()
        max_bytes = settings.max_upload_size_mb * 1024 * 1024
        if len(content) > max_bytes:
            raise HTTPException(status_code=413, detail=f"{file.filename} 超过 {settings.max_upload_size_mb}MB 限制")

        saved_name = f"{uuid.uuid4().hex}.{ext}"
        file_path = os.path.join(settings.upload_dir, saved_name)
        with open(file_path, "wb") as f:
            f.write(content)
        saved_paths.append((file_path, ext, file.filename))

        if first_filename is None:
            first_filename = file.filename

    primary_ext = saved_paths[0][1]
    all_file_paths = "\n".join(p[0] for p in saved_paths)
    project_name = Path(first_filename or "未知项目").stem
    original_filenames = " + ".join(p[2] for p in saved_paths)

    ev = Evaluation(
        project_name=project_name,
        original_filename=original_filenames,
        file_path=all_file_paths,
        file_type=primary_ext,
        extracted_text="",
        text_length=0,
        status="pending",
    )
    db.add(ev)
    await db.commit()
    await db.refresh(ev)

    background_tasks.add_task(run_evaluation, ev.id, db)

    return UploadResponse(
        id=ev.id,
        project_name=ev.project_name,
        status=ev.status,
        message=f"{'、'.join(p[2] for p in saved_paths)} 上传成功，正在评估中...",
    )


@router.get("", response_model=EvaluationListResponse)
async def list_evaluations(
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db),
):
    page = max(1, page)
    page_size = min(max(1, page_size), 100)
    offset = (page - 1) * page_size

    total = await db.scalar(select(func.count()).select_from(Evaluation))
    stmt = select(Evaluation).order_by(Evaluation.created_at.desc()).offset(offset).limit(page_size)
    result = await db.execute(stmt)
    items = result.scalars().all()

    return EvaluationListResponse(
        items=[EvaluationListItem.model_validate(ev) for ev in items],
        total=total or 0,
        page=page,
        page_size=page_size,
        total_pages=math.ceil((total or 0) / page_size),
    )


@router.get("/{evaluation_id}/status", response_model=EvaluationStatusResponse)
async def get_status(evaluation_id: int, db: AsyncSession = Depends(get_db)):
    ev = await db.get(Evaluation, evaluation_id)
    if not ev:
        raise HTTPException(status_code=404, detail="评估记录不存在")
    return EvaluationStatusResponse(
        id=ev.id,
        status=ev.status,
        final_score=ev.final_score,
        decision=ev.decision,
        error_message=ev.error_message,
    )


@router.get("/{evaluation_id}", response_model=EvaluationDetailResponse)
async def get_evaluation(evaluation_id: int, db: AsyncSession = Depends(get_db)):
    ev = await db.get(Evaluation, evaluation_id)
    if not ev:
        raise HTTPException(status_code=404, detail="评估记录不存在")

    scores_data = ev.get_scores()
    scores_list = None
    if scores_data:
        scores_list = [
            ScoreDimensionResult(**dim)
            for dim in scores_data.get("dimensions", [])
        ]

    return EvaluationDetailResponse(
        id=ev.id,
        project_name=ev.project_name,
        original_filename=ev.original_filename,
        file_type=ev.file_type,
        text_length=ev.text_length,
        llm_provider=ev.llm_provider,
        llm_model=ev.llm_model,
        project_intro=ev.get_project_intro(),
        scores=scores_list,
        score_team=ev.score_team,
        score_pain_point=ev.score_pain_point,
        score_traction=ev.score_traction,
        score_moat=ev.score_moat,
        final_score=ev.final_score,
        decision=ev.decision,
        suggestions=ev.get_suggestions(),
        status=ev.status,
        error_message=ev.error_message,
        created_at=ev.created_at,
        updated_at=ev.updated_at,
    )


@router.get("/{evaluation_id}/share-image")
async def share_image(evaluation_id: int, db: AsyncSession = Depends(get_db)):
    """分享卡片缩略图（og:image）。仅对已完成的评估生成。
    注意：URL 不带 .png 后缀，避免 Nginx 把它当静态文件拦截。"""
    from fastapi import Response
    from app.services.share_image import generate_share_image

    ev = await db.get(Evaluation, evaluation_id)
    if not ev or ev.status != "completed" or ev.final_score is None:
        raise HTTPException(status_code=404, detail="评估结果不存在或未完成")

    png = generate_share_image(ev.id, ev.project_name, ev.final_score)
    return Response(content=png, media_type="image/png",
                    headers={"Cache-Control": "public, max-age=86400"})



@router.delete("/{evaluation_id}")
async def delete_evaluation(evaluation_id: int, db: AsyncSession = Depends(get_db)):
    ev = await db.get(Evaluation, evaluation_id)
    if not ev:
        raise HTTPException(status_code=404, detail="评估记录不存在")

    # Delete uploaded file
    if ev.file_path:
        for fp in ev.file_path.split("\n"):
            fp = fp.strip()
            if fp and os.path.exists(fp):
                try:
                    os.remove(fp)
                except OSError:
                    pass

    await db.delete(ev)
    await db.commit()
    return {"message": "已删除"}
