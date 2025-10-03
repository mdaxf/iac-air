from typing import Optional, Dict, Any, List, Union
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict, model_validator, field_serializer
from uuid import UUID


class ChatMessageBase(BaseModel):
    conversation_id: str = Field(..., description="Conversation identifier")
    text: str = Field(..., description="User message text")
    db_alias: Optional[str] = Field(None, description="Target database alias")


class ChatMessageCreate(ChatMessageBase):
    pass


class ChatResponse(BaseModel):
    model_config = ConfigDict(extra='forbid', validate_assignment=True)

    answer_id: str = Field(..., description="Unique answer identifier")
    conversation_id: str = Field(..., description="Conversation identifier")
    narrative: str = Field(..., description="Natural language response")
    sql: Optional[str] = Field(None, description="Generated SQL query")
    table_preview: Optional[List[Dict[str, Any]]] = Field(None, description="Result data preview")
    chart_meta: Optional[Dict[str, Any]] = Field(None, description="Chart configuration")
    provenance: Dict[str, Any] = Field(..., description="Data source information")
    created_at: datetime


class ConversationMessage(BaseModel):
    """Complete conversation message with both user question and AI response"""
    model_config = ConfigDict(extra='forbid', validate_assignment=True)

    message_id: str = Field(..., description="Unique message identifier")
    conversation_id: str = Field(..., description="Conversation identifier")
    user_question: str = Field(..., description="Original user question")
    ai_response: str = Field(..., description="AI generated response")
    sql: Optional[str] = Field(None, description="Generated SQL query")
    table_preview: Optional[List[Dict[str, Any]]] = Field(None, description="Result data preview")
    chart_meta: Optional[Dict[str, Any]] = Field(None, description="Chart configuration")
    provenance: Dict[str, Any] = Field(..., description="Data source information")
    created_at: datetime

    @model_validator(mode='before')
    @classmethod
    def convert_uuid_fields(cls, values):
        if isinstance(values, dict):
            # Convert message_id if it's a UUID
            if 'message_id' in values:
                message_id = values['message_id']
                if isinstance(message_id, UUID):
                    values['message_id'] = str(message_id)
                elif hasattr(message_id, '__str__') and 'uuid' in str(type(message_id)).lower():
                    values['message_id'] = str(message_id)

            # Convert conversation_id if it's a UUID
            if 'conversation_id' in values:
                conversation_id = values['conversation_id']
                if isinstance(conversation_id, UUID):
                    values['conversation_id'] = str(conversation_id)
                elif hasattr(conversation_id, '__str__') and 'uuid' in str(type(conversation_id)).lower():
                    values['conversation_id'] = str(conversation_id)
        # Handle SQLAlchemy model objects
        elif hasattr(values, 'message_id'):
            message_id = getattr(values, 'message_id')
            if isinstance(message_id, UUID):
                setattr(values, 'message_id', str(message_id))
            elif hasattr(message_id, '__str__') and 'uuid' in str(type(message_id)).lower():
                setattr(values, 'message_id', str(message_id))
        elif hasattr(values, 'conversation_id'):
            conversation_id = getattr(values, 'conversation_id')
            if isinstance(conversation_id, UUID):
                setattr(values, 'conversation_id', str(conversation_id))
            elif hasattr(conversation_id, '__str__') and 'uuid' in str(type(conversation_id)).lower():
                setattr(values, 'conversation_id', str(conversation_id))
        return values



