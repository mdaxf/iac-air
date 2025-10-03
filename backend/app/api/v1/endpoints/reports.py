from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, desc

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.models.report import (
    Report, ReportDatasource, ReportComponent, ReportTemplate,
    ReportExecution, ReportShare, ReportType, ComponentType, ChartType
)
from app.schemas.report import (
    ReportCreate, ReportUpdate, Report as ReportSchema,
    ReportDetail, ReportListItem, ReportDatasourceCreate,
    ReportDatasourceUpdate, ReportDatasource as ReportDatasourceSchema,
    ReportComponentCreate, ReportComponentUpdate,
    ReportComponent as ReportComponentSchema, ReportExecutionRequest,
    ReportExecution as ReportExecutionSchema, ReportShareCreate,
    ReportShare as ReportShareSchema, ReportTemplateCreate,
    ReportTemplateUpdate, ReportTemplate as ReportTemplateSchema
)
from app.schemas.chat import ChatReportGenerateRequest
from app.schemas.report_parameter import (
    ReportViewRequest, ReportDataResponse, ReportParameterResponse,
    ReportParameterCreate, ReportParameterUpdate
)
from app.services.report_service import ReportService
from app.services.report_view_service import ReportViewService
from app.models.report_parameter import ReportParameter
from app.core.logging_config import log_method_calls, Logger, log_performance

router = APIRouter()
report_service = ReportService()


