"""
Text2SQL API Endpoints - Natural language to SQL conversion
Inspired by WrenAI's chat-based interface for data querying
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field, ConfigDict
import logging

from app.core.database import get_db
from app.services.text2sql_service import (
    Text2SQLService,
    Text2SQLQuery,
    Text2SQLResponse
)

logger = logging.getLogger(__name__)
router = APIRouter()


class ChatQueryRequest(BaseModel):
    """Request model for chat-based SQL generation"""
    model_config = ConfigDict(extra='forbid', validate_assignment=True)

    question: str = Field(..., min_length=1, description="Natural language question")
    database_alias: str = Field(..., description="Database to query")
    thread_id: Optional[str] = Field(None, description="Conversation thread ID")
    execute_query: bool = Field(True, description="Whether to execute the generated query")
    sample_size: Optional[int] = Field(100, le=1000, description="Maximum number of rows to return")


class ChatQueryResponse(BaseModel):
    """Response model for chat-based SQL generation"""
    sql: str
    explanation: str
    confidence: float
    reasoning: str
    thread_id: str
    query_type: str
    tables_used: List[str]
    columns_used: List[str]
    data: Optional[Dict[str, Any]] = None
    execution_time: Optional[float] = None
    error: Optional[str] = None


class SuggestedQuestionsResponse(BaseModel):
    """Response model for suggested questions"""
    questions: List[str]
    database_alias: str


class QueryHistoryItem(BaseModel):
    """Model for query history item"""
    question: str
    sql: str
    timestamp: str
    confidence: float
    execution_time: Optional[float] = None


class QueryHistoryResponse(BaseModel):
    """Response model for query history"""
    history: List[QueryHistoryItem]
    thread_id: str
    total_count: int


@router.post(
    "/chat/ask",
    response_model=ChatQueryResponse,
    summary="Generate SQL from natural language question",
    description="Convert a natural language question into SQL and optionally execute it"
)
async def ask_question(
    request: ChatQueryRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
) -> ChatQueryResponse:
    """
    Generate SQL from natural language question using AI

    This endpoint:
    1. Analyzes the natural language question
    2. Generates appropriate SQL query
    3. Optionally executes the query and returns data
    4. Maintains conversation context for follow-up questions
    """
    try:
        # Initialize Text2SQL service
        text2sql_service = Text2SQLService()

        # Create query object
        text2sql_query = Text2SQLQuery(
            question=request.question,
            database_alias=request.database_alias,
            thread_id=request.thread_id,
            sample_size=request.sample_size
        )

        # Generate SQL
        sql_response = await text2sql_service.generate_sql(text2sql_query, db)

        # Prepare response
        response_data = ChatQueryResponse(
            sql=sql_response.sql,
            explanation=sql_response.explanation,
            confidence=sql_response.confidence,
            reasoning=sql_response.reasoning,
            thread_id=sql_response.thread_id,
            query_type=sql_response.query_type,
            tables_used=sql_response.tables_used,
            columns_used=sql_response.columns_used
        )

        # Execute query if requested
        if request.execute_query:
            try:
                import time
                start_time = time.time()

                query_result = await text2sql_service.execute_generated_sql(
                    sql=sql_response.sql,
                    database_alias=request.database_alias,
                    db_session=db,
                    limit=request.sample_size
                )

                execution_time = time.time() - start_time

                response_data.data = query_result
                response_data.execution_time = execution_time

            except Exception as e:
                logger.error(f"Error executing generated SQL: {str(e)}")
                response_data.error = f"Query generation succeeded but execution failed: {str(e)}"

        # Save to history in background
        background_tasks.add_task(
            _save_query_to_history,
            db,
            request,
            sql_response,
            response_data.execution_time
        )

        return response_data

    except Exception as e:
        logger.error(f"Error in ask_question endpoint: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=f"Failed to process question: {str(e)}"
        )


@router.get(
    "/chat/suggestions/{database_alias}",
    response_model=SuggestedQuestionsResponse,
    summary="Get suggested questions for a database",
    description="Get AI-generated suggested questions based on database schema"
)
async def get_suggested_questions(
    database_alias: str,
    limit: int = 5,
    db: AsyncSession = Depends(get_db)
) -> SuggestedQuestionsResponse:
    """
    Get suggested questions for exploring a database

    Uses AI to analyze the database schema and suggest
    useful questions that can be asked about the data.
    """
    try:
        text2sql_service = Text2SQLService()

        questions = await text2sql_service.get_suggested_questions(
            database_alias=database_alias,
            db_session=db,
            limit=min(limit, 10)  # Cap at 10 questions
        )

        return SuggestedQuestionsResponse(
            questions=questions,
            database_alias=database_alias
        )

    except Exception as e:
        logger.error(f"Error getting suggested questions: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=f"Failed to get suggested questions: {str(e)}"
        )


@router.post(
    "/chat/validate-sql",
    summary="Validate SQL query",
    description="Validate a SQL query without executing it"
)
async def validate_sql(
    sql: str,
    database_alias: str,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Validate SQL query syntax and safety

    Checks:
    - Basic SQL syntax
    - Query safety (no dangerous operations)
    - Table and column existence
    """
    try:
        text2sql_service = Text2SQLService()

        # Perform validation
        await text2sql_service._basic_sql_validation(sql, database_alias)

        return {
            "valid": True,
            "message": "SQL query is valid",
            "sql": sql
        }

    except Exception as e:
        return {
            "valid": False,
            "message": str(e),
            "sql": sql
        }