class ConversationBase(BaseModel):
    model_config = ConfigDict(extra='forbid', validate_assignment=True)

    title: Optional[str] = Field(None, description="Conversation title")
    user_id: str = Field(..., description="User identifier")
    db_alias: Optional[str] = Field(None, description="Selected database alias")
    auto_execute_query: bool = Field(True, description="Auto execute generated queries")

    @model_validator(mode='before')
    @classmethod
    def convert_uuid_to_str(cls, values):
        if isinstance(values, dict) and 'user_id' in values:
            user_id = values['user_id']
            if isinstance(user_id, UUID):
                values['user_id'] = str(user_id)
            # Handle asyncpg UUID type and other UUID-like objects
            elif hasattr(user_id, '__str__') and 'uuid' in str(type(user_id)).lower():
                values['user_id'] = str(user_id)
        # Handle SQLAlchemy model objects
        elif hasattr(values, 'user_id'):
            user_id = getattr(values, 'user_id')
            if isinstance(user_id, UUID):
                setattr(values, 'user_id', str(user_id))
            elif hasattr(user_id, '__str__') and 'uuid' in str(type(user_id)).lower():
                setattr(values, 'user_id', str(user_id))
        return values

    @field_serializer('user_id')
    def serialize_user_id(self, value):
        if isinstance(value, UUID):
            return str(value)
        # Handle asyncpg UUID type
        if hasattr(value, '__str__') and 'uuid' in str(type(value)).lower():
            return str(value)
        return value


class ConversationCreate(BaseModel):
    model_config = ConfigDict(extra='forbid', validate_assignment=True)

    title: Optional[str] = Field(None, description="Conversation title")
    user_id: Optional[str] = Field(None, description="User identifier")
    db_alias: Optional[str] = Field(None, description="Selected database alias")
    auto_execute_query: bool = Field(True, description="Auto execute generated queries")


class Conversation(ConversationBase):
    model_config = ConfigDict(extra='forbid', validate_assignment=True, from_attributes=True)

    id: str
    created_at: datetime
    updated_at: datetime
    message_count: int = 0

    @model_validator(mode='before')
    @classmethod
    def convert_id_to_str(cls, values):
        if isinstance(values, dict) and 'id' in values:
            conv_id = values['id']
            if isinstance(conv_id, UUID):
                values['id'] = str(conv_id)
            elif hasattr(conv_id, '__str__') and 'uuid' in str(type(conv_id)).lower():
                values['id'] = str(conv_id)
        # Handle SQLAlchemy model objects
        elif hasattr(values, 'id'):
            conv_id = getattr(values, 'id')
            if isinstance(conv_id, UUID):
                setattr(values, 'id', str(conv_id))
            elif hasattr(conv_id, '__str__') and 'uuid' in str(type(conv_id)).lower():
                setattr(values, 'id', str(conv_id))
        return values

    @field_serializer('id')
    def serialize_id(self, value):
        if isinstance(value, UUID):
            return str(value)
        if hasattr(value, '__str__') and 'uuid' in str(type(value)).lower():
            return str(value)
        return value


class DrillDownRequest(BaseModel):
    answer_id: str = Field(..., description="Original answer ID to drill down from")
    filter_criteria: Dict[str, Any] = Field(..., description="Additional filters for drill-down")


class ExportRequest(BaseModel):
    answer_id: str = Field(..., description="Answer ID to export")
    format: str = Field(..., description="Export format: csv, excel, pdf")
    include_sql: bool = Field(False, description="Include SQL query in export")


class ExecutePendingQueryRequest(BaseModel):
    message_id: str = Field(..., description="Message ID containing the pending query")
    modified_sql: Optional[str] = Field(None, description="Modified SQL query to execute instead of original")


class RegenerateQueryRequest(BaseModel):
    message_id: str = Field(..., description="Message ID to regenerate query for")
    additional_context: Optional[str] = Field(None, description="Additional context to help regenerate the query")


class ChatReportGenerateRequest(BaseModel):
    title: str = Field(..., description="Report title")
    sql: str = Field(..., description="SQL query from the chat")
    data: Optional[List[Dict[str, Any]]] = Field(None, description="Table data from the chat response")
    chart_meta: Optional[Dict[str, Any]] = Field(None, description="Chart metadata from the chat response")
    db_alias: Optional[str] = Field(None, description="Database alias")
    tables: Optional[List[str]] = Field(None, description="Source tables")