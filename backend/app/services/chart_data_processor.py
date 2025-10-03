"""
Enhanced Chart Data Processing Service inspired by DataEase
Implements a 4-stage data processing pipeline: Format → Filter → Calculate → Build
"""

from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import asyncio
import json
from datetime import datetime
import hashlib

from ..models.report import ReportComponent, ReportDatasource
from ..schemas.report import QueryResult, VisualQuery
from .database_service import DatabaseService


class DataProcessingContext:
    """Context object passed through the processing pipeline"""
    def __init__(self, user_id: str, report_id: str, component: ReportComponent):
        self.user_id = user_id
        self.report_id = report_id
        self.component = component
        self.permissions = []
        self.filters = []
        self.metadata = {}


class AxisFormatResult:
    """Result of axis formatting stage"""
    def __init__(self):
        self.dimensions = []
        self.measures = []
        self.time_fields = []
        self.calculated_fields = []
        self.field_mappings = {}


class FilterResult:
    """Result of filtering stage"""
    def __init__(self):
        self.where_conditions = []
        self.having_conditions = []
        self.parameter_bindings = {}
        self.applied_filters = []


class CalculationResult:
    """Result of calculation stage"""
    def __init__(self):
        self.raw_data = []
        self.total_rows = 0
        self.execution_time = 0
        self.cache_hit = False
        self.sql_query = ""


