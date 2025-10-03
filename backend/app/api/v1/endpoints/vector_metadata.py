"""
Vector Metadata API Endpoints

Provides REST API for schema synchronization and vector metadata management.
"""
from typing import List, Optional
from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.services.schema_sync_service import SchemaSyncService, VectorJobService
from app.core.logging_config import log_method_calls, debug_logger
import logging

router = APIRouter()
logger = logging.getLogger("vector_metadata_api")


# ============================================================================
# Schema Sync Endpoints
# ============================================================================

@router.post("/sync-schema")
@log_method_calls
async def sync_database_schema(
    db_alias: str = Query(..., description="Database alias to sync"),
    schema_names: Optional[List[str]] = Query(None, description="Specific schemas to sync"),
    force_refresh: bool = Query(False, description="Force refresh existing metadata"),
    background_tasks: BackgroundTasks = None,
    db: AsyncSession = Depends(get_db)
):
    """Synchronize database schema to vector metadata tables"""
    try:
        # Start sync job
        result = await SchemaSyncService.sync_database_schema(
            db=db,
            db_alias=db_alias,
            schema_names=schema_names,
            force_refresh=force_refresh
        )

        return {
            "status": "success",
            "message": "Schema sync completed",
            "result": result
        }
    except Exception as e:
        logger.error(f"Schema sync failed for {db_alias}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Schema sync failed: {str(e)}"
        )


