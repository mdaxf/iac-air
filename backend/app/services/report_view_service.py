"""
Report viewing service for executing reports with parameters and fetching data
"""

import re
import json
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.models.report import Report, ReportDatasource, ReportComponent
from app.models.report_parameter import ReportParameter, ReportParameterValue, ParameterType
from app.models.database import DatabaseConnection
from app.schemas.report_parameter import ReportViewRequest, ReportDataResponse
from app.services.database_service import DatabaseService


class ReportViewService:
    def __init__(self, db: Session):
        self.db = db
        self.database_service = DatabaseService()

    def execute_report(self, request: ReportViewRequest) -> ReportDataResponse:
        """
        Execute a report with given parameters and return the data
        """
        # Generate execution ID if not provided
        execution_id = request.execution_id or str(uuid.uuid4())
        start_time = datetime.utcnow()

        # Get report and validate
        report = self.db.query(Report).filter(Report.id == request.report_id).first()
        if not report:
            raise ValueError(f"Report with ID {request.report_id} not found")

        # Validate and store parameter values
        validated_parameters = self._validate_and_store_parameters(
            report, request.parameters, execution_id
        )

        # Execute datasources and collect data
        datasource_data = {}
        for datasource in report.datasources:
            try:
                data = self._execute_datasource(datasource, validated_parameters)
                datasource_data[datasource.alias] = data
            except Exception as e:
                datasource_data[datasource.alias] = {
                    "error": str(e),
                    "data": []
                }

        # Get component configurations for rendering
        components_data = self._get_components_for_rendering(report)

        execution_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)

        return ReportDataResponse(
            report_id=request.report_id,
            execution_id=execution_id,
            datasources=datasource_data,
            components=components_data,
            parameters=validated_parameters,
            execution_time_ms=execution_time,
            generated_at=datetime.utcnow()
        )

    def _validate_and_store_parameters(
        self, report: Report, parameters: Dict[str, Any], execution_id: str
    ) -> Dict[str, Any]:
        """
        Validate parameter values against report parameter definitions and store them
        """
        validated_params = {}

        # Get report parameter definitions
        report_params = {param.name: param for param in report.parameters}

        for param_name, param_value in parameters.items():
            if param_name in report_params:
                param_def = report_params[param_name]

                # Validate parameter value
                validated_value = self._validate_parameter_value(param_def, param_value)
                validated_params[param_name] = validated_value

                # Store parameter value for this execution
                param_value_record = ReportParameterValue(
                    parameter_id=param_def.id,
                    execution_id=execution_id,
                    value=json.dumps(validated_value) if validated_value is not None else None
                )
                self.db.add(param_value_record)

        # Check for required parameters
        for param in report.parameters:
            if param.is_required and param.name not in validated_params:
                if param.default_value:
                    # Use default value
                    default_val = json.loads(param.default_value) if param.default_value else None
                    validated_params[param.name] = default_val
                else:
                    raise ValueError(f"Required parameter '{param.name}' is missing")
            elif param.name not in validated_params and param.default_value:
                # Use default value for optional parameters
                default_val = json.loads(param.default_value) if param.default_value else None
                validated_params[param.name] = default_val

        self.db.commit()
        return validated_params

    def _validate_parameter_value(self, param_def: ReportParameter, value: Any) -> Any:
        """
        Validate a parameter value against its definition
        """
        if value is None:
            return None

        try:
            if param_def.parameter_type == ParameterType.TEXT:
                return str(value)
            elif param_def.parameter_type == ParameterType.NUMBER:
                return float(value)
            elif param_def.parameter_type == ParameterType.BOOLEAN:
                if isinstance(value, str):
                    return value.lower() in ('true', '1', 'yes', 'on')
                return bool(value)
            elif param_def.parameter_type in (ParameterType.DATE, ParameterType.DATETIME):
                # For dates, accept ISO format strings or datetime objects
                if isinstance(value, str):
                    return value  # Return as string, will be handled by database
                return str(value)
            elif param_def.parameter_type in (ParameterType.SELECT, ParameterType.MULTI_SELECT):
                # Validate against options if available
                if param_def.options:
                    valid_options = json.loads(param_def.options)
                    if param_def.parameter_type == ParameterType.SELECT:
                        if value not in valid_options:
                            raise ValueError(f"Invalid option '{value}' for parameter '{param_def.name}'")
                    else:  # MULTI_SELECT
                        if not isinstance(value, list):
                            value = [value]
                        for v in value:
                            if v not in valid_options:
                                raise ValueError(f"Invalid option '{v}' for parameter '{param_def.name}'")
                return value
            else:
                return value
        except (ValueError, TypeError) as e:
            raise ValueError(f"Invalid value for parameter '{param_def.name}': {str(e)}")

    def _execute_datasource(self, datasource: ReportDatasource, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a datasource query with parameter substitution
        """
        # Get database connection
        db_conn = self.db.query(DatabaseConnection).filter(
            DatabaseConnection.alias == datasource.database_alias
        ).first()

        if not db_conn:
            raise ValueError(f"Database connection '{datasource.database_alias}' not found")

        # Determine query to execute
        if datasource.query_type == "custom" and datasource.custom_sql:
            query = datasource.custom_sql
        else:
            # Build query from visual query builder data
            query = self._build_visual_query(datasource)

        # Substitute parameters in query
        final_query = self._substitute_parameters(query, parameters)

        # Execute query
        try:
            engine = self.database_service.get_sync_engine(db_conn)
            with engine.connect() as connection:
                result = connection.execute(text(final_query))

                # Convert result to list of dictionaries
                columns = result.keys()
                data = []
                for row in result:
                    data.append(dict(zip(columns, row)))

                return {
                    "data": data,
                    "columns": list(columns),
                    "query": final_query,
                    "row_count": len(data)
                }

        except Exception as e:
            raise Exception(f"Query execution failed: {str(e)}")

    def _validate_datasource(self, datasource: ReportDatasource) -> dict:
        """
        Validate datasource definition and return validation results
        """
        validation_errors = []
        warnings = []

        selected_tables = datasource.selected_tables or []
        selected_fields = datasource.selected_fields or []
        joins = datasource.joins or []

        # 1. Basic validation
        if not selected_tables:
            validation_errors.append("At least one table must be selected")
        if not selected_fields:
            validation_errors.append("At least one field must be selected")

        # 2. Main table identification
        main_table = None
        if selected_tables:
            # The first table in selected_tables should be the main table
            main_table = selected_tables[0]
            if isinstance(main_table, dict):
                main_table = main_table.get('name', '')

        # 3. Validate field-table relationships
        referenced_tables = set()
        invalid_fields = []

        for field in selected_fields:
            if isinstance(field, dict):
                table_name = field.get('table', '')
                field_name = field.get('field', '')
                if table_name:
                    referenced_tables.add(table_name)
                if not table_name or not field_name:
                    invalid_fields.append(field)
            elif isinstance(field, str):
                # Handle simple string field format like "table.field"
                if '.' in field:
                    table_name = field.split('.')[0]
                    referenced_tables.add(table_name)

        # 4. Check if all referenced tables are in selected_tables or have proper JOINs
        selected_table_names = set()
        for table in selected_tables:
            if isinstance(table, dict):
                name = table.get('name', '')
            else:
                name = str(table)
            if name:
                selected_table_names.add(name)

        # Tables that need JOINs
        tables_needing_joins = referenced_tables - selected_table_names

        # 5. Validate JOIN definitions (align with database metadata service)
        explicit_joined_tables = set()
        invalid_joins = []

        for join in joins:
            if isinstance(join, dict):
                # Support both formats: new structured format and legacy format
                if 'left_table' in join and 'right_table' in join:
                    # New structured format (align with QueryBuilderJoin)
                    left_table = join.get('left_table', '')
                    right_table = join.get('right_table', '')
                    left_field = join.get('left_field', '')
                    right_field = join.get('right_field', '')
                    join_type = join.get('join_type', 'INNER')

                    if right_table:
                        explicit_joined_tables.add(right_table)

                    if not left_table or not right_table or not left_field or not right_field:
                        invalid_joins.append(join)
                    elif join_type not in ['INNER', 'LEFT', 'RIGHT', 'FULL']:
                        warnings.append(f"Unusual JOIN type: {join_type}")
                else:
                    # Legacy format (table and condition)
                    table = join.get('table', '')
                    condition = join.get('condition', '')
                    join_type = join.get('type', 'INNER')

                    if isinstance(table, dict):
                        table_name = table.get('name', '')
                    else:
                        table_name = str(table)

                    if table_name:
                        explicit_joined_tables.add(table_name)

                    if not table_name or not condition:
                        invalid_joins.append(join)
                    elif join_type not in ['INNER', 'LEFT', 'RIGHT', 'FULL']:
                        warnings.append(f"Unusual JOIN type: {join_type}")

        # 6. Check for missing JOINs
        missing_joins = tables_needing_joins - explicit_joined_tables

        # 7. Validate database connection exists
        if datasource.database_alias:
            try:
                from app.models.database import DatabaseConnection
                db_conn = self.db.query(DatabaseConnection).filter(
                    DatabaseConnection.alias == datasource.database_alias
                ).first()
                if not db_conn:
                    validation_errors.append(f"Database connection '{datasource.database_alias}' not found")
            except Exception as e:
                warnings.append(f"Could not validate database connection: {str(e)}")

        # Add validation errors
        if invalid_fields:
            validation_errors.append(f"Invalid field definitions: {len(invalid_fields)} fields missing table or field name")
        if invalid_joins:
            validation_errors.append(f"Invalid JOIN definitions: {len(invalid_joins)} joins missing table or condition")
        if missing_joins:
            # Check if we're using structured joins - if so, be stricter about missing joins
            has_structured_joins = any(
                isinstance(join, dict) and 'left_table' in join and 'right_table' in join
                for join in joins
            )

            if has_structured_joins:
                # With structured joins, all missing joins should be explicitly defined
                validation_errors.append(f"Missing explicit JOINs for tables: {', '.join(missing_joins)}. Please define JOINs for all referenced tables.")
            elif len(missing_joins) <= 3:  # Only auto-join if reasonable number of tables
                warnings.append(f"Tables referenced in fields but not joined: {', '.join(missing_joins)}. Automatic JOINs will be generated.")
            else:
                validation_errors.append(f"Too many missing JOINs ({len(missing_joins)} tables). Please define explicit JOINs for: {', '.join(missing_joins)}")

        return {
            "is_valid": len(validation_errors) == 0,
            "errors": validation_errors,
            "warnings": warnings,
            "main_table": main_table,
            "referenced_tables": list(referenced_tables),
            "missing_joins": list(missing_joins),
            "explicit_joins": list(explicit_joined_tables)
        }

    def _build_visual_query(self, datasource: ReportDatasource) -> str:
        """
        Build SQL query from visual query builder data with proper validation
        """
        # Validate datasource first
        validation = self._validate_datasource(datasource)

        if not validation["is_valid"]:
            raise ValueError(f"Datasource validation failed: {'; '.join(validation['errors'])}")

        # Log warnings if any
        if validation["warnings"]:
            from app.core.logging_config import Logger
            Logger.warning(f"Datasource warnings: {'; '.join(validation['warnings'])}")

        selected_tables = datasource.selected_tables or []
        selected_fields = datasource.selected_fields or []
        joins = datasource.joins or []
        filters = datasource.filters or []
        sorting = datasource.sorting or []
        grouping = datasource.grouping or []

        # Build SELECT clause with aggregation support
        field_parts = []
        for field in selected_fields:
            if isinstance(field, dict):
                table_name = field.get('table', '')
                field_name = field.get('field', '')
                alias = field.get('alias', '')
                aggregation = field.get('aggregation', '')
                if table_name and field_name:
                    field_expr = f"{table_name}.{field_name}"
                    # Apply aggregation function if specified
                    if aggregation:
                        field_expr = f"{aggregation}({field_expr})"
                    if alias:
                        field_expr += f" AS {alias}"
                    field_parts.append(field_expr)
            else:
                field_parts.append(str(field))

        select_clause = "SELECT " + ", ".join(field_parts)

        # Build FROM clause using validated main table
        main_table = validation["main_table"]
        from_clause = f"FROM {main_table}" if main_table else "FROM"

        # Build JOIN clauses (align with database metadata service)
        join_clauses = []
        for join in joins:
            if isinstance(join, dict):
                # Support both formats: new structured format and legacy format
                if 'left_table' in join and 'right_table' in join:
                    # New structured format (align with QueryBuilderJoin)
                    left_table = join.get('left_table', '')
                    right_table = join.get('right_table', '')
                    left_field = join.get('left_field', '')
                    right_field = join.get('right_field', '')
                    join_type = join.get('join_type', 'INNER')

                    if left_table and right_table and left_field and right_field:
                        join_clause = f"{join_type} JOIN {right_table} ON {left_table}.{left_field} = {right_table}.{right_field}"
                        join_clauses.append(join_clause)
                else:
                    # Legacy format (table and condition)
                    join_type = join.get('type', 'INNER')
                    table = join.get('table', '')
                    condition = join.get('condition', '')

                    # Handle table as dictionary or string
                    if isinstance(table, dict):
                        table_name = table.get('name', '')
                    else:
                        table_name = str(table)

                    if table_name and condition:
                        join_clauses.append(f"{join_type} JOIN {table_name} ON {condition}")

        # Add automatic JOINs for tables referenced in fields but not in FROM or explicit JOINs
        explicit_joined_tables = set()
        for join_clause in join_clauses:
            # Extract table name from JOIN clause (basic parsing)
            if " JOIN " in join_clause:
                parts = join_clause.split(" JOIN ")
                if len(parts) > 1:
                    table_part = parts[1].split(" ON ")[0].strip()
                    explicit_joined_tables.add(table_part)

        # Tables that need automatic JOINs using the validated main table
        tables_needing_joins = set(validation["referenced_tables"]) - {validation["main_table"]} - explicit_joined_tables if validation["main_table"] else set()

        # Only add automatic JOINs if not using structured format and there are missing joins
        has_structured_joins = any(
            isinstance(join, dict) and 'left_table' in join and 'right_table' in join
            for join in joins
        )

        # Create automatic JOINs based on common patterns (only for legacy format)
        validated_main_table = validation["main_table"]
        if not has_structured_joins and tables_needing_joins:
            for table_to_join in tables_needing_joins:
                # Simple heuristic: try to join based on common foreign key patterns
                if validated_main_table and table_to_join:
                    # Remove schema prefix for pattern matching
                    main_table_simple = validated_main_table.split('.')[-1] if '.' in validated_main_table else validated_main_table
                    join_table_simple = table_to_join.split('.')[-1] if '.' in table_to_join else table_to_join

                    # Common patterns: join child tables to parent tables
                    if 'user' in main_table_simple.lower() and 'user' in join_table_simple.lower():
                        # Determine which is the parent (users) and which is the child (user_activities, user_sessions, etc.)
                        if main_table_simple.lower() == 'users' or main_table_simple.lower() == 'public.users':
                            # Main table is users, joining to user_activities/sessions
                            join_clauses.append(f"INNER JOIN {table_to_join} ON {validated_main_table}.id = {table_to_join}.user_id")
                        elif join_table_simple.lower() == 'users' or join_table_simple.lower() == 'public.users':
                            # Joining users table to user_activities/sessions main table
                            join_clauses.append(f"INNER JOIN {table_to_join} ON {table_to_join}.id = {validated_main_table}.user_id")
                        elif 'activities' in main_table_simple.lower() or 'sessions' in main_table_simple.lower():
                            # Main table is user_activities/sessions, need to join to users
                            join_clauses.append(f"INNER JOIN {table_to_join} ON {table_to_join}.id = {validated_main_table}.user_id")
                        elif 'activities' in join_table_simple.lower() or 'sessions' in join_table_simple.lower():
                            # Joining user_activities/sessions to users main table
                            join_clauses.append(f"INNER JOIN {table_to_join} ON {validated_main_table}.id = {table_to_join}.user_id")
                        else:
                            # Generic user table join - assume alphabetically first is parent
                            if main_table_simple.lower() < join_table_simple.lower():
                                join_clauses.append(f"INNER JOIN {table_to_join} ON {validated_main_table}.id = {table_to_join}.user_id")
                            else:
                                join_clauses.append(f"INNER JOIN {table_to_join} ON {table_to_join}.id = {validated_main_table}.user_id")
                    else:
                        # For non-user tables, use more generic pattern matching
                        # Try common foreign key patterns: table_id, table_name_id
                        table_id_field = f"{main_table_simple.lower()}_id"
                        join_table_id_field = f"{join_table_simple.lower()}_id"

                        # Check if the joining table likely has a foreign key to main table
                        join_clauses.append(f"INNER JOIN {table_to_join} ON {validated_main_table}.id = {table_to_join}.{table_id_field}")

        # Build WHERE clause
        where_conditions = []
        for filter_condition in filters:
            if isinstance(filter_condition, dict):
                condition = filter_condition.get('condition', '')
                if condition:
                    where_conditions.append(condition)
            else:
                where_conditions.append(str(filter_condition))

        where_clause = "WHERE " + " AND ".join(where_conditions) if where_conditions else ""

        # Build GROUP BY clause
        group_fields = []
        for group_field in grouping:
            if isinstance(group_field, dict):
                table_name = group_field.get('table', '')
                field_name = group_field.get('field', '')
                if table_name and field_name:
                    group_fields.append(f"{table_name}.{field_name}")
            else:
                group_fields.append(str(group_field))

        # Auto-add non-aggregated fields to GROUP BY when we have mixed aggregated/non-aggregated fields
        has_aggregated = any(isinstance(f, dict) and f.get('aggregation') for f in selected_fields)
        has_non_aggregated = any(isinstance(f, dict) and not f.get('aggregation') for f in selected_fields)

        if has_aggregated and has_non_aggregated:
            # Auto-add non-aggregated fields to GROUP BY
            for field in selected_fields:
                if isinstance(field, dict) and not field.get('aggregation'):  # Non-aggregated field
                    table_name = field.get('table', '')
                    field_name = field.get('field', '')
                    if table_name and field_name:
                        field_expr = f"{table_name}.{field_name}"
                        if field_expr not in group_fields:
                            group_fields.append(field_expr)

        group_clause = "GROUP BY " + ", ".join(group_fields) if group_fields else ""

        # Build ORDER BY clause
        order_fields = []
        for sort_field in sorting:
            if isinstance(sort_field, dict):
                table_name = sort_field.get('table', '')
                field_name = sort_field.get('field', '')
                direction = sort_field.get('direction', 'ASC')
                if table_name and field_name:
                    order_fields.append(f"{table_name}.{field_name} {direction}")
            else:
                order_fields.append(str(sort_field))

        order_clause = "ORDER BY " + ", ".join(order_fields) if order_fields else ""

        # Combine all parts
        query_parts = [select_clause, from_clause] + join_clauses
        if where_clause:
            query_parts.append(where_clause)
        if group_clause:
            query_parts.append(group_clause)
        if order_clause:
            query_parts.append(order_clause)

        # Add LIMIT clause for safety (unless custom SQL is being used)
        query_parts.append("LIMIT 1000")

        final_query = " ".join(query_parts)

        # Log the generated query for debugging
        from app.core.logging_config import Logger
        Logger.info(f"Generated SQL query: {final_query}")

        return final_query

    def _substitute_parameters(self, query: str, parameters: Dict[str, Any]) -> str:
        """
        Substitute @parameter_name placeholders in query with actual values
        """
        def replace_param(match):
            param_name = match.group(1)
            if param_name in parameters:
                param_value = parameters[param_name]

                # Handle different parameter types
                if param_value is None:
                    return "NULL"
                elif isinstance(param_value, str):
                    # Escape single quotes and wrap in quotes
                    escaped_value = param_value.replace("'", "''")
                    return f"'{escaped_value}'"
                elif isinstance(param_value, bool):
                    return "TRUE" if param_value else "FALSE"
                elif isinstance(param_value, (int, float)):
                    return str(param_value)
                elif isinstance(param_value, list):
                    # For multi-select parameters, create IN clause
                    escaped_values = []
                    for v in param_value:
                        if isinstance(v, str):
                            escaped_values.append(f"'{v.replace(chr(39), chr(39)+chr(39))}'")
                        else:
                            escaped_values.append(str(v))
                    return f"({', '.join(escaped_values)})"
                else:
                    return str(param_value)
            else:
                # Parameter not found, leave as is (might be handled by database)
                return match.group(0)

        # Find all @parameter_name patterns and replace them
        pattern = r'@(\w+)'
        result_query = re.sub(pattern, replace_param, query)

        return result_query

    def get_report_parameters(self, report_id: str) -> List[ReportParameter]:
        """
        Get all parameters for a report
        """
        return self.db.query(ReportParameter).filter(
            ReportParameter.report_id == report_id,
            ReportParameter.is_enabled == True
        ).order_by(ReportParameter.sort_order, ReportParameter.name).all()

    def validate_datasource_configuration(self, datasource: ReportDatasource) -> dict:
        """
        Validate a datasource configuration and return validation results
        This method can be used to validate datasources before saving
        """
        try:
            # Check if this is a custom SQL datasource
            if datasource.query_type == "custom" and datasource.custom_sql:
                # For custom SQL, just validate that the SQL is not empty
                return {
                    "is_valid": True,
                    "errors": [],
                    "warnings": [],
                    "main_table": None,
                    "referenced_tables": [],
                    "missing_joins": [],
                    "explicit_joins": [],
                    "sql_preview": datasource.custom_sql
                }

            # For visual queries, use the existing validation
            validation = self._validate_datasource(datasource)

            # Add SQL query preview if validation passes
            if validation["is_valid"]:
                try:
                    sql_query = self._build_visual_query(datasource)
                    validation["sql_preview"] = sql_query
                except Exception as e:
                    validation["warnings"].append(f"Could not generate SQL preview: {str(e)}")

            return validation
        except Exception as e:
            return {
                "is_valid": False,
                "errors": [f"Validation failed: {str(e)}"],
                "warnings": [],
                "main_table": None,
                "referenced_tables": [],
                "missing_joins": [],
                "explicit_joins": []
            }

    def test_datasource_execution(self, datasource: ReportDatasource, parameters: Dict[str, Any] = None) -> dict:
        """
        Test execute a datasource with validation and return results or errors
        This method can be used to test datasources before saving
        """
        try:
            # First validate the datasource
            validation = self.validate_datasource_configuration(datasource)

            if not validation["is_valid"]:
                return {
                    "success": False,
                    "validation": validation,
                    "error": "Datasource validation failed",
                    "data": None
                }

            # Try to execute with empty parameters if none provided
            test_parameters = parameters or {}

            # Execute the datasource
            result = self._execute_datasource(datasource, test_parameters)

            return {
                "success": True,
                "validation": validation,
                "data": result,
                "error": None
            }

        except Exception as e:
            return {
                "success": False,
                "validation": self._validate_datasource(datasource),
                "error": str(e),
                "data": None
            }

    def _get_components_for_rendering(self, report) -> List[Dict[str, Any]]:
        """
        Get component configurations optimized for frontend rendering
        """
        components_data = []

        for component in report.components:
            if not component.is_visible:
                continue

            component_data = {
                "id": str(component.id),
                "component_type": component.component_type.value if component.component_type else None,
                "name": component.name,
                "datasource_alias": component.datasource_alias,

                # Layout properties
                "x": component.x,
                "y": component.y,
                "width": component.width,
                "height": component.height,
                "z_index": component.z_index,

                # Component configurations
                "data_config": component.data_config or {},
                "component_config": component.component_config or {},
                "style_config": component.style_config or {},

                # Type-specific configurations
                "chart_type": component.chart_type.value if component.chart_type else None,
                "chart_config": component.chart_config or {},
                "barcode_type": component.barcode_type.value if component.barcode_type else None,
                "barcode_config": component.barcode_config or {},
                "drill_down_config": component.drill_down_config or {},
                "conditional_formatting": component.conditional_formatting or []
            }

            # For table components, ensure we include column configuration
            if component.component_type and component.component_type.value == "table":
                # Merge data_config with additional table-specific processing
                component_data = self._enhance_table_component_config(component_data, component)

            # For chart components, ensure we include chart-specific configuration
            elif component.component_type and component.component_type.value == "chart":
                # Merge chart_config with additional chart-specific processing
                component_data = self._enhance_chart_component_config(component_data, component)

            components_data.append(component_data)

        # Sort components by z_index for proper layering
        components_data.sort(key=lambda c: c.get("z_index", 0))

        return components_data

    def _enhance_table_component_config(self, component_data: Dict[str, Any], component) -> Dict[str, Any]:
        """
        Enhance table component configuration with proper column sequencing and display rules
        """
        data_config = component_data.get("data_config", {})

        # Check for both "columns" and "fields" configuration
        fields_config = data_config.get("fields", [])
        columns_config = data_config.get("columns", [])

        if fields_config:
            # Process fields configuration (this is the actual format used)
            normalized_columns = []

            for field in fields_config:
                if isinstance(field, dict):
                    # Convert field object to column configuration
                    field_name = field.get("field", "")
                    alias = field.get("alias", "")
                    aggregation = field.get("aggregation", "")

                    # Determine the actual column name in the data
                    if alias:
                        # Use alias (convert to lowercase to match data)
                        actual_column_name = alias.lower()
                    elif aggregation and field_name:
                        # For aggregated fields with no alias, construct from aggregation + field
                        field_base = field_name.split(".")[-1] if "." in field_name else field_name
                        actual_column_name = f"{aggregation.lower()}_{field_base}".lower()
                    else:
                        # For non-aggregated fields, use the field name
                        actual_column_name = field_name.split(".")[-1] if "." in field_name else field_name

                    # Create display name
                    if alias:
                        display_name = alias
                    elif aggregation:
                        display_name = f"{aggregation}({field_name.split('.')[-1]})"
                    else:
                        display_name = field_name.split(".")[-1] if "." in field_name else field_name

                    normalized_columns.append({
                        "field": actual_column_name,
                        "display_name": display_name,
                        "visible": True,
                        "width": "auto",
                        "align": "left",
                        "original_field": field
                    })

            component_data["data_config"]["columns"] = normalized_columns
            # Remove the needs_column_inference flag since we processed the fields
            component_data.pop("needs_column_inference", None)

        elif columns_config:
            # Process standard columns configuration
            normalized_columns = []

            for col in columns_config:
                if isinstance(col, str):
                    normalized_columns.append({
                        "field": col,
                        "display_name": col,
                        "visible": True,
                        "width": "auto",
                        "align": "left"
                    })
                elif isinstance(col, dict):
                    normalized_columns.append({
                        "field": col.get("field"),
                        "display_name": col.get("display_name") or col.get("field"),
                        "visible": col.get("visible", True),
                        "width": col.get("width", "auto"),
                        "align": col.get("align", "left"),
                        "format": col.get("format"),
                        "sort_order": col.get("sort_order")
                    })

            # Sort columns by sort_order if specified
            normalized_columns.sort(key=lambda c: c.get("sort_order", 999))
            component_data["data_config"]["columns"] = normalized_columns
            # Remove the needs_column_inference flag
            component_data.pop("needs_column_inference", None)

        else:
            # No column configuration found, mark for inference
            component_data["needs_column_inference"] = True

        return component_data

    def _enhance_chart_component_config(self, component_data: Dict[str, Any], component) -> Dict[str, Any]:
        """
        Enhance chart component configuration with proper chart rendering setup
        """
        chart_config = component_data.get("chart_config", {})
        data_config = component_data.get("data_config", {})

        # Process axis configuration from both chart_config and data_config
        x_axis_config = chart_config.get("xAxis", [])
        y_axis_config = chart_config.get("yAxis", [])

        # Extract field names for x and y axes
        x_field = None
        y_field = None

        if x_axis_config and isinstance(x_axis_config, list) and len(x_axis_config) > 0:
            x_axis_field = x_axis_config[0]
            if isinstance(x_axis_field, dict):
                x_field_name = x_axis_field.get("field", "")
                x_alias = x_axis_field.get("alias", "")
                x_aggregation = x_axis_field.get("aggregation", "")

                # Determine actual field name in data
                if x_alias:
                    x_field = x_alias.lower()
                elif x_aggregation and x_field_name:
                    field_base = x_field_name.split(".")[-1] if "." in x_field_name else x_field_name
                    x_field = f"{x_aggregation.lower()}_{field_base}".lower()
                else:
                    x_field = x_field_name.split(".")[-1] if "." in x_field_name else x_field_name

        if y_axis_config and isinstance(y_axis_config, list) and len(y_axis_config) > 0:
            y_axis_field = y_axis_config[0]
            if isinstance(y_axis_field, dict):
                y_field_name = y_axis_field.get("field", "")
                y_alias = y_axis_field.get("alias", "")
                y_aggregation = y_axis_field.get("aggregation", "")

                # Determine actual field name in data
                if y_alias:
                    y_field = y_alias.lower()
                elif y_aggregation and y_field_name:
                    field_base = y_field_name.split(".")[-1] if "." in y_field_name else y_field_name
                    y_field = f"{y_aggregation.lower()}_{field_base}".lower()
                else:
                    y_field = y_field_name.split(".")[-1] if "." in y_field_name else y_field_name

        # Update chart config with processed field names
        if x_field:
            chart_config["x_axis"] = x_field
        if y_field:
            chart_config["y_axis"] = y_field

        # Check if we have valid axis configuration
        if not x_field or not y_field:
            component_data["needs_axis_configuration"] = True
        else:
            # Remove the flag if we have valid configuration
            component_data.pop("needs_axis_configuration", None)

        # Ensure chart type is properly set
        if not component_data.get("chart_type"):
            # Default to bar chart if not specified
            component_data["chart_type"] = "bar"

        # Add default chart options if missing
        default_chart_config = {
            "legend": {
                "enabled": True,
                "position": "right"
            },
            "tooltip": {
                "enabled": True
            },
            "responsive": True,
            "animation": {
                "enabled": True,
                "duration": 300
            }
        }

        # Merge with existing config (existing config takes precedence)
        for key, value in default_chart_config.items():
            if key not in chart_config:
                chart_config[key] = value

        component_data["chart_config"] = chart_config

        return component_data