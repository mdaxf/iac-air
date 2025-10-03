from typing import List
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import Field
from sqlalchemy.ext.asyncio import AsyncSession
import json
import asyncio

from app.core.database import get_db
from app.core.auth import get_current_active_user, require_database_access
from app.models.user import User
from app.schemas.chat import (
    ChatMessageCreate,
    ChatResponse,
    ConversationCreate,
    Conversation,
    ConversationMessage,
    DrillDownRequest,
    ExportRequest,
    ExecutePendingQueryRequest,
    RegenerateQueryRequest
)
from app.services.chat_service import ChatService
from app.core.logging_config import log_method_calls, Logger, log_performance
from app.api.v1.endpoints import text2sql
from datetime import datetime 
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks

router = APIRouter()


@router.post("/conversations", response_model=Conversation)
async def create_conversation(
    conversation_data: ConversationCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new conversation"""
    # Set user_id to current user
    conversation_data.user_id = str(current_user.id)
    chat_service = ChatService()
    return await chat_service.create_conversation(db, conversation_data)


@router.get("/conversations", response_model=List[Conversation])
async def list_conversations(
    limit: int = 100,
    offset: int = 0,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """List conversations for current user with pagination"""
    chat_service = ChatService()
    return await chat_service.get_user_conversations(db, str(current_user.id), limit=limit, offset=offset)


@router.get("/conversations/{conversation_id}", response_model=Conversation)
async def get_conversation(
    conversation_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get a conversation by ID"""
    chat_service = ChatService()
    conversation = await chat_service.get_conversation(db, conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a conversation and all its messages"""
    chat_service = ChatService()
    success = await chat_service.delete_conversation(db, conversation_id, str(current_user.id))
    if not success:
        raise HTTPException(status_code=404, detail="Conversation not found or access denied")
    return {"message": "Conversation deleted successfully"}


@router.get("/conversations/{conversation_id}/messages", response_model=List[ChatResponse])
async def get_conversation_messages(
    conversation_id: str,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
):
    """Get messages for a specific conversation"""
    chat_service = ChatService()
    messages = await chat_service.get_conversation_messages(db, conversation_id, limit=limit, offset=offset)
    return messages


@router.get("/conversations/{conversation_id}/messages/complete", response_model=List[ConversationMessage])
async def get_conversation_messages_complete(
    conversation_id: str,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
):
    """Get complete conversation messages with both user questions and AI responses"""
    chat_service = ChatService()
    messages = await chat_service.get_conversation_messages_complete(db, conversation_id, limit=limit, offset=offset)
    return messages


@router.get("/conversations/{conversation_id}/title")
async def get_conversation_title(
    conversation_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get conversation title based on first question (20-50 words)"""
    chat_service = ChatService()
    title = await chat_service.get_conversation_first_question(db, conversation_id)
    return {"title": title}


@router.get("/conversations/{conversation_id}/messages/stream")
async def stream_conversation_messages(
    conversation_id: str,
    limit: int = 50,
    offset: int = 0,
    token: str = None,
    db: AsyncSession = Depends(get_db)
):
    """Stream messages for a specific conversation using Server-Sent Events"""

    # Verify token authentication for SSE
    if not token:
        raise HTTPException(status_code=401, detail="Authentication token required")

    # Validate token using auth service
    from app.services.auth_service import AuthService

    try:
        auth_service = AuthService()
        current_user = await auth_service.get_user_by_token(db, token)
        if not current_user:
            raise HTTPException(status_code=401, detail="Invalid authentication token")

    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid authentication token")

    async def generate_messages():
        try:
            chat_service = ChatService()
            messages = await chat_service.get_conversation_messages(db, conversation_id, limit=limit, offset=offset)

            # Send messages one by one with a small delay for better UX
            for i, message in enumerate(messages):
                # Convert message to dict for JSON serialization
                message_dict = {
                    "answer_id": message.answer_id,
                    "conversation_id": message.conversation_id,
                    "narrative": message.narrative,
                    "sql": message.sql,
                    "table_preview": message.table_preview,
                    "chart_meta": message.chart_meta,
                    "provenance": message.provenance,
                    "created_at": message.created_at.isoformat() if message.created_at else None
                }

                try:
                    # Send the message
                    yield f"data: {json.dumps({'type': 'message', 'data': message_dict})}\n\n"

                    # Small delay to avoid overwhelming the frontend
                    if i < len(messages) - 1:  # Don't delay after the last message
                        await asyncio.sleep(0.1)
                except (GeneratorExit, asyncio.CancelledError):
                    # Client disconnected, cleanup gracefully
                    from app.core.logging_config import Logger
                    Logger.info(f"SSE client disconnected for conversation {conversation_id}")
                    return

            # Send completion signal
            yield f"data: {json.dumps({'type': 'complete', 'total': len(messages)})}\n\n"

        except (GeneratorExit, asyncio.CancelledError):
            # Client disconnected, cleanup gracefully
            from app.core.logging_config import Logger
            Logger.info(f"SSE connection cancelled for conversation {conversation_id}")
            return
        except Exception as e:
            # Send error message
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"

    return StreamingResponse(
        generate_messages(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Cache-Control"
        }
    )



@router.post("/message", response_model=ChatResponse)
async def send_chat_message(
    message_data: ChatMessageCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Send a chat message and get AI response"""
    # Check if user has access to the database

#    request = text2sql.ChatQueryRequest(
#        question = message_data.text,
#        database_alias = message_data.db_alias,
#        execute_query = True,
#        sample_size = 1000
#    )
#    background_tasks =  BackgroundTasks() 
#    try:
#        response = await text2sql.ask_question(
#            request = request,
#            background_tasks = background_tasks,
#            db = db
#        )

#        return  ChatResponse(
#            answer_id=response.thread_id,
#            conversation_id= response.thread_id,
#            narrative= response.columns_used,
#            sql = response.sql,
#            table_preview = response.data,
#            chart_meta = response.explanation,
#            provenance = response.confidence,
#            created_at= Field(default_factory=datetime.utcnow)           
#        )
    
#    except Exception as e:
#        raise HTTPException(status_code=500, detail=f"Failed to process message: {str(e)}")



    if message_data.db_alias:
        # Check database access
        try:
            user_db_aliases = [db.alias for db in current_user.accessible_databases] if current_user.accessible_databases else []
        except Exception:
            # If relationship is not loaded, assume no access (will be caught by admin check)
            user_db_aliases = []
        if not current_user.is_admin and message_data.db_alias not in user_db_aliases:
            raise HTTPException(
                status_code=403,
                detail=f"Access denied to database '{message_data.db_alias}'"
            )

    chat_service = ChatService()
    try:
        return await chat_service.process_message(db, message_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process message: {str(e)}")


@router.post("/drill-down", response_model=ChatResponse)
async def drill_down(
    drill_request: DrillDownRequest,
    db: AsyncSession = Depends(get_db)
):
    """Perform drill-down analysis on previous results"""
    chat_service = ChatService()
    try:
        return await chat_service.drill_down_analysis(db, drill_request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to perform drill-down: {str(e)}")


@router.post("/export")
async def export_results(
    export_request: ExportRequest,
    db: AsyncSession = Depends(get_db)
):
    """Export chat results to various formats"""
    chat_service = ChatService()
    try:
        export_data = await chat_service.export_results(db, export_request)
        return export_data
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to export results: {str(e)}")


@router.post("/execute-pending-query", response_model=ChatResponse)
async def execute_pending_query(
    request: ExecutePendingQueryRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Execute a pending query (when auto_execute_query is false)"""
    chat_service = ChatService()
    try:
        return await chat_service.execute_pending_query(db, request.message_id, request.modified_sql)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to execute pending query: {str(e)}")


@router.post("/regenerate-query", response_model=ChatResponse)
async def regenerate_query(
    request: RegenerateQueryRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Regenerate a query with additional context"""
    chat_service = ChatService()
    try:
        return await chat_service.regenerate_query(db, request.message_id, request.additional_context)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to regenerate query: {str(e)}")