@router.get("/sync-jobs/{job_id}")
@log_method_calls
async def get_sync_job(
    job_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get status of a schema sync job"""
    try:
        job = await VectorJobService.get_job(db, job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        return {
            "id": str(job.id),
            "db_alias": job.db_alias,
            "job_type": job.job_type,
            "status": job.status,
            "progress": job.progress,
            "current_step": job.current_step,
            "results": job.results,
            "error_message": job.error_message,
            "created_at": job.created_at.isoformat(),
            "started_at": job.started_at.isoformat() if job.started_at else None,
            "completed_at": job.completed_at.isoformat() if job.completed_at else None
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get job {job_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get job: {str(e)}"
        )


@router.get("/sync-jobs")
@log_method_calls
async def list_sync_jobs(
    db_alias: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """List schema sync jobs"""
    try:
        jobs = await VectorJobService.list_jobs(
            db=db,
            db_alias=db_alias,
            status=status,
            limit=limit
        )

        return [
            {
                "id": str(job.id),
                "db_alias": job.db_alias,
                "job_type": job.job_type,
                "status": job.status,
                "progress": job.progress,
                "created_at": job.created_at.isoformat(),
                "completed_at": job.completed_at.isoformat() if job.completed_at else None
            }
            for job in jobs
        ]
    except Exception as e:
        logger.error(f"Failed to list jobs: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list jobs: {str(e)}"
        )


@router.post("/sync-jobs/{job_id}/cancel")
@log_method_calls
async def cancel_sync_job(
    job_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Cancel a running job"""
    try:
        from app.models.vector_job import VectorRegenerationJob

        query = select(VectorRegenerationJob).where(VectorRegenerationJob.id == job_id)
        result = await db.execute(query)
        job = result.scalars().first()

        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        if job.status in ('completed', 'failed', 'cancelled'):
            raise HTTPException(
                status_code=400,
                detail=f"Cannot cancel job with status: {job.status}"
            )

        job.status = 'cancelled'
        job.error_message = 'Cancelled by user'
        job.completed_at = datetime.utcnow()
        await db.commit()

        return {
            "status": "success",
            "message": f"Job {job_id} cancelled",
            "job_id": str(job.id)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cancel job {job_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to cancel job: {str(e)}"
        )


@router.get("/sync-jobs/active/{db_alias}")
@log_method_calls
async def get_active_job_for_database(
    db_alias: str,
    db: AsyncSession = Depends(get_db)
):
    """Get active regeneration job for a specific database (for initial load)"""
    try:
        from app.models.vector_job import VectorRegenerationJob

        query = select(VectorRegenerationJob).where(
            VectorRegenerationJob.db_alias == db_alias,
            VectorRegenerationJob.job_type == 'regenerate_embeddings',
            VectorRegenerationJob.status.in_(['pending', 'in_progress'])
        ).order_by(VectorRegenerationJob.created_at.desc())

        result = await db.execute(query)
        job = result.scalars().first()

        if not job:
            return {"active_job": None}

        return {
            "active_job": {
                "id": str(job.id),
                "db_alias": job.db_alias,
                "job_type": job.job_type,
                "status": job.status,
                "progress": job.progress,
                "current_step": job.current_step,
                "results": job.results,
                "error_message": job.error_message,
                "created_at": job.created_at.isoformat(),
                "started_at": job.started_at.isoformat() if job.started_at else None
            }
        }
    except Exception as e:
        logger.error(f"Failed to get active job for {db_alias}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get active job: {str(e)}"
        )


@router.get("/sync-jobs/stream/{db_alias}")
@log_method_calls
async def stream_job_updates(
    db_alias: str,
    db: AsyncSession = Depends(get_db)
):
    """Stream real-time job updates using Server-Sent Events (event-driven, no polling)"""
    from fastapi.responses import StreamingResponse
    from app.models.vector_job import VectorRegenerationJob
    from app.services.job_event_bus import job_event_bus
    import json
    import asyncio

    async def event_generator():
        """Generate SSE events from job event bus"""
        queue = None

        try:
            # Check if there's an active job first
            query = select(VectorRegenerationJob).where(
                VectorRegenerationJob.db_alias == db_alias,
                VectorRegenerationJob.job_type == 'regenerate_embeddings',
                VectorRegenerationJob.status.in_(['pending', 'in_progress'])
            ).order_by(VectorRegenerationJob.created_at.desc())

            result = await db.execute(query)
            job = result.scalars().first()

            if job:
                # Send initial job state
                job_data = {
                    "id": str(job.id),
                    "db_alias": job.db_alias,
                    "job_type": job.job_type,
                    "status": job.status,
                    "progress": job.progress,
                    "current_step": job.current_step,
                    "results": job.results,
                    "error_message": job.error_message,
                    "created_at": job.created_at.isoformat(),
                    "started_at": job.started_at.isoformat() if job.started_at else None
                }
                yield f"data: {json.dumps({'active_job': job_data})}\n\n"

                # Subscribe to event bus for real-time updates
                queue = await job_event_bus.subscribe(db_alias)

                # Listen for events (event-driven, no polling!)
                timeout_seconds = 30 * 60  # 30 minute timeout
                start_time = asyncio.get_event_loop().time()

                while True:
                    try:
                        # Wait for next event with timeout
                        event = await asyncio.wait_for(queue.get(), timeout=30.0)

                        # Check overall timeout
                        if asyncio.get_event_loop().time() - start_time > timeout_seconds:
                            logger.info(f"SSE stream timeout for {db_alias}")
                            break

                        # Send event to client
                        job_data = {
                            "id": event.job_id,
                            "db_alias": event.db_alias,
                            "job_type": "regenerate_embeddings",
                            "status": event.status,
                            "progress": event.progress,
                            "current_step": event.current_step,
                            "results": event.results,
                            "error_message": event.error_message,
                            "created_at": event.timestamp.isoformat(),
                            "started_at": event.timestamp.isoformat()
                        }
                        yield f"data: {json.dumps({'active_job': job_data})}\n\n"

                        # Close connection if job finished
                        if event.status in ('completed', 'failed', 'cancelled'):
                            logger.info(f"Job {event.status} for {db_alias}, closing SSE")
                            await asyncio.sleep(0.5)  # Small delay to ensure client receives
                            break

                    except asyncio.TimeoutError:
                        # No event for 30 seconds, send heartbeat to keep connection alive
                        try:
                            yield f": heartbeat\n\n"
                        except (GeneratorExit, asyncio.CancelledError):
                            logger.info(f"SSE client disconnected during heartbeat for {db_alias}")
                            break
                        continue
                    except (GeneratorExit, asyncio.CancelledError):
                        logger.info(f"SSE client disconnected for {db_alias}")
                        break

            else:
                # No active job - keep connection open and wait for job to start
                yield f"data: {json.dumps({'active_job': None})}\n\n"
                logger.debug(f"No active job for {db_alias}, waiting for job to start...")

                # Subscribe to event bus to be notified when job starts
                queue = await job_event_bus.subscribe(db_alias)

                # Wait for job to start (with timeout)
                timeout_seconds = 5 * 60  # 5 minute timeout when no job
                start_time = asyncio.get_event_loop().time()

                while True:
                    try:
                        # Wait for next event with timeout
                        event = await asyncio.wait_for(queue.get(), timeout=30.0)

                        # Check overall timeout
                        if asyncio.get_event_loop().time() - start_time > timeout_seconds:
                            logger.info(f"SSE stream timeout (no job) for {db_alias}")
                            break

                        # Send event to client
                        job_data = {
                            "id": event.job_id,
                            "db_alias": event.db_alias,
                            "job_type": "regenerate_embeddings",
                            "status": event.status,
                            "progress": event.progress,
                            "current_step": event.current_step,
                            "results": event.results,
                            "error_message": event.error_message,
                            "created_at": event.timestamp.isoformat(),
                            "started_at": event.timestamp.isoformat()
                        }
                        yield f"data: {json.dumps({'active_job': job_data})}\n\n"

                        # If job finished, close connection
                        if event.status in ('completed', 'failed', 'cancelled'):
                            logger.info(f"Job {event.status} for {db_alias}, closing SSE")
                            await asyncio.sleep(0.5)
                            break

                    except asyncio.TimeoutError:
                        # No event for 30 seconds, send heartbeat to keep connection alive
                        try:
                            yield f": heartbeat\n\n"
                        except (GeneratorExit, asyncio.CancelledError):
                            logger.info(f"SSE client disconnected during heartbeat for {db_alias}")
                            break
                        continue
                    except (GeneratorExit, asyncio.CancelledError):
                        logger.info(f"SSE client disconnected for {db_alias}")
                        break

        except Exception as e:
            logger.error(f"Error in SSE event generator for {db_alias}: {str(e)}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

        finally:
            if queue:
                await job_event_bus.unsubscribe(db_alias, queue)
            logger.debug(f"SSE stream closed for {db_alias}")

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable buffering in nginx
        }
    )


# ============================================================================
# Table Metadata Endpoints
# ============================================================================

@router.get("/tables")
@log_method_calls
async def list_table_metadata(
    db_alias: Optional[str] = Query(None),
    schema_name: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db)
):
    """List table metadata"""
    try:
        from app.models.vector_metadata import VectorTableMetadata

        query = select(VectorTableMetadata)

        if db_alias:
            query = query.filter(VectorTableMetadata.db_alias == db_alias)
        if schema_name:
            query = query.filter(VectorTableMetadata.schema_name == schema_name)

        query = query.limit(limit)
        result = await db.execute(query)
        tables = result.scalars().all()

        return [
            {
                "id": str(table.id),
                "db_alias": table.db_alias,
                "schema_name": table.schema_name,
                "table_name": table.table_name,
                "table_type": table.table_type,
                "description": table.description,
                "row_count": table.business_metadata.get("row_count_estimate") if table.business_metadata else None,
                "size_bytes": int(table.business_metadata.get("size_mb", 0) * 1024 * 1024) if table.business_metadata and table.business_metadata.get("size_mb") else None,
                "business_metadata": table.business_metadata,
                "technical_metadata": table.technical_metadata,
                "quality_score": table.quality_score,
                "usage_count": table.usage_count,
                "last_sync_at": table.last_schema_sync.isoformat() if table.last_schema_sync else None,
                "created_at": table.created_at.isoformat(),
                "updated_at": table.updated_at.isoformat()
            }
            for table in tables
        ]
    except Exception as e:
        logger.error(f"Failed to list table metadata: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list table metadata: {str(e)}"
        )