# Report CRUD operations
@router.post("/", response_model=ReportSchema)
async def create_report(
    report: ReportCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new report"""
    try:
        return await report_service.create_report(db, report, current_user.id)
    except Exception as e:
        Logger.error(f"Error creating report: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create report")


@router.get("", response_model=List[ReportListItem])
async def list_reports(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = Query(None),
    report_type: Optional[ReportType] = Query(None),
    is_template: Optional[bool] = Query(None),
    tags: Optional[str] = Query(None, description="Comma-separated tags"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List reports with filtering and pagination"""
    try:
        reports = await report_service.list_reports(
            db, current_user.id, skip, limit, search, report_type, is_template
        )

        # Get creator names for the reports
        creator_ids = list(set(report.created_by for report in reports))
        creators_query = select(User.id, User.username).where(User.id.in_(creator_ids))
        creators_result = await db.execute(creators_query)
        creators_map = {creator.id: creator.username for creator in creators_result}

        return [
            ReportListItem(
                id=report.id,
                name=report.name,
                description=report.description,
                report_type=report.report_type,
                is_template=report.is_template,
                is_public=report.is_public,
                created_by=report.created_by,
                creator_name=creators_map.get(report.created_by),
                created_at=report.created_at,
                updated_at=report.updated_at,
                last_executed_at=report.last_executed_at,
                tags=report.tags or []
            )
            for report in reports
        ]
    except Exception as e:
        Logger.error(f"Error listing reports: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to list reports")


@router.get("/{report_id}", response_model=ReportDetail)
async def get_report(
    report_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific report with all details"""
    try:
        report = await report_service.get_report(db, report_id, current_user.id)
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")
        return report
    except HTTPException:
        raise
    except Exception as e:
        Logger.error(f"Error getting report: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get report")


@router.put("/{report_id}", response_model=ReportSchema)
async def update_report(
    report_id: UUID,
    report_update: ReportUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update a report"""
    try:
        report = await report_service.update_report(db, report_id, report_update, current_user.id)
        if not report:
            raise HTTPException(status_code=404, detail="Report not found or access denied")
        return report
    except HTTPException:
        raise
    except Exception as e:
        Logger.error(f"Error updating report: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update report")


@router.put("/{report_id}/complete", response_model=ReportDetail)
async def update_complete_report(
    report_id: UUID,
    request: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update a complete report with all related data (metadata, components, etc.) in a single transaction"""
    try:
        Logger.info(f"=== COMPLETE REPORT UPDATE REQUEST ===")
        Logger.info(f"Report ID: {report_id}")
        Logger.info(f"Raw request data: {dict(request)}")
        Logger.info(f"Components in request: {request.get('components', [])}")

        # Validate request data integrity
        components = request.get('components', [])
        if not isinstance(components, list):
            raise HTTPException(status_code=400, detail="Components must be a list")

        # Check for malformed component data
        for i, comp in enumerate(components):
            if not isinstance(comp, dict):
                raise HTTPException(status_code=400, detail=f"Component {i} must be an object")

            # Check if component has incomplete data (like truncated JSON)
            if 'id' in comp and comp['id'] == '':
                raise HTTPException(status_code=400, detail=f"Component {i} has invalid empty ID")
            if 'id' in comp and not isinstance(comp['id'], str):
                raise HTTPException(status_code=400, detail=f"Component {i} has invalid ID type")

            # Check for truncated boolean values (common JSON truncation issue)
            for field, value in comp.items():
                if isinstance(value, str) and field in ['is_visible'] and value in ['tru', 'fals']:
                    raise HTTPException(status_code=400, detail=f"Component {i} has truncated boolean value in field '{field}': '{value}'. This suggests malformed JSON.")

            # Check for other incomplete values that might indicate truncation
            if 'is_visible' in comp and comp['is_visible'] not in [True, False, None]:
                raise HTTPException(status_code=400, detail=f"Component {i} has invalid is_visible value: {comp['is_visible']}")

        # Also check layout_config components if present
        layout_config = request.get('layout_config', {})
        if isinstance(layout_config, dict) and 'components' in layout_config:
            layout_components = layout_config['components']
            if isinstance(layout_components, list):
                for i, comp in enumerate(layout_components):
                    if isinstance(comp, dict) and 'is_visible' in comp:
                        if isinstance(comp['is_visible'], str) and comp['is_visible'] in ['tru', 'fals']:
                            raise HTTPException(status_code=400, detail=f"Layout component {i} has truncated boolean value. This suggests malformed JSON.")
                        if comp['is_visible'] not in [True, False, None]:
                            raise HTTPException(status_code=400, detail=f"Layout component {i} has invalid is_visible value: {comp['is_visible']}")

        # Extract only valid ReportUpdate fields from request
        report_update_fields = {
            'name', 'description', 'is_public', 'is_template',
            'layout_config', 'page_settings', 'tags'
        }
        report_update_data = {k: v for k, v in request.items()
                            if k in report_update_fields and k != 'components'}
        report_data = ReportUpdate(**report_update_data)
        components = request.get('components', [])

        Logger.info(f"Updating complete report {report_id} with {len(components)} components")

        updated_report = await report_service.update_complete_report(
            db, report_id, report_data, current_user.id, components
        )

        if not updated_report:
            raise HTTPException(status_code=404, detail="Report not found or access denied")

        return updated_report
    except HTTPException:
        raise
    except ValueError as e:
        Logger.error(f"Validation error updating complete report: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        import traceback
        from datetime import datetime
        error_msg = f"Error updating complete report: {str(e)}"
        full_traceback = traceback.format_exc()
        Logger.error(error_msg)
        Logger.error(f"Full traceback: {full_traceback}")

        # Write error to file for debugging since logs aren't showing
        try:
            with open("C:/working/projects/air/debug_error.log", "a") as f:
                f.write(f"\n=== REPORT UPDATE ERROR {datetime.now()} ===\n")
                f.write(f"Report ID: {report_id}\n")
                f.write(f"Error: {error_msg}\n")
                f.write(f"Traceback: {full_traceback}\n")
                f.write("="*50 + "\n")
        except:
            pass

        # For debugging, return the actual error message
        raise HTTPException(status_code=500, detail=f"Failed to update complete report: {str(e)}")


@router.delete("/{report_id}")
async def delete_report(
    report_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a report (soft delete)"""
    try:
        success = await report_service.delete_report(db, report_id, current_user.id)
        if not success:
            raise HTTPException(status_code=404, detail="Report not found or access denied")
        return {"message": "Report deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        Logger.error(f"Error deleting report: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete report")


# Datasource operations
@router.post("/{report_id}/datasources", response_model=ReportDatasourceSchema)
async def create_datasource(
    report_id: UUID,
    datasource: ReportDatasourceCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Add a datasource to a report"""
    try:
        # Verify report ownership
        result = await db.execute(
            select(Report).where(
                and_(
                    Report.id == report_id,
                    Report.created_by == current_user.id
                )
            )
        )
        report = result.scalar_one_or_none()

        if not report:
            raise HTTPException(status_code=404, detail="Report not found or access denied")

        db_datasource = ReportDatasource(**datasource.model_dump())
        db.add(db_datasource)
        await db.commit()
        await db.refresh(db_datasource)
        return db_datasource
    except HTTPException:
        raise
    except Exception as e:
        Logger.error(f"Error creating datasource: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create datasource: {str(e)}")


@router.get("/{report_id}/datasources", response_model=List[ReportDatasourceSchema])
async def list_datasources(
    report_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List datasources for a report"""
    try:
        # Verify report access
        result = await db.execute(
            select(Report).where(
                and_(
                    Report.id == report_id,
                    or_(
                        Report.created_by == current_user.id,
                        Report.is_public == True
                    )
                )
            )
        )
        report = result.scalar_one_or_none()

        if not report:
            raise HTTPException(status_code=404, detail="Report not found")

        datasources_result = await db.execute(
            select(ReportDatasource).where(ReportDatasource.report_id == report_id)
        )
        return datasources_result.scalars().all()
    except HTTPException:
        raise
    except Exception as e:
        Logger.error(f"Error listing datasources: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to list datasources")


@router.put("/{report_id}/datasources/{datasource_id}", response_model=ReportDatasourceSchema)
async def update_datasource(
    report_id: UUID,
    datasource_id: UUID,
    datasource_update: ReportDatasourceUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update a datasource"""
    try:
        # Verify report ownership
        result = await db.execute(
            select(Report).where(
                and_(
                    Report.id == report_id,
                    Report.created_by == current_user.id
                )
            )
        )
        report = result.scalar_one_or_none()

        if not report:
            raise HTTPException(status_code=404, detail="Report not found or access denied")

        # Get datasource
        ds_result = await db.execute(
            select(ReportDatasource).where(
                and_(
                    ReportDatasource.id == datasource_id,
                    ReportDatasource.report_id == report_id
                )
            )
        )
        datasource = ds_result.scalar_one_or_none()

        if not datasource:
            raise HTTPException(status_code=404, detail="Datasource not found")

        # Update fields
        update_data = datasource_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(datasource, field, value)

        await db.commit()
        await db.refresh(datasource)
        return datasource
    except HTTPException:
        raise
    except Exception as e:
        Logger.error(f"Error updating datasource: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update datasource")


@router.delete("/{report_id}/datasources/{datasource_id}")
async def delete_datasource(
    report_id: UUID,
    datasource_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a datasource"""
    try:
        # Verify report ownership
        result = await db.execute(
            select(Report).where(
                and_(
                    Report.id == report_id,
                    Report.created_by == current_user.id
                )
            )
        )
        report = result.scalar_one_or_none()

        if not report:
            raise HTTPException(status_code=404, detail="Report not found or access denied")

        # Get datasource
        ds_result = await db.execute(
            select(ReportDatasource).where(
                and_(
                    ReportDatasource.id == datasource_id,
                    ReportDatasource.report_id == report_id
                )
            )
        )
        datasource = ds_result.scalar_one_or_none()

        if not datasource:
            raise HTTPException(status_code=404, detail="Datasource not found")

        # Check for component dependencies
        components_result = await db.execute(
            select(ReportComponent).where(
                and_(
                    ReportComponent.report_id == report_id,
                    ReportComponent.datasource_alias == datasource.alias
                )
            )
        )
        linked_components = components_result.scalars().all()

        if linked_components:
            component_names = [comp.name for comp in linked_components]
            raise HTTPException(
                status_code=400,
                detail=f"Cannot delete datasource. It is linked to components: {', '.join(component_names)}"
            )

        await db.delete(datasource)
        await db.commit()

        return {"message": "Datasource deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        Logger.error(f"Error deleting datasource: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete datasource")


# Component operations
@router.post("/{report_id}/components", response_model=ReportComponentSchema)
async def create_component(
    report_id: UUID,
    component: ReportComponentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Add a component to a report"""
    try:
        # Verify report ownership
        result = await db.execute(
            select(Report).where(
                and_(
                    Report.id == report_id,
                    Report.created_by == current_user.id
                )
            )
        )
        report = result.scalar_one_or_none()

        if not report:
            raise HTTPException(status_code=404, detail="Report not found or access denied")

        db_component = ReportComponent(
            **component.model_dump(),
            report_id=report_id
        )
        db.add(db_component)
        await db.commit()
        await db.refresh(db_component)
        return db_component
    except HTTPException:
        raise
    except Exception as e:
        Logger.error(f"Error creating component: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create component")


@router.get("/{report_id}/components", response_model=List[ReportComponentSchema])
async def list_components(
    report_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List components for a report"""
    try:
        # Verify report access
        result = await db.execute(
            select(Report).where(
                and_(
                    Report.id == report_id,
                    or_(
                        Report.created_by == current_user.id,
                        Report.is_public == True
                    )
                )
            )
        )
        report = result.scalar_one_or_none()

        if not report:
            raise HTTPException(status_code=404, detail="Report not found")

        components_result = await db.execute(
            select(ReportComponent)
            .where(ReportComponent.report_id == report_id)
            .order_by(ReportComponent.z_index)
        )
        return components_result.scalars().all()
    except HTTPException:
        raise
    except Exception as e:
        Logger.error(f"Error listing components: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to list components")


@router.put("/{report_id}/components/{component_id}", response_model=ReportComponentSchema)
async def update_component(
    report_id: UUID,
    component_id: UUID,
    component_update: ReportComponentUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update a component"""
    try:
        # Verify report ownership
        result = await db.execute(
            select(Report).where(
                and_(
                    Report.id == report_id,
                    Report.created_by == current_user.id
                )
            )
        )
        report = result.scalar_one_or_none()

        if not report:
            raise HTTPException(status_code=404, detail="Report not found or access denied")

        # Get component
        comp_result = await db.execute(
            select(ReportComponent).where(
                and_(
                    ReportComponent.id == component_id,
                    ReportComponent.report_id == report_id
                )
            )
        )
        component = comp_result.scalar_one_or_none()

        if not component:
            raise HTTPException(status_code=404, detail="Component not found")

        # Update fields
        update_data = component_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(component, field, value)

        await db.commit()
        await db.refresh(component)
        return component
    except HTTPException:
        raise
    except Exception as e:
        Logger.error(f"Error updating component: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update component")


@router.delete("/{report_id}/components/{component_id}")
async def delete_component(
    report_id: UUID,
    component_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a component"""
    try:
        # Verify report ownership
        result = await db.execute(
            select(Report).where(
                and_(
                    Report.id == report_id,
                    Report.created_by == current_user.id
                )
            )
        )
        report = result.scalar_one_or_none()

        if not report:
            raise HTTPException(status_code=404, detail="Report not found or access denied")

        # Delete component
        comp_result = await db.execute(
            select(ReportComponent).where(
                and_(
                    ReportComponent.id == component_id,
                    ReportComponent.report_id == report_id
                )
            )
        )
        component = comp_result.scalar_one_or_none()

        if not component:
            raise HTTPException(status_code=404, detail="Component not found")

        await db.delete(component)
        await db.commit()

        return {"message": "Component deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        Logger.error(f"Error deleting component: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete component")


# Report execution
@router.post("/{report_id}/execute", response_model=ReportExecutionSchema)
async def execute_report(
    report_id: UUID,
    execution_request: ReportExecutionRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Execute a report and generate output"""
    try:
        # Verify report access
        result = await db.execute(
            select(Report).where(
                and_(
                    Report.id == report_id,
                    or_(
                        Report.created_by == current_user.id,
                        Report.is_public == True
                    )
                )
            )
        )
        report = result.scalar_one_or_none()

        if not report:
            raise HTTPException(status_code=404, detail="Report not found")

        # Create execution record
        execution = ReportExecution(
            report_id=report_id,
            executed_by=current_user.id,
            parameters=execution_request.parameters,
            output_format=execution_request.output_format,
            execution_status="running"
        )
        db.add(execution)
        await db.commit()
        await db.refresh(execution)

        # Execute report in background
        background_tasks.add_task(
            report_service.execute_report_background,
            execution.id,
            report_id,
            execution_request.parameters,
            execution_request.output_format
        )

        return execution
    except HTTPException:
        raise
    except Exception as e:
        Logger.error(f"Error executing report: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to execute report")


@router.get("/{report_id}/executions", response_model=List[ReportExecutionSchema])
async def list_executions(
    report_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List execution history for a report"""
    try:
        # Verify report access
        result = await db.execute(
            select(Report).where(
                and_(
                    Report.id == report_id,
                    or_(
                        Report.created_by == current_user.id,
                        Report.is_public == True
                    )
                )
            )
        )
        report = result.scalar_one_or_none()

        if not report:
            raise HTTPException(status_code=404, detail="Report not found")

        executions_result = await db.execute(
            select(ReportExecution)
            .where(ReportExecution.report_id == report_id)
            .order_by(desc(ReportExecution.created_at))
            .offset(skip)
            .limit(limit)
        )
        return executions_result.scalars().all()
    except HTTPException:
        raise
    except Exception as e:
        Logger.error(f"Error listing executions: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to list executions")


# Report sharing
@router.post("/{report_id}/share", response_model=ReportShareSchema)
async def share_report(
    report_id: UUID,
    share_request: ReportShareCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Share a report with another user or publicly"""
    try:
        # Verify report ownership
        result = await db.execute(
            select(Report).where(
                and_(
                    Report.id == report_id,
                    Report.created_by == current_user.id
                )
            )
        )
        report = result.scalar_one_or_none()

        if not report:
            raise HTTPException(status_code=404, detail="Report not found or access denied")

        # Create share record
        share = ReportShare(
            report_id=report_id,
            shared_by=current_user.id,
            **share_request.model_dump()
        )

        # Generate share token for public shares
        if share_request.shared_with is None:
            import secrets
            share.share_token = secrets.token_urlsafe(32)

        db.add(share)
        await db.commit()
        await db.refresh(share)
        return share
    except HTTPException:
        raise
    except Exception as e:
        Logger.error(f"Error sharing report: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to share report")


# Template operations
@router.get("/templates", response_model=List[ReportTemplateSchema])
async def list_templates(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    category: Optional[str] = Query(None),
    ai_compatible: Optional[bool] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List available report templates"""
    try:
        return await report_service.list_templates(db, skip, limit, category, ai_compatible)
    except Exception as e:
        Logger.error(f"Error listing templates: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to list templates")


@router.post("/templates", response_model=ReportTemplateSchema)
async def create_template(
    template: ReportTemplateCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new report template"""
    try:
        return await report_service.create_template(db, template, current_user.id)
    except Exception as e:
        Logger.error(f"Error creating template: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create template")


@router.post("/templates/{template_id}/create-report", response_model=ReportSchema)
async def create_report_from_template(
    template_id: UUID,
    request_body: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new report from a template"""
    try:
        report_name = request_body.get("name")
        if not report_name:
            raise HTTPException(status_code=400, detail="Report name is required")

        return await report_service.create_report_from_template(
            db, template_id, report_name, current_user.id
        )
    except HTTPException:
        raise
    except Exception as e:
        Logger.error(f"Error creating report from template: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create report from template")


# Generate report from chat response
@router.post("/generate-from-chat", response_model=dict)
async def generate_report_from_chat(
    request: ChatReportGenerateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Generate a report from AI chat response data."""
    try:
        # Create the report
        report_create = ReportCreate(
            name=request.title,
            description=f"Generated from AI chat: {request.title}",
            report_type=ReportType.MANUAL,  # Use MANUAL to avoid enum issues
            canvas_config={
                "width": 1920,
                "height": 1080,
                "background": "#ffffff"
            }
        )

        report = await report_service.create_report(db, report_create, current_user.id)

        # Create datasource from SQL with proper field definitions
        datasource = None
        if request.sql and request.db_alias:
            # Generate field definitions from AI data - for custom queries, fields come from query output
            selected_fields = []
            if request.data and len(request.data) > 0:
                first_row = request.data[0]
                for i, (field_name, field_value) in enumerate(first_row.items()):
                    # Determine field type from value
                    field_type = "varchar"
                    if isinstance(field_value, (int, float)):
                        field_type = "numeric"
                    elif isinstance(field_value, bool):
                        field_type = "boolean"

                    # For custom queries, fields don't map to specific tables - they come from query result
                    selected_fields.append({
                        "field": field_name,
                        "alias": field_name,
                        "data_type": field_type,
                        "display_name": field_name.replace("_", " ").title(),
                        "sort_order": i + 1,
                        "visible": True,
                        "aggregation": None,
                        "source": "query"  # Indicate this field comes from query output
                    })

            datasource_create = ReportDatasourceCreate(
                report_id=report.id,
                name=f"{request.title} Data",
                alias=f"chat_data_{str(report.id).replace('-', '_')}",
                database_alias=request.db_alias,
                query_type="custom",
                custom_sql=request.sql,
                selected_fields=selected_fields,
                selected_tables=[]  # Empty for custom queries - not using visual table selection
            )

            # Use the service method to create datasource properly
            datasource = await report_service.create_datasource(db, datasource_create, current_user.id)

        components = []

        # Create table component if we have data
        if request.data and datasource:
            # Get column information from the datasource fields - for custom queries, no table mapping
            table_columns = []
            for field in datasource.selected_fields:
                table_columns.append({
                    "field": field["field"],
                    "display_name": field["display_name"],
                    "visible": field["visible"],
                    "width": "150px",
                    "align": "left",
                    "sort_order": field["sort_order"],
                    "data_type": field["data_type"],
                    "alias": field["alias"],
                    "source": field.get("source", "query")  # Custom query fields come from query output
                })

            table_component = ReportComponent(
                report_id=report.id,
                name="Data Table",
                component_type=ComponentType.TABLE,
                x=50,
                y=50,
                width=800,
                height=400,
                z_index=1,
                datasource_alias=datasource.alias,
                data_config={
                    "columns": table_columns,
                    "datasource_alias": datasource.alias,
                    "query_type": "custom",  # Indicate this uses custom query
                    "field_mapping": {field["field"]: field["alias"] for field in datasource.selected_fields}
                },
                component_config={
                    "showHeader": True,
                    "pagination": {
                        "enabled": True,
                        "pageSize": 10
                    },
                    "sorting": {
                        "enabled": True
                    }
                }
            )
            db.add(table_component)
            components.append("table")

        # Create chart component if we have chart metadata
        if request.chart_meta and request.data and datasource:
            chart_type_str = request.chart_meta.get('type', 'bar')
            # Map string to enum
            chart_type_enum = ChartType.BAR if chart_type_str == 'bar' else ChartType.LINE

            # Find the field references in the datasource
            x_field = request.chart_meta.get('x_axis')
            y_field = request.chart_meta.get('y_axis')

            chart_component = ReportComponent(
                report_id=report.id,
                name="Chart",
                component_type=ComponentType.CHART,
                x=900,
                y=50,
                width=600,
                height=400,
                z_index=2,
                datasource_alias=datasource.alias,
                chart_type=chart_type_enum,
                data_config={
                    "datasource_alias": datasource.alias,
                    "x_field": x_field,
                    "y_field": y_field,
                    "query_type": "custom",  # Indicate this uses custom query
                    "field_mapping": {field["field"]: field["alias"] for field in datasource.selected_fields}
                },
                chart_config={
                    "xAxis": {
                        "field": x_field,
                        "label": x_field.replace("_", " ").title() if x_field else ""
                    },
                    "yAxis": {
                        "field": y_field,
                        "label": y_field.replace("_", " ").title() if y_field else ""
                    },
                    "legend": {
                        "enabled": True,
                        "position": "right"
                    },
                    "tooltip": {
                        "enabled": True
                    }
                }
            )
            db.add(chart_component)
            components.append("chart")

        await db.commit()

        Logger.info(f"Generated report {report.id} from chat with components: {', '.join(components)}")

        return {
            "report_id": str(report.id),
            "message": f"Report '{request.title}' created successfully with {len(components)} components",
            "components": components
        }

    except Exception as e:
        Logger.error(f"Error generating report from chat: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate report: {str(e)}")


# Report viewing and parameter management endpoints
@router.post("/{report_id}/view", response_model=ReportDataResponse)
async def view_report_with_data(
    report_id: UUID,
    request: ReportViewRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Execute a report with given parameters and return the data for viewing
    """
    try:
        # Convert to sync session for ReportViewService
        from app.core.database import SessionLocal
        sync_db = SessionLocal()
        try:
            # Set the report_id from URL
            request.report_id = str(report_id)

            service = ReportViewService(sync_db)
            result = service.execute_report(request)
            return result
        finally:
            sync_db.close()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        Logger.error(f"Error viewing report: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Report viewing failed: {str(e)}")


@router.get("/{report_id}/parameters", response_model=List[ReportParameterResponse])
async def get_report_parameters(
    report_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all parameters for a report
    """
    try:
        # Convert to sync session for ReportViewService
        from app.core.database import SessionLocal
        sync_db = SessionLocal()
        try:
            service = ReportViewService(sync_db)
            parameters = service.get_report_parameters(str(report_id))
            return parameters
        finally:
            sync_db.close()
    except Exception as e:
        Logger.error(f"Error getting report parameters: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{report_id}/parameters", response_model=ReportParameterResponse)
async def create_report_parameter(
    report_id: UUID,
    parameter: ReportParameterCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new parameter for a report
    """
    try:
        # Convert to sync session for ReportParameter operations
        from app.core.database import SessionLocal
        sync_db = SessionLocal()
        try:
            # Ensure report_id matches
            parameter.report_id = str(report_id)

            db_parameter = ReportParameter(**parameter.dict())
            sync_db.add(db_parameter)
            sync_db.commit()
            sync_db.refresh(db_parameter)
            return db_parameter
        finally:
            sync_db.close()
    except Exception as e:
        Logger.error(f"Error creating report parameter: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/parameters/{parameter_id}", response_model=ReportParameterResponse)
async def update_report_parameter(
    parameter_id: str,
    parameter_update: ReportParameterUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update a report parameter
    """
    try:
        # Convert to sync session for ReportParameter operations
        from app.core.database import SessionLocal
        sync_db = SessionLocal()
        try:
            db_parameter = sync_db.query(ReportParameter).filter(ReportParameter.id == parameter_id).first()
            if not db_parameter:
                raise HTTPException(status_code=404, detail="Parameter not found")

            # Update fields
            update_data = parameter_update.dict(exclude_unset=True)
            for field, value in update_data.items():
                setattr(db_parameter, field, value)

            sync_db.commit()
            sync_db.refresh(db_parameter)
            return db_parameter
        finally:
            sync_db.close()
    except HTTPException:
        raise
    except Exception as e:
        Logger.error(f"Error updating report parameter: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/parameters/{parameter_id}")
async def delete_report_parameter(
    parameter_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a report parameter
    """
    try:
        # Convert to sync session for ReportParameter operations
        from app.core.database import SessionLocal
        sync_db = SessionLocal()
        try:
            db_parameter = sync_db.query(ReportParameter).filter(ReportParameter.id == parameter_id).first()
            if not db_parameter:
                raise HTTPException(status_code=404, detail="Parameter not found")

            sync_db.delete(db_parameter)
            sync_db.commit()
            return {"message": "Parameter deleted successfully"}
        finally:
            sync_db.close()
    except HTTPException:
        raise
    except Exception as e:
        Logger.error(f"Error deleting report parameter: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Datasource validation endpoints
@router.post("/{report_id}/datasources/{datasource_id}/validate")
async def validate_datasource(
    report_id: UUID,
    datasource_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Validate a datasource configuration
    """
    try:
        # Get datasource
        ds_result = await db.execute(
            select(ReportDatasource).where(
                and_(
                    ReportDatasource.id == datasource_id,
                    ReportDatasource.report_id == report_id
                )
            )
        )
        datasource = ds_result.scalar_one_or_none()

        if not datasource:
            raise HTTPException(status_code=404, detail="Datasource not found")

        # Convert to sync session for ReportViewService
        from app.core.database import SessionLocal
        sync_db = SessionLocal()
        try:
            service = ReportViewService(sync_db)
            validation_result = service.validate_datasource_configuration(datasource)
            return validation_result
        finally:
            sync_db.close()

    except HTTPException:
        raise
    except Exception as e:
        Logger.error(f"Error validating datasource: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Datasource validation failed: {str(e)}")


@router.post("/{report_id}/datasources/{datasource_id}/test")
async def test_datasource(
    report_id: UUID,
    datasource_id: UUID,
    request_body: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Test execute a datasource configuration
    """
    try:
        # Get datasource
        ds_result = await db.execute(
            select(ReportDatasource).where(
                and_(
                    ReportDatasource.id == datasource_id,
                    ReportDatasource.report_id == report_id
                )
            )
        )
        datasource = ds_result.scalar_one_or_none()

        if not datasource:
            raise HTTPException(status_code=404, detail="Datasource not found")

        # Extract test parameters from request
        test_parameters = request_body.get('parameters', {})

        # Convert to sync session for ReportViewService
        from app.core.database import SessionLocal
        sync_db = SessionLocal()
        try:
            service = ReportViewService(sync_db)
            test_result = service.test_datasource_execution(datasource, test_parameters)
            return test_result
        finally:
            sync_db.close()

    except HTTPException:
        raise
    except Exception as e:
        Logger.error(f"Error testing datasource: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Datasource test failed: {str(e)}")