class ChartDataProcessor:
    """Main chart data processor implementing DataEase-inspired pipeline"""

    def __init__(self, db_service: DatabaseService):
        self.db_service = db_service
        self.cache = {}  # Simple in-memory cache (should use Redis in production)

    async def process_chart_data(
        self,
        component: ReportComponent,
        datasource: ReportDatasource,
        context: DataProcessingContext
    ) -> QueryResult:
        """
        Main entry point - processes chart data through 4-stage pipeline
        """
        try:
            # Stage 1: Format axis data and prepare dimensions/measures
            format_result = await self.format_axis(component, datasource, context)

            # Stage 2: Apply filters (dashboard + component + permission filters)
            filter_result = await self.apply_filters(component, format_result, context)

            # Stage 3: Execute SQL and get raw data
            calc_result = await self.calculate_data(component, datasource, filter_result, context)

            # Stage 4: Build final chart data structure
            chart_data = await self.build_chart_data(component, calc_result, context)

            return chart_data

        except Exception as e:
            raise Exception(f"Chart data processing failed: {str(e)}")

    async def format_axis(
        self,
        component: ReportComponent,
        datasource: ReportDatasource,
        context: DataProcessingContext
    ) -> AxisFormatResult:
        """
        Stage 1: Format axis data - dimension and measure processing
        Similar to DataEase's AxisFormatResult processing
        """
        result = AxisFormatResult()

        # Process data configuration
        data_config = component.data_config or {}
        fields = data_config.get('fields', [])

        for field in fields:
            field_info = {
                'name': field.get('field'),
                'alias': field.get('alias', field.get('field')),
                'type': field.get('type', 'string'),
                'aggregation': field.get('aggregation'),
                'format': field.get('format')
            }

            if field.get('type') == 'dimension':
                result.dimensions.append(field_info)
            elif field.get('type') == 'measure':
                result.measures.append(field_info)
            elif field.get('type') == 'time':
                result.time_fields.append(field_info)

        # Add field mappings for SQL generation
        for field_info in result.dimensions + result.measures + result.time_fields:
            result.field_mappings[field_info['alias']] = field_info

        return result

    async def apply_filters(
        self,
        component: ReportComponent,
        format_result: AxisFormatResult,
        context: DataProcessingContext
    ) -> FilterResult:
        """
        Stage 2: Apply filters - dashboard + component + permission filters
        Similar to DataEase's CustomFilterResult processing
        """
        result = FilterResult()

        # Component-level filters
        component_filters = component.data_config.get('filters', [])
        for filter_config in component_filters:
            condition = self._build_filter_condition(filter_config, format_result)
            if condition:
                result.where_conditions.append(condition)
                result.applied_filters.append(filter_config)

        # Dashboard-level filters (from context)
        dashboard_filters = context.filters
        for filter_config in dashboard_filters:
            condition = self._build_filter_condition(filter_config, format_result)
            if condition:
                result.where_conditions.append(condition)
                result.applied_filters.append(filter_config)

        # Permission-based filters (row-level security)
        permission_filters = await self._get_permission_filters(context)
        result.where_conditions.extend(permission_filters)

        return result

    async def calculate_data(
        self,
        component: ReportComponent,
        datasource: ReportDatasource,
        filter_result: FilterResult,
        context: DataProcessingContext
    ) -> CalculationResult:
        """
        Stage 3: Execute SQL and get data - optimized query execution
        Similar to DataEase's ChartCalcDataResult processing
        """
        result = CalculationResult()
        start_time = datetime.utcnow()

        # Generate cache key
        cache_key = self._generate_cache_key(component, datasource, filter_result)

        # Check cache first
        if cache_key in self.cache:
            cached_data = self.cache[cache_key]
            if datetime.utcnow().timestamp() - cached_data['timestamp'] < 300:  # 5 min cache
                result.raw_data = cached_data['data']
                result.total_rows = cached_data['total_rows']
                result.cache_hit = True
                result.sql_query = cached_data['sql_query']
                return result

        # Build SQL query
        sql_query = await self._build_sql_query(component, datasource, filter_result)
        result.sql_query = sql_query

        # Execute query
        try:
            query_result = await self.db_service.execute_query(
                datasource.database_alias,
                sql_query,
                filter_result.parameter_bindings
            )

            result.raw_data = query_result.data
            result.total_rows = len(query_result.data)

            # Cache result
            self.cache[cache_key] = {
                'data': result.raw_data,
                'total_rows': result.total_rows,
                'sql_query': sql_query,
                'timestamp': datetime.utcnow().timestamp()
            }

        except Exception as e:
            raise Exception(f"Query execution failed: {str(e)}")

        result.execution_time = (datetime.utcnow() - start_time).total_seconds()
        return result

    async def build_chart_data(
        self,
        component: ReportComponent,
        calc_result: CalculationResult,
        context: DataProcessingContext
    ) -> QueryResult:
        """
        Stage 4: Build final chart data - data transformation and chart building
        Similar to DataEase's final chart building
        """
        # Transform data based on chart type
        transformed_data = await self._transform_data_for_chart(
            calc_result.raw_data,
            component.chart_type,
            component.data_config
        )

        # Build chart metadata
        chart_meta = await self._build_chart_metadata(
            component,
            calc_result,
            context
        )

        return QueryResult(
            data=transformed_data,
            columns=[],  # Will be populated based on component configuration
            total_rows=calc_result.total_rows,
            execution_time=calc_result.execution_time,
            sql_query=calc_result.sql_query,
            cache_hit=calc_result.cache_hit,
            chart_meta=chart_meta
        )

    def _build_filter_condition(self, filter_config: Dict[str, Any], format_result: AxisFormatResult) -> Optional[str]:
        """Build SQL WHERE condition from filter configuration"""
        field_name = filter_config.get('field')
        operator = filter_config.get('operator')
        value = filter_config.get('value')

        if not all([field_name, operator, value is not None]):
            return None

        # Map field name through field mappings
        field_info = format_result.field_mappings.get(field_name)
        if not field_info:
            return None

        actual_field = field_info['name']

        # Build condition based on operator
        if operator == 'equals':
            return f"{actual_field} = '{value}'"
        elif operator == 'not_equals':
            return f"{actual_field} != '{value}'"
        elif operator == 'contains':
            return f"{actual_field} LIKE '%{value}%'"
        elif operator == 'starts_with':
            return f"{actual_field} LIKE '{value}%'"
        elif operator == 'ends_with':
            return f"{actual_field} LIKE '%{value}'"
        elif operator == 'greater_than':
            return f"{actual_field} > {value}"
        elif operator == 'less_than':
            return f"{actual_field} < {value}"
        elif operator == 'between':
            if isinstance(value, list) and len(value) == 2:
                return f"{actual_field} BETWEEN {value[0]} AND {value[1]}"
        elif operator == 'in':
            if isinstance(value, list):
                value_list = "', '".join(str(v) for v in value)
                return f"{actual_field} IN ('{value_list}')"

        return None

    async def _get_permission_filters(self, context: DataProcessingContext) -> List[str]:
        """Get permission-based filters for row-level security"""
        filters = []

        # Example: Add user-based filters
        # if context.user_id:
        #     filters.append(f"created_by = '{context.user_id}'")

        return filters

    def _generate_cache_key(self, component: ReportComponent, datasource: ReportDatasource, filter_result: FilterResult) -> str:
        """Generate cache key for query results"""
        key_data = {
            'component_id': component.id,
            'datasource_id': datasource.id,
            'data_config': component.data_config,
            'filters': filter_result.applied_filters
        }

        key_string = json.dumps(key_data, sort_keys=True, default=str)
        return hashlib.md5(key_string.encode()).hexdigest()

    async def _build_sql_query(
        self,
        component: ReportComponent,
        datasource: ReportDatasource,
        filter_result: FilterResult
    ) -> str:
        """Build SQL query from component configuration and filters"""
        # This is a simplified version - real implementation would be more sophisticated
        data_config = component.data_config or {}
        fields = data_config.get('fields', [])

        # Build SELECT clause
        select_fields = []
        for field in fields:
            field_name = field.get('field')
            alias = field.get('alias', field_name)
            aggregation = field.get('aggregation')

            if aggregation:
                select_fields.append(f"{aggregation}({field_name}) AS {alias}")
            else:
                select_fields.append(f"{field_name} AS {alias}")

        if not select_fields:
            select_fields = ['*']

        select_clause = 'SELECT ' + ', '.join(select_fields)

        # Build FROM clause
        from_clause = f"FROM {datasource.selected_tables[0]['name']}"

        # Build WHERE clause
        where_conditions = filter_result.where_conditions
        where_clause = ''
        if where_conditions:
            where_clause = 'WHERE ' + ' AND '.join(where_conditions)

        # Build GROUP BY clause
        group_by_fields = [f['field'] for f in fields if f.get('type') == 'dimension']
        group_by_clause = ''
        if group_by_fields:
            group_by_clause = 'GROUP BY ' + ', '.join(group_by_fields)

        # Build ORDER BY clause
        order_by_clause = 'ORDER BY 1'

        # Build LIMIT clause
        limit = data_config.get('limit', 1000)
        limit_clause = f'LIMIT {limit}'

        # Combine all clauses
        query_parts = [select_clause, from_clause]
        if where_clause:
            query_parts.append(where_clause)
        if group_by_clause:
            query_parts.append(group_by_clause)
        if order_by_clause:
            query_parts.append(order_by_clause)
        if limit_clause:
            query_parts.append(limit_clause)

        return ' '.join(query_parts)

    async def _transform_data_for_chart(
        self,
        raw_data: List[Dict[str, Any]],
        chart_type: str,
        data_config: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Transform raw data for specific chart types"""
        if not raw_data:
            return []

        # For now, return data as-is
        # Real implementation would transform based on chart type requirements
        return raw_data

    async def _build_chart_metadata(
        self,
        component: ReportComponent,
        calc_result: CalculationResult,
        context: DataProcessingContext
    ) -> Dict[str, Any]:
        """Build chart metadata for frontend rendering"""
        return {
            'chart_type': component.chart_type,
            'component_id': component.id,
            'total_rows': calc_result.total_rows,
            'execution_time': calc_result.execution_time,
            'cache_hit': calc_result.cache_hit,
            'generated_at': datetime.utcnow().isoformat()
        }