@router.get("/columns")
@log_method_calls
async def list_column_metadata(
    db_alias: Optional[str] = Query(None),
    table_metadata_id: Optional[UUID] = Query(None),
    limit: int = Query(1000, ge=1, le=5000),
    db: AsyncSession = Depends(get_db)
):
    """List column metadata"""
    try:
        from app.models.vector_metadata import VectorColumnMetadata, VectorTableMetadata

        query = select(VectorColumnMetadata)

        if db_alias:
            query = query.join(VectorTableMetadata).filter(
                VectorTableMetadata.db_alias == db_alias
            )
        if table_metadata_id:
            query = query.filter(VectorColumnMetadata.table_metadata_id == table_metadata_id)

        query = query.limit(limit)
        result = await db.execute(query)
        columns = result.scalars().all()

        return [
            {
                "id": str(col.id),
                "table_metadata_id": str(col.table_metadata_id),
                "column_name": col.column_name,
                "data_type": col.data_type,
                "is_nullable": col.is_nullable,
                "is_primary_key": col.business_metadata.get("is_primary_key", False) if col.business_metadata else False,
                "is_foreign_key": col.business_metadata.get("is_foreign_key", False) if col.business_metadata else False,
                "default_value": col.business_metadata.get("default_value") if col.business_metadata else None,
                "description": col.column_description,
                "sample_values": col.business_metadata.get("examples", []) if col.business_metadata else [],
                "statistics": col.statistics,
                "created_at": col.created_at.isoformat(),
                "updated_at": col.updated_at.isoformat()
            }
            for col in columns
        ]
    except Exception as e:
        logger.error(f"Failed to list column metadata: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list column metadata: {str(e)}"
        )