@router.get(
    "/chat/history/{thread_id}",
    response_model=QueryHistoryResponse,
    summary="Get conversation history",
    description="Retrieve conversation history for a thread"
)
async def get_query_history(
    thread_id: str,
    limit: int = 20,
    db: AsyncSession = Depends(get_db)
) -> QueryHistoryResponse:
    """
    Get query history for a conversation thread

    Returns the history of questions and generated SQL
    queries for the specified thread.
    """
    try:
        # This would typically query a history table
        # For now, return empty history as example

        return QueryHistoryResponse(
            history=[],
            thread_id=thread_id,
            total_count=0
        )

    except Exception as e:
        logger.error(f"Error getting query history: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=f"Failed to get query history: {str(e)}"
        )


@router.post(
    "/chat/explain-sql",
    summary="Explain SQL query",
    description="Get natural language explanation of a SQL query"
)
async def explain_sql(
    sql: str,
    database_alias: str,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Generate natural language explanation of a SQL query

    Analyzes the SQL query and provides a human-readable
    explanation of what the query does.
    """
    try:
        text2sql_service = Text2SQLService()

        if not text2sql_service.client:
            return {
                "explanation": "SQL explanation requires OpenAI API configuration",
                "sql": sql
            }

        # Get schema context
        schema_info = await text2sql_service._get_database_schema(database_alias, db)

        explain_prompt = f"""
Explain this SQL query in simple, non-technical language:

SQL Query:
{sql}

Database Schema Context:
{schema_info}

Provide a clear explanation of:
1. What data the query retrieves
2. Which tables are involved
3. Any filtering or sorting applied
4. What the results would represent

Keep the explanation concise and business-focused.
"""

        response = await text2sql_service.client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {
                    "role": "system",
                    "content": "You are a data analyst who explains SQL queries in simple, business-friendly language."
                },
                {"role": "user", "content": explain_prompt}
            ],
            temperature=0.3,
            max_tokens=500
        )

        explanation = response.choices[0].message.content

        return {
            "explanation": explanation,
            "sql": sql,
            "database_alias": database_alias
        }

    except Exception as e:
        logger.error(f"Error explaining SQL: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=f"Failed to explain SQL: {str(e)}"
        )


async def _save_query_to_history(
    db: AsyncSession,
    request: ChatQueryRequest,
    sql_response: Text2SQLResponse,
    execution_time: Optional[float]
) -> None:
    """Save query to history (background task)"""
    try:
        # This would save to a database table
        # Implementation depends on your history storage strategy
        logger.info(f"Saving query to history: {request.question[:50]}...")

        # Example: Create a QueryHistory model and save
        # history_item = QueryHistory(
        #     thread_id=sql_response.thread_id,
        #     question=request.question,
        #     sql=sql_response.sql,
        #     confidence=sql_response.confidence,
        #     execution_time=execution_time,
        #     database_alias=request.database_alias,
        #     created_at=datetime.utcnow()
        # )
        # db.add(history_item)
        # db.commit()

    except Exception as e:
        logger.error(f"Error saving query to history: {str(e)}")
        # Don't raise exception as this is a background task