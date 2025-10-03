from typing import List, Optional, Dict, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, desc
from sqlalchemy.orm import selectinload

from app.core.logging_config import Logger, log_method_calls
from app.models.report import (
    Report, ReportDatasource, ReportComponent, ReportTemplate,
    ReportExecution, ReportShare, ReportType
)
from app.schemas.report import (
    ReportCreate, ReportUpdate, ReportDetail,
    ReportDatasourceCreate, ReportDatasourceUpdate,
    ReportComponentCreate, ReportComponentUpdate,
    ReportTemplateCreate, ReportTemplateUpdate,
    ReportExecutionRequest, ReportShareCreate
)
from app.models.user import User


class ReportService:
    def __init__(self):
        pass

    @log_method_calls
    async def create_report(self, db: AsyncSession, report_data: ReportCreate, user_id: UUID) -> Report:
        """Create a new report"""
        try:
            db_report = Report(
                **report_data.model_dump(),
                created_by=user_id
            )
            db.add(db_report)
            await db.commit()
            await db.refresh(db_report)
            Logger.info(f"Created report {db_report.id} by user {user_id}")
            return db_report
        except Exception as e:
            Logger.error(f"Error creating report: {str(e)}")
            await db.rollback()
            raise

    @log_method_calls
    async def get_report(self, db: AsyncSession, report_id: UUID, user_id: UUID) -> Optional[ReportDetail]:
        """Get a report with all related data"""
        try:
            query = (
                select(Report)
                .options(
                    selectinload(Report.datasources),
                    selectinload(Report.components)
                )
                .where(
                    and_(
                        Report.id == report_id,
                        Report.is_active == True,
                        or_(
                            Report.created_by == user_id,
                            Report.is_public == True
                        )
                    )
                )
            )
            result = await db.execute(query)
            report = result.scalar_one_or_none()

            if not report:
                return None

            # Get creator name
            creator_query = select(User.username).where(User.id == report.created_by)
            creator_result = await db.execute(creator_query)
            creator_name = creator_result.scalar_one_or_none()

            # Get template source name if applicable
            template_source_name = None
            if report.template_source_id:
                template_query = select(ReportTemplate.name).where(ReportTemplate.id == report.template_source_id)
                template_result = await db.execute(template_query)
                template_source_name = template_result.scalar_one_or_none()

            # Create a copy of the report dict excluding relationship fields to avoid conflicts
            report_dict = {k: v for k, v in report.__dict__.items()
                          if k not in ['datasources', 'components', '_sa_instance_state']}

            return ReportDetail(
                **report_dict,
                datasources=report.datasources,
                components=report.components,
                creator_name=creator_name,
                template_source_name=template_source_name
            )
        except Exception as e:
            Logger.error(f"Error getting report {report_id}: {str(e)}")
            raise

    @log_method_calls
    async def update_report(self, db: AsyncSession, report_id: UUID, report_data: ReportUpdate, user_id: UUID) -> Optional[Report]:
        """Update a report"""
        try:
            query = select(Report).where(
                and_(
                    Report.id == report_id,
                    Report.created_by == user_id,
                    Report.is_active == True
                )
            )
            result = await db.execute(query)
            report = result.scalar_one_or_none()

            if not report:
                return None

            update_data = report_data.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(report, field, value)

            # Increment version
            report.version += 1

            await db.commit()
            await db.refresh(report)
            Logger.info(f"Updated report {report_id} to version {report.version}")
            return report
        except Exception as e:
            Logger.error(f"Error updating report {report_id}: {str(e)}")
            await db.rollback()
            raise

    @log_method_calls
    async def update_complete_report(self, db: AsyncSession, report_id: UUID, report_data: ReportUpdate, user_id: UUID, components: List[Dict[str, Any]] = None) -> Optional[ReportDetail]:
        """Update a complete report with all related data in a single transaction"""
        try:
            # Verify user owns the report
            query = select(Report).options(
                selectinload(Report.components)
            ).where(
                and_(
                    Report.id == report_id,
                    Report.created_by == user_id,
                    Report.is_active == True
                )
            )
            result = await db.execute(query)
            report = result.scalar_one_or_none()

            if not report:
                return None

            # Update report metadata
            update_data = report_data.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                if field != 'layout_config' or not components:  # Skip layout_config if we have components data
                    setattr(report, field, value)

            # Increment version
            report.version += 1

            # Update components if provided
            if components is not None:
                Logger.info(f"Updating {len(components)} components for report {report_id}")

                # Get existing components
                existing_components = report.components
                existing_component_ids = {comp.id for comp in existing_components}

                # Identify new components (don't have database IDs or have temp IDs)
                new_components = []
                update_components = []

                # Deduplicate components by ID to prevent processing the same component multiple times
                # Also handle components without IDs by considering their content
                seen_component_ids = set()
                seen_component_signatures = set()
                deduplicated_components = []

                for i, comp_data in enumerate(components):
                    comp_id = comp_data.get('id')

                    # Create a signature for components without IDs
                    comp_signature = f"{comp_data.get('name', '')}-{comp_data.get('component_type', '')}-{comp_data.get('x', 0)}-{comp_data.get('y', 0)}"

                    # Skip if we've seen this component ID before
                    if comp_id and comp_id in seen_component_ids:
                        Logger.warning(f"Duplicate component ID {comp_id} found at index {i}, skipping duplicate")
                        continue

                    # Skip if we've seen this exact component signature before (for components without IDs)
                    if not comp_id and comp_signature in seen_component_signatures:
                        Logger.warning(f"Duplicate component signature {comp_signature} found at index {i}, skipping duplicate")
                        continue

                    # Track this component
                    if comp_id:
                        seen_component_ids.add(comp_id)
                    else:
                        seen_component_signatures.add(comp_signature)

                    deduplicated_components.append(comp_data)

                Logger.info(f"Deduplicated {len(components)} components to {len(deduplicated_components)} components")

                for comp_data in deduplicated_components:
                    comp_id = comp_data.get('id')
                    if not comp_id or comp_id not in existing_component_ids:
                        # New component
                        new_components.append(comp_data)
                    else:
                        # Update existing component
                        update_components.append(comp_data)

                # Delete components that no longer exist
                new_component_temp_ids = {comp.get('id') for comp in deduplicated_components if comp.get('id')}
                for existing_comp in existing_components:
                    if existing_comp.id not in new_component_temp_ids:
                        Logger.info(f"Deleting component {existing_comp.id}")
                        await db.delete(existing_comp)

                # Create new components
                for comp_data in new_components:
                    try:
                        Logger.info(f"Processing new component data: {comp_data}")

                        # Remove problematic fields that frontend might send but shouldn't be in component creation
                        excluded_fields = [
                            'id', 'report_id',  # Existing exclusions
                            'created_at', 'updated_at',  # Timestamp fields that SQLAlchemy manages
                        ]
                        comp_data_clean = {k: v for k, v in comp_data.items() if k not in excluded_fields}
                        Logger.info(f"Cleaned component data: {comp_data_clean}")

                        # Apply defaults for missing required fields
                        from app.models.report import ComponentType

                        # Handle component_type field mapping and defaults
                        if 'component_type' not in comp_data_clean:
                            # Check if they used 'type' instead of 'component_type'
                            if 'type' in comp_data_clean:
                                comp_data_clean['component_type'] = comp_data_clean.pop('type')
                                Logger.info(f"Mapped 'type' field to 'component_type' for component")
                            else:
                                # Default to 'text' component type
                                comp_data_clean['component_type'] = ComponentType.TEXT.value
                                Logger.info(f"Applied default component_type: {ComponentType.TEXT.value}")

                        # Apply default name if missing
                        if 'name' not in comp_data_clean:
                            # Generate a default name based on component type
                            comp_type = comp_data_clean.get('component_type', 'component')
                            comp_data_clean['name'] = f"New {comp_type.title()} Component"
                            Logger.info(f"Applied default name: {comp_data_clean['name']}")

                        # Validate component_type is valid, apply default if invalid
                        valid_types = [e.value for e in ComponentType]
                        if comp_data_clean['component_type'] not in valid_types:
                            Logger.warning(f"Invalid component_type '{comp_data_clean['component_type']}', using default 'text'")
                            comp_data_clean['component_type'] = ComponentType.TEXT.value

                        # Apply other defaults for common fields
                        defaults = {
                            'x': 0,
                            'y': 0,
                            'width': 200,
                            'height': 100,
                            'z_index': 1,
                            'data_config': {},
                            'component_config': {},
                            'style_config': {},
                            'chart_config': {},
                            'barcode_config': {},
                            'drill_down_config': {},
                            'conditional_formatting': [],
                            'is_visible': True
                        }

                        for field, default_value in defaults.items():
                            if field not in comp_data_clean:
                                comp_data_clean[field] = default_value

                        # Additional safety validation
                        if not comp_data_clean.get('component_type'):
                            Logger.error(f"Component missing component_type after processing: {comp_data_clean}")
                            raise ValueError("Component must have a valid component_type")

                        if not comp_data_clean.get('name'):
                            Logger.error(f"Component missing name after processing: {comp_data_clean}")
                            raise ValueError("Component must have a name")

                        # Ensure numeric fields are properly typed
                        for numeric_field in ['x', 'y', 'width', 'height', 'z_index']:
                            if numeric_field in comp_data_clean and comp_data_clean[numeric_field] is not None:
                                try:
                                    comp_data_clean[numeric_field] = float(comp_data_clean[numeric_field])
                                except (ValueError, TypeError):
                                    Logger.warning(f"Invalid {numeric_field} value: {comp_data_clean[numeric_field]}, using default")
                                    comp_data_clean[numeric_field] = defaults.get(numeric_field, 0)

                        try:
                            db_component = ReportComponent(
                                **comp_data_clean,
                                report_id=report_id
                            )
                            db.add(db_component)
                            Logger.info(f"Creating new component: {comp_data.get('name', 'Unnamed')} of type {comp_data.get('component_type')}")
                        except Exception as db_error:
                            # Write detailed error to file for debugging
                            try:
                                with open("C:/working/projects/air/component_error.log", "a") as f:
                                    from datetime import datetime
                                    f.write(f"\n=== COMPONENT CREATION ERROR {datetime.now()} ===\n")
                                    f.write(f"Original component data: {comp_data}\n")
                                    f.write(f"Cleaned component data: {comp_data_clean}\n")
                                    f.write(f"DB Error: {str(db_error)}\n")
                                    f.write("="*50 + "\n")
                            except:
                                pass
                            raise db_error
                    except Exception as e:
                        Logger.error(f"Error creating component: {str(e)}")
                        raise ValueError(f"Invalid component data: {str(e)}")

                # Update existing components
                for comp_data in update_components:
                    try:
                        comp_id = comp_data['id']
                        existing_comp = next((c for c in existing_components if c.id == comp_id), None)
                        if existing_comp:
                            # Remove problematic fields from component updates
                            excluded_update_fields = ['id', 'report_id', 'created_at', 'updated_at']
                            update_comp_data = {k: v for k, v in comp_data.items() if k not in excluded_update_fields}

                            # Handle field mapping and validation for updates
                            from app.models.report import ComponentType

                            # Handle component_type field mapping
                            if 'type' in update_comp_data and 'component_type' not in update_comp_data:
                                update_comp_data['component_type'] = update_comp_data.pop('type')
                                Logger.info(f"Mapped 'type' field to 'component_type' for component update")

                            # Validate component_type if being updated
                            if 'component_type' in update_comp_data:
                                valid_types = [e.value for e in ComponentType]
                                if update_comp_data['component_type'] not in valid_types:
                                    Logger.warning(f"Invalid component_type '{update_comp_data['component_type']}' in update, keeping existing value")
                                    del update_comp_data['component_type']  # Remove invalid value, keep existing

                            # Ensure numeric fields are properly typed in updates
                            for numeric_field in ['x', 'y', 'width', 'height', 'z_index']:
                                if numeric_field in update_comp_data and update_comp_data[numeric_field] is not None:
                                    try:
                                        update_comp_data[numeric_field] = float(update_comp_data[numeric_field])
                                    except (ValueError, TypeError):
                                        Logger.warning(f"Invalid {numeric_field} value in update: {update_comp_data[numeric_field]}, skipping")
                                        del update_comp_data[numeric_field]

                            try:
                                for field, value in update_comp_data.items():
                                    setattr(existing_comp, field, value)
                                Logger.info(f"Updating existing component {comp_id}")
                            except Exception as update_error:
                                # Write detailed error to file for debugging
                                try:
                                    with open("C:/working/projects/air/update_error.log", "a") as f:
                                        from datetime import datetime
                                        f.write(f"\n=== COMPONENT UPDATE ERROR {datetime.now()} ===\n")
                                        f.write(f"Component ID: {comp_id}\n")
                                        f.write(f"Original component data: {comp_data}\n")
                                        f.write(f"Update component data: {update_comp_data}\n")
                                        f.write(f"Update Error: {str(update_error)}\n")
                                        f.write("="*50 + "\n")
                                except:
                                    pass
                                raise update_error
                    except Exception as e:
                        Logger.error(f"Error updating component {comp_id}: {str(e)}")
                        raise ValueError(f"Invalid component update data: {str(e)}")

            try:
                await db.commit()
                await db.refresh(report)
            except Exception as commit_error:
                Logger.error(f"Database commit failed: {str(commit_error)}")
                await db.rollback()
                raise ValueError(f"Database transaction failed: {str(commit_error)}")

            # Return the complete updated report
            return await self.get_report(db, report_id, user_id)
        except Exception as e:
            Logger.error(f"Error updating complete report {report_id}: {str(e)}")
            await db.rollback()
            raise

    @log_method_calls
    async def delete_report(self, db: AsyncSession, report_id: UUID, user_id: UUID) -> bool:
        """Soft delete a report"""
        try:
            query = select(Report).where(
                and_(
                    Report.id == report_id,
                    Report.created_by == user_id,
                    Report.is_active == True
                )
            )
            result = await db.execute(query)
            report = result.scalar_one_or_none()

            if not report:
                return False

            report.is_active = False
            await db.commit()
            Logger.info(f"Deleted report {report_id}")
            return True
        except Exception as e:
            Logger.error(f"Error deleting report {report_id}: {str(e)}")
            await db.rollback()
            raise

    @log_method_calls
    async def list_reports(self, db: AsyncSession, user_id: UUID, skip: int = 0, limit: int = 100,
                          search: Optional[str] = None, report_type: Optional[ReportType] = None,
                          is_template: Optional[bool] = None) -> List[Report]:
        """List reports with filters"""
        try:
            query = select(Report).where(
                and_(
                    Report.is_active == True,
                    or_(
                        Report.created_by == user_id,
                        Report.is_public == True
                    )
                )
            )

            if search:
                query = query.where(
                    or_(
                        Report.name.icontains(search),
                        Report.description.icontains(search)
                    )
                )

            if report_type:
                query = query.where(Report.report_type == report_type)

            if is_template is not None:
                query = query.where(Report.is_template == is_template)

            query = query.order_by(desc(Report.updated_at)).offset(skip).limit(limit)

            result = await db.execute(query)
            return result.scalars().all()
        except Exception as e:
            Logger.error(f"Error listing reports: {str(e)}")
            raise

    # Datasource methods
    @log_method_calls
    async def create_datasource(self, db: AsyncSession, datasource_data: ReportDatasourceCreate, user_id: UUID) -> ReportDatasource:
        """Create a report datasource"""
        try:
            # Verify user owns the report
            report_query = select(Report).where(
                and_(
                    Report.id == datasource_data.report_id,
                    Report.created_by == user_id,
                    Report.is_active == True
                )
            )
            report_result = await db.execute(report_query)
            report = report_result.scalar_one_or_none()

            if not report:
                raise ValueError("Report not found or access denied")

            db_datasource = ReportDatasource(**datasource_data.model_dump())
            db.add(db_datasource)
            await db.commit()
            await db.refresh(db_datasource)
            Logger.info(f"Created datasource {db_datasource.id} for report {datasource_data.report_id}")
            return db_datasource
        except Exception as e:
            Logger.error(f"Error creating datasource: {str(e)}")
            await db.rollback()
            raise

    @log_method_calls
    async def update_datasource(self, db: AsyncSession, datasource_id: UUID, datasource_data: ReportDatasourceUpdate, user_id: UUID) -> Optional[ReportDatasource]:
        """Update a report datasource"""
        try:
            query = (
                select(ReportDatasource)
                .join(Report)
                .where(
                    and_(
                        ReportDatasource.id == datasource_id,
                        Report.created_by == user_id,
                        Report.is_active == True
                    )
                )
            )
            result = await db.execute(query)
            datasource = result.scalar_one_or_none()

            if not datasource:
                return None

            update_data = datasource_data.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(datasource, field, value)

            await db.commit()
            await db.refresh(datasource)
            Logger.info(f"Updated datasource {datasource_id}")
            return datasource
        except Exception as e:
            Logger.error(f"Error updating datasource {datasource_id}: {str(e)}")
            await db.rollback()
            raise

    # Component methods
    @log_method_calls
    async def create_component(self, db: AsyncSession, component_data: ReportComponentCreate, user_id: UUID) -> ReportComponent:
        """Create a report component"""
        try:
            # Verify user owns the report
            report_query = select(Report).where(
                and_(
                    Report.id == component_data.report_id,
                    Report.created_by == user_id,
                    Report.is_active == True
                )
            )
            report_result = await db.execute(report_query)
            report = report_result.scalar_one_or_none()

            if not report:
                raise ValueError("Report not found or access denied")

            db_component = ReportComponent(**component_data.model_dump())
            db.add(db_component)
            await db.commit()
            await db.refresh(db_component)
            Logger.info(f"Created component {db_component.id} for report {component_data.report_id}")
            return db_component
        except Exception as e:
            Logger.error(f"Error creating component: {str(e)}")
            await db.rollback()
            raise

    @log_method_calls
    async def update_component(self, db: AsyncSession, component_id: UUID, component_data: ReportComponentUpdate, user_id: UUID) -> Optional[ReportComponent]:
        """Update a report component"""
        try:
            query = (
                select(ReportComponent)
                .join(Report)
                .where(
                    and_(
                        ReportComponent.id == component_id,
                        Report.created_by == user_id,
                        Report.is_active == True
                    )
                )
            )
            result = await db.execute(query)
            component = result.scalar_one_or_none()

            if not component:
                return None

            update_data = component_data.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(component, field, value)

            await db.commit()
            await db.refresh(component)
            Logger.info(f"Updated component {component_id}")
            return component
        except Exception as e:
            Logger.error(f"Error updating component {component_id}: {str(e)}")
            await db.rollback()
            raise

    # Template methods
    @log_method_calls
    async def create_template(self, db: AsyncSession, template_data: ReportTemplateCreate, user_id: UUID) -> ReportTemplate:
        """Create a report template"""
        try:
            db_template = ReportTemplate(
                **template_data.model_dump(),
                created_by=user_id
            )
            db.add(db_template)
            await db.commit()
            await db.refresh(db_template)
            Logger.info(f"Created template {db_template.id} by user {user_id}")
            return db_template
        except Exception as e:
            Logger.error(f"Error creating template: {str(e)}")
            await db.rollback()
            raise

    @log_method_calls
    async def list_templates(self, db: AsyncSession, skip: int = 0, limit: int = 100,
                           category: Optional[str] = None, ai_compatible: Optional[bool] = None) -> List[ReportTemplate]:
        """List available templates"""
        try:
            query = select(ReportTemplate).where(ReportTemplate.is_public == True)

            if category:
                query = query.where(ReportTemplate.category == category)

            if ai_compatible is not None:
                query = query.where(ReportTemplate.ai_compatible == ai_compatible)

            query = query.order_by(desc(ReportTemplate.rating), desc(ReportTemplate.usage_count)).offset(skip).limit(limit)

            result = await db.execute(query)
            return result.scalars().all()
        except Exception as e:
            Logger.error(f"Error listing templates: {str(e)}")
            raise

    @log_method_calls
    async def create_report_from_template(self, db: AsyncSession, template_id: UUID, report_name: str, user_id: UUID) -> Report:
        """Create a new report from a template"""
        try:
            # Get template
            template_query = select(ReportTemplate).where(ReportTemplate.id == template_id)
            template_result = await db.execute(template_query)
            template = template_result.scalar_one_or_none()

            if not template:
                raise ValueError("Template not found")

            # Extract report data from template config
            template_config = template.template_config

            # Create new report
            report_data = ReportCreate(
                name=report_name,
                description=f"Report created from template: {template.name}",
                report_type=ReportType.MANUAL,
                layout_config=template_config.get("layout_config", {}),
                page_settings=template_config.get("page_settings", {}),
                template_source_id=template_id
            )

            new_report = await self.create_report(db, report_data, user_id)

            # Increment template usage
            template.usage_count += 1
            await db.commit()

            Logger.info(f"Created report {new_report.id} from template {template_id}")
            return new_report
        except Exception as e:
            Logger.error(f"Error creating report from template {template_id}: {str(e)}")
            await db.rollback()
            raise