@router.post("/regenerate-embeddings")
@log_method_calls
async def regenerate_embeddings(
    background_tasks: BackgroundTasks,
    db_alias: str = Query(..., description="Database alias"),
    metadata_type: str = Query("all", description="Type: all, tables, columns, entities, metrics, templates"),
    db: AsyncSession = Depends(get_db)
):
    """Regenerate vector embeddings for metadata"""
    # Debug logging
    print(f"[REGENERATE] regenerate_embeddings called: db_alias={db_alias}, metadata_type={metadata_type}")
    print(f"[REGENERATE] background_tasks type: {type(background_tasks)}, is None: {background_tasks is None}")
    debug_logger.debug(f"regenerate_embeddings called: db_alias={db_alias}, metadata_type={metadata_type}")
    debug_logger.debug(f"background_tasks type: {type(background_tasks)}, is None: {background_tasks is None}")

    try:
        from app.services.schema_sync_service import VectorJobService
        from app.models.vector_job import VectorRegenerationJob

        # Check for existing active job for this database
        query = select(VectorRegenerationJob).where(
            VectorRegenerationJob.db_alias == db_alias,
            VectorRegenerationJob.job_type == 'regenerate_embeddings',
            VectorRegenerationJob.status.in_(['pending', 'in_progress'])
        )
        result = await db.execute(query)
        existing_job = result.scalars().first()
        debug_logger.debug(f"the existing job: {existing_job}")
        if existing_job:
            return {
                "status": "already_running",
                "message": f"Embedding regeneration already in progress for {db_alias}",
                "job_id": str(existing_job.id),
                "db_alias": db_alias,
                "metadata_type": metadata_type
            }

        # Create a job to track the regeneration
        debug_logger.debug(f"create a new VectorJobService job")
        job = await VectorJobService.create_job(
            db=db,
            job_type='regenerate_embeddings',
            db_alias=db_alias,
            target_type=metadata_type,
            parameters={'metadata_type': metadata_type}
        )

        # Start background task
        print(f"[REGENERATE] Adding background task for job {job.id}, db_alias={db_alias}, metadata_type={metadata_type}")
        debug_logger.debug(f"Adding background task for job {job.id}, db_alias={db_alias}, metadata_type={metadata_type}")

        try:
            background_tasks.add_task(
                _regenerate_embeddings_task,
                str(job.id),
                db_alias,
                metadata_type
            )
            print(f"[REGENERATE] Background task added successfully via BackgroundTasks for job {job.id}")
            debug_logger.debug(f"Background task added successfully via BackgroundTasks for job {job.id}")
        except Exception as e:
            debug_logger.debug(f"Failed to add background task via BackgroundTasks: {e}")
            # Fallback: use asyncio.create_task
            import asyncio
            asyncio.create_task(_regenerate_embeddings_task(str(job.id), db_alias, metadata_type))
            debug_logger.debug(f"Background task started via asyncio.create_task for job {job.id}")

        return {
            "status": "success",
            "message": f"Embedding regeneration started for {metadata_type}",
            "job_id": str(job.id),
            "db_alias": db_alias,
            "metadata_type": metadata_type
        }
    except Exception as e:
        debug_logger.debug(f"Failed to regenerate embeddings: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to regenerate embeddings: {str(e)}"
        )


async def _regenerate_embeddings_task(job_id: str, db_alias: str, metadata_type: str):
    """Background task to regenerate embeddings (event-driven, pushes updates to SSE)"""
    try:
        print(f"[REGENERATE] Background task STARTED for job {job_id}, db_alias={db_alias}, metadata_type={metadata_type}")
        debug_logger.debug(f"Background task started for job {job_id}, db_alias={db_alias}, metadata_type={metadata_type}")

        from app.core.database import AsyncSessionLocal
        from app.services.schema_sync_service import VectorJobService
        from app.services.embedding_service import EmbeddingService
        from app.services.job_event_bus import job_event_bus, JobEvent
        from app.models.vector_metadata import VectorTableMetadata, VectorColumnMetadata
        from app.models.business_semantic import BusinessEntity, BusinessMetric, QueryTemplate
        from sqlalchemy import select, func
        from uuid import UUID
        import asyncio

        JOB_TIMEOUT_SECONDS = 1800  # 30 minutes timeout
        BATCH_SIZE = 20  # Process 20 items at a time to respect OpenAI rate limits
        DELAY_BETWEEN_BATCHES = 1.0  # 1 second delay between batches
        DELAY_PER_ITEM_FALLBACK = 0.6  # If batch fails, delay between individual items (100 req/min = 0.6s)

        debug_logger.debug(f"[TASK] About to enter async context manager")
        async with AsyncSessionLocal() as db:
            debug_logger.debug(f"[TASK] Successfully entered async context manager")
            try:
                debug_logger.debug(f"[TASK] Inside async context for job {job_id}")
                # Update job status
                job = await VectorJobService.get_job(db, UUID(job_id))
                debug_logger.debug(f"[TASK] Retrieved job: {job}, status={job.status if job else 'N/A'}")
                if not job:
                    debug_logger.debug(f"Job {job_id} not found")
                    return

                # Check if job was cancelled
                if job.status == 'cancelled':
                    debug_logger.debug(f"Job {job_id} was cancelled before starting")
                    return

                debug_logger.debug(f"[TASK] Updating job {job_id} to in_progress")
                job.status = 'in_progress'
                job.started_at = datetime.utcnow()
                job.current_step = 'Starting embedding regeneration...'
                job.progress = 0.0
                await db.commit()
                debug_logger.debug(f"[TASK] Job {job_id} status updated and committed")

                # Set up timeout
                start_time = datetime.utcnow()

                async def check_timeout():
                    """Check if job should be timed out"""
                    elapsed = (datetime.utcnow() - start_time).total_seconds()
                    if elapsed > JOB_TIMEOUT_SECONDS:
                        raise TimeoutError(f"Job exceeded timeout of {JOB_TIMEOUT_SECONDS} seconds")

                    # Check if job was cancelled
                    await db.refresh(job)
                    if job.status == 'cancelled':
                        raise InterruptedError("Job was cancelled")

                # Helper function to emit progress events
                async def emit_progress_event():
                    """Emit job progress event to event bus (only if there are subscribers)"""
                    if job_event_bus.has_subscribers(db_alias):
                        event = JobEvent(
                            job_id=str(job.id),
                            db_alias=db_alias,
                            status=job.status,
                            progress=job.progress or 0.0,
                            current_step=job.current_step or "",
                            timestamp=datetime.utcnow(),
                            results=job.results,
                            error_message=job.error_message
                        )
                        await job_event_bus.publish(event)

                # Emit initial event that job has started
                await emit_progress_event()

                embedding_service = EmbeddingService()
                count = 0
                total_items = 0
                processed_items = 0

                # Count total items to process
                if metadata_type in ('all', 'tables'):
                    result = await db.execute(select(func.count()).select_from(VectorTableMetadata).where(VectorTableMetadata.db_alias == db_alias))
                    total_items += result.scalar() or 0
                if metadata_type in ('all', 'columns'):
                    result = await db.execute(select(func.count()).select_from(VectorColumnMetadata).join(VectorTableMetadata).where(VectorTableMetadata.db_alias == db_alias))
                    total_items += result.scalar() or 0
                if metadata_type in ('all', 'entities'):
                    result = await db.execute(select(func.count()).select_from(BusinessEntity).where(BusinessEntity.db_alias == db_alias))
                    total_items += result.scalar() or 0
                if metadata_type in ('all', 'metrics'):
                    result = await db.execute(select(func.count()).select_from(BusinessMetric).where(BusinessMetric.db_alias == db_alias))
                    total_items += result.scalar() or 0
                if metadata_type in ('all', 'templates'):
                    result = await db.execute(select(func.count()).select_from(QueryTemplate).where(QueryTemplate.db_alias == db_alias))
                    total_items += result.scalar() or 0

                debug_logger.debug(f"Starting embedding generation for {total_items} items")

                # Regenerate table embeddings
                if metadata_type in ('all', 'tables'):
                    await check_timeout()

                    query = select(VectorTableMetadata).where(VectorTableMetadata.db_alias == db_alias)
                    result = await db.execute(query)
                    tables = result.scalars().all()

                    table_count = len(tables)
                    debug_logger.debug(f"Processing {table_count} tables")

                    # Process in batches to avoid rate limits
                    for batch_start in range(0, table_count, BATCH_SIZE):
                        await check_timeout()
                        batch_end = min(batch_start + BATCH_SIZE, table_count)
                        batch = tables[batch_start:batch_end]

                        # Prepare texts for batch embedding
                        texts = []
                        for table in batch:
                            text_parts = [
                                f"Table: {table.schema_name}.{table.table_name}",
                                f"Type: {table.table_type or 'table'}"
                            ]
                            if table.description:
                                text_parts.append(f"Description: {table.description}")
                            texts.append("\n".join(text_parts))

                        try:
                            # Get embeddings in batch
                            embeddings = await embedding_service.get_embeddings_batch(texts)

                            # Assign embeddings to tables
                            for idx, (table, embedding) in enumerate(zip(batch, embeddings)):
                                table.embedding = embedding
                                processed_items += 1
                                count += 1

                                # Update progress for last item in batch
                                if idx == len(batch) - 1:
                                    progress_pct = int((processed_items / total_items) * 100) if total_items > 0 else 0
                                    job.current_step = f'Generating table embeddings ({batch_end}/{table_count}): {table.schema_name}.{table.table_name}'
                                    job.progress = progress_pct / 100.0

                            await db.commit()

                            # Emit progress event to SSE subscribers
                            await emit_progress_event()

                            debug_logger.debug(f"Processed batch {batch_start}-{batch_end} ({len(embeddings)} tables)")

                            # Delay between batches to respect rate limits
                            if batch_end < table_count:
                                await asyncio.sleep(DELAY_BETWEEN_BATCHES)

                        except Exception as e:
                            debug_logger.debug(f"Failed to generate embeddings for batch {batch_start}-{batch_end}: {str(e)}")
                            # Try individual items if batch fails
                            for idx, table in enumerate(batch):
                                try:
                                    text_parts = [
                                        f"Table: {table.schema_name}.{table.table_name}",
                                        f"Type: {table.table_type or 'table'}"
                                    ]
                                    if table.description:
                                        text_parts.append(f"Description: {table.description}")

                                    text = "\n".join(text_parts)
                                    embedding = await embedding_service.get_embedding(text)
                                    table.embedding = embedding
                                    count += 1
                                    processed_items += 1
                                    await asyncio.sleep(DELAY_PER_ITEM_FALLBACK)
                                except Exception as e2:
                                    debug_logger.debug(f"Failed to generate embedding for table {table.table_name}: {str(e2)}")

                        await db.commit()

                        debug_logger.debug(f"Generated embeddings for {count}/{table_count} tables")

                # Regenerate column embeddings
                if metadata_type in ('all', 'columns'):
                    await check_timeout()

                    query = select(VectorColumnMetadata).join(VectorTableMetadata).where(
                        VectorTableMetadata.db_alias == db_alias
                    )
                    result = await db.execute(query)
                    columns = result.scalars().all()

                    column_count = len(columns)
                    debug_logger.debug(f"Processing {column_count} columns")

                    for idx, column in enumerate(columns, 1):
                        await check_timeout()

                        # Update progress
                        processed_items += 1
                        progress_pct = int((processed_items / total_items) * 100) if total_items > 0 else 0
                        job.current_step = f'Generating column embeddings ({idx}/{column_count}): {column.column_name}'
                        job.progress = progress_pct / 100.0

                        # Commit progress every 10 items
                        if idx % 10 == 0:
                            await db.commit()
                            await emit_progress_event()

                        try:
                            text_parts = [
                                f"Column: {column.column_name}",
                                f"Data Type: {column.data_type}"
                            ]
                            if column.column_description:
                                text_parts.append(f"Description: {column.column_description}")

                            text = "\n".join(text_parts)
                            embedding = await embedding_service.get_embedding(text)
                            column.embedding = embedding
                            count += 1
                        except Exception as e:
                            debug_logger.debug(f"Failed to generate embedding for column {column.column_name}: {str(e)}")

                    await db.commit()
                    await emit_progress_event()
                    debug_logger.debug(f"Generated embeddings for {count}/{column_count} columns")

                # Regenerate entity embeddings
                if metadata_type in ('all', 'entities'):
                    await check_timeout()

                    query = select(BusinessEntity).where(BusinessEntity.db_alias == db_alias)
                    result = await db.execute(query)
                    entities = result.scalars().all()

                    entity_count = len(entities)
                    debug_logger.debug(f"Processing {entity_count} entities")

                    for idx, entity in enumerate(entities, 1):
                        await check_timeout()

                        # Update progress
                        processed_items += 1
                        progress_pct = int((processed_items / total_items) * 100) if total_items > 0 else 0
                        job.current_step = f'Generating entity embeddings ({idx}/{entity_count}): {entity.entity_name}'
                        job.progress = progress_pct / 100.0

                        # Commit progress every 10 items
                        if idx % 10 == 0:
                            await db.commit()
                            await emit_progress_event()

                        try:
                            text_parts = [
                                f"Entity: {entity.entity_name}",
                                f"Type: {entity.entity_type}"
                            ]
                            if entity.description:
                                text_parts.append(f"Description: {entity.description}")

                            text = "\n".join(text_parts)
                            embedding = await embedding_service.get_embedding(text)
                            entity.embedding = embedding
                            count += 1
                        except Exception as e:
                            debug_logger.debug(f"Failed to generate embedding for entity {entity.entity_name}: {str(e)}")

                    await db.commit()
                    await emit_progress_event()
                    debug_logger.debug(f"Generated embeddings for {count}/{entity_count} entities")

                # Regenerate metric embeddings
                if metadata_type in ('all', 'metrics'):
                    await check_timeout()

                    query = select(BusinessMetric).where(BusinessMetric.db_alias == db_alias)
                    result = await db.execute(query)
                    metrics = result.scalars().all()

                    metric_count = len(metrics)
                    debug_logger.debug(f"Processing {metric_count} metrics")

                    for idx, metric in enumerate(metrics, 1):
                        await check_timeout()

                        # Update progress
                        processed_items += 1
                        progress_pct = int((processed_items / total_items) * 100) if total_items > 0 else 0
                        job.current_step = f'Generating metric embeddings ({idx}/{metric_count}): {metric.metric_name}'
                        job.progress = progress_pct / 100.0

                        # Commit progress every 10 items
                        if idx % 10 == 0:
                            await db.commit()
                            await emit_progress_event()

                        try:
                            text_parts = [f"Metric: {metric.metric_name}"]
                            if metric.metric_definition and metric.metric_definition.get('description'):
                                text_parts.append(f"Description: {metric.metric_definition['description']}")

                            text = "\n".join(text_parts)
                            embedding = await embedding_service.get_embedding(text)
                            metric.embedding = embedding
                            count += 1
                        except Exception as e:
                            logger.error(f"Failed to generate embedding for metric {metric.metric_name}: {str(e)}")

                    await db.commit()
                    await emit_progress_event()
                    logger.info(f"Generated embeddings for {count}/{metric_count} metrics")

                # Regenerate template embeddings
                if metadata_type in ('all', 'templates'):
                    await check_timeout()

                    query = select(QueryTemplate).where(QueryTemplate.db_alias == db_alias)
                    result = await db.execute(query)
                    templates = result.scalars().all()

                    template_count = len(templates)
                    logger.info(f"Processing {template_count} templates")

                    for idx, template in enumerate(templates, 1):
                        await check_timeout()

                        # Update progress
                        processed_items += 1
                        progress_pct = int((processed_items / total_items) * 100) if total_items > 0 else 0
                        job.current_step = f'Generating template embeddings ({idx}/{template_count}): {template.template_name}'
                        job.progress = progress_pct / 100.0

                        # Commit progress every 10 items
                        if idx % 10 == 0:
                            await db.commit()
                            await emit_progress_event()

                        try:
                            text_parts = [f"Template: {template.template_name}"]
                            if template.description:
                                text_parts.append(f"Description: {template.description}")

                            text = "\n".join(text_parts)
                            embedding = await embedding_service.get_embedding(text)
                            template.embedding = embedding
                            count += 1
                        except Exception as e:
                            logger.error(f"Failed to generate embedding for template {template.template_name}: {str(e)}")

                    await db.commit()
                    await emit_progress_event()
                    logger.info(f"Generated embeddings for {count}/{template_count} templates")

                # Update job as completed
                job.status = 'completed'
                job.completed_at = datetime.utcnow()
                job.results = {'embeddings_generated': count}
                job.progress = 1.0
                await db.commit()

                # Emit final completion event
                await emit_progress_event()

                logger.info(f"Completed embedding regeneration job {job_id}: {count} embeddings generated")

            except (TimeoutError, InterruptedError) as e:
                logger.warning(f"Embedding regeneration job {job_id} was interrupted: {str(e)}")
                try:
                    await db.refresh(job)
                    if job.status != 'cancelled':  # Only update if not already cancelled
                        job.status = 'failed'
                        job.error_message = str(e)
                        job.completed_at = datetime.utcnow()
                    await db.commit()

                    # Emit failure event
                    await emit_progress_event()
                except:
                    pass
            except Exception as e:
                debug_logger.debug(f"[TASK] Exception in embedding regeneration for job {job_id}: {str(e)}")
                debug_logger.debug(f"[TASK] Exception type: {type(e)}")
                import traceback
                debug_logger.debug(f"[TASK] Traceback: {traceback.format_exc()}")
                logger.error(f"Embedding regeneration failed for job {job_id}: {str(e)}")
                # Update job as failed
                try:
                    job.status = 'failed'
                    job.error_message = str(e)
                    job.completed_at = datetime.utcnow()
                    await db.commit()

                    # Emit failure event
                    await emit_progress_event()
                except Exception as e2:
                    debug_logger.debug(f"[TASK] Failed to update job status: {str(e2)}")
    except Exception as outer_e:
        debug_logger.debug(f"[TASK] Outer exception in _regenerate_embeddings_task: {str(outer_e)}")
        import traceback
        debug_logger.debug(f"[TASK] Outer traceback: {traceback.format_exc()}")
