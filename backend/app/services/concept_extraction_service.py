"""
Concept Extraction Service

Extracts business concepts from natural language queries using NLP and pattern matching.
Identifies metrics, dimensions, time periods, aggregations, and other query components.
"""
from typing import List, Dict, Any, Optional, Set
import re
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.services.business_semantic_service import ConceptMappingService


class ConceptExtractionService:
    """Service for extracting business concepts from natural language"""

    # Common metric keywords
    METRIC_KEYWORDS = {
        'revenue', 'sales', 'profit', 'income', 'cost', 'expense', 'margin',
        'count', 'total', 'sum', 'average', 'mean', 'median', 'max', 'min',
        'growth', 'rate', 'percentage', 'ratio', 'share',
        'customers', 'orders', 'users', 'transactions', 'conversions',
        'clv', 'lifetime value', 'churn', 'retention', 'acquisition'
    }

    # Common dimension keywords
    DIMENSION_KEYWORDS = {
        'region', 'country', 'state', 'city', 'location', 'geography',
        'time', 'date', 'month', 'quarter', 'year', 'week', 'day',
        'category', 'product', 'service', 'type', 'segment',
        'channel', 'source', 'medium', 'campaign',
        'customer', 'user', 'account', 'company'
    }

    # Aggregation function keywords
    AGGREGATION_KEYWORDS = {
        'sum': ['sum', 'total', 'aggregate'],
        'avg': ['average', 'avg', 'mean'],
        'count': ['count', 'number of', 'how many'],
        'max': ['maximum', 'max', 'highest', 'largest', 'top'],
        'min': ['minimum', 'min', 'lowest', 'smallest', 'bottom'],
        'distinct': ['unique', 'distinct', 'different']
    }

    # Time period patterns
    TIME_PATTERNS = {
        'this_month': r'\b(this month|current month)\b',
        'last_month': r'\b(last month|previous month)\b',
        'this_quarter': r'\b(this quarter|current quarter|Q[1-4])\b',
        'last_quarter': r'\b(last quarter|previous quarter)\b',
        'this_year': r'\b(this year|current year|\d{4})\b',
        'last_year': r'\b(last year|previous year)\b',
        'ytd': r'\b(ytd|year to date|year-to-date)\b',
        'mtd': r'\b(mtd|month to date|month-to-date)\b',
        'last_7_days': r'\b(last 7 days|past week|last week)\b',
        'last_30_days': r'\b(last 30 days|past month)\b',
        'last_90_days': r'\b(last 90 days|past quarter)\b'
    }

    # Comparison patterns
    COMPARISON_PATTERNS = {
        'greater_than': r'\b(greater than|more than|above|over|exceeds|>)\b',
        'less_than': r'\b(less than|fewer than|below|under|<)\b',
        'equals': r'\b(equals|equal to|is|=)\b',
        'between': r'\b(between)\b',
        'top_n': r'\b(top \d+|highest \d+|largest \d+)\b',
        'bottom_n': r'\b(bottom \d+|lowest \d+|smallest \d+)\b'
    }

    @staticmethod
    async def extract_concepts(
        db: Session,
        db_alias: str,
        question: str
    ) -> Dict[str, Any]:
        """
        Extract all business concepts from a natural language question

        Returns:
        {
            'metrics': List[str],           # Detected metrics
            'dimensions': List[str],        # Detected dimensions
            'aggregations': List[str],      # Detected aggregation functions
            'time_periods': List[Dict],     # Detected time periods
            'comparisons': List[Dict],      # Detected comparison operators
            'filters': List[Dict],          # Detected filter conditions
            'limit': Optional[int],         # Detected result limit
            'order_by': Optional[str],      # Detected sort order
            'mapped_terms': Dict[str, str]  # Term mappings from concept_mappings
        }
        """
        question_lower = question.lower()

        return {
            'metrics': await ConceptExtractionService._extract_metrics(db, db_alias, question_lower),
            'dimensions': await ConceptExtractionService._extract_dimensions(db, db_alias, question_lower),
            'aggregations': ConceptExtractionService._extract_aggregations(question_lower),
            'time_periods': ConceptExtractionService._extract_time_periods(question_lower),
            'comparisons': ConceptExtractionService._extract_comparisons(question_lower),
            'filters': ConceptExtractionService._extract_filters(question_lower),
            'limit': ConceptExtractionService._extract_limit(question_lower),
            'order_by': ConceptExtractionService._extract_order(question_lower),
            'mapped_terms': await ConceptExtractionService._map_terms(db, db_alias, question_lower)
        }

    @staticmethod
    async def _extract_metrics(db: Session, db_alias: str, question: str) -> List[str]:
        """Extract metric names from question"""
        metrics = set()

        # Check for keyword matches
        for metric_keyword in ConceptExtractionService.METRIC_KEYWORDS:
            if metric_keyword in question:
                metrics.add(metric_keyword)

        # Check concept mappings for synonyms
        for term in question.split():
            mapping = await ConceptMappingService.get_mapping_by_term(db, db_alias, term)
            if mapping and mapping.metric_id:
                metrics.add(mapping.canonical_term)

        return list(metrics)

    @staticmethod
    async def _extract_dimensions(db: Session, db_alias: str, question: str) -> List[str]:
        """Extract dimension names from question"""
        dimensions = set()

        # Check for keyword matches
        for dim_keyword in ConceptExtractionService.DIMENSION_KEYWORDS:
            if dim_keyword in question:
                dimensions.add(dim_keyword)

        # Check for "by X" patterns
        by_pattern = r'\bby\s+(\w+)'
        by_matches = re.findall(by_pattern, question)
        dimensions.update(by_matches)

        # Check concept mappings for synonyms
        for term in question.split():
            mapping = await ConceptMappingService.get_mapping_by_term(db, db_alias, term)
            if mapping and mapping.entity_id:
                dimensions.add(mapping.canonical_term)

        return list(dimensions)

    @staticmethod
    def _extract_aggregations(question: str) -> List[str]:
        """Extract aggregation function types from question"""
        aggregations = set()

        for agg_type, keywords in ConceptExtractionService.AGGREGATION_KEYWORDS.items():
            for keyword in keywords:
                if keyword in question:
                    aggregations.add(agg_type)
                    break

        return list(aggregations)

    @staticmethod
    def _extract_time_periods(question: str) -> List[Dict[str, Any]]:
        """Extract time period specifications from question"""
        time_periods = []

        for period_type, pattern in ConceptExtractionService.TIME_PATTERNS.items():
            matches = re.findall(pattern, question, re.IGNORECASE)
            if matches:
                time_periods.append({
                    'type': period_type,
                    'matched_text': matches[0] if isinstance(matches[0], str) else matches[0][0],
                    'start_date': ConceptExtractionService._resolve_time_period(period_type)[0],
                    'end_date': ConceptExtractionService._resolve_time_period(period_type)[1]
                })

        # Extract specific dates
        date_patterns = [
            r'\b(\d{4}-\d{2}-\d{2})\b',  # YYYY-MM-DD
            r'\b(\d{2}/\d{2}/\d{4})\b',  # MM/DD/YYYY
            r'\b(\w+ \d{1,2}, \d{4})\b'  # Month DD, YYYY
        ]

        for pattern in date_patterns:
            matches = re.findall(pattern, question)
            for match in matches:
                time_periods.append({
                    'type': 'specific_date',
                    'matched_text': match,
                    'date': match
                })

        return time_periods

    @staticmethod
    def _resolve_time_period(period_type: str) -> tuple:
        """Resolve time period type to actual start and end dates"""
        today = datetime.now().date()

        if period_type == 'this_month':
            start = today.replace(day=1)
            end = today
        elif period_type == 'last_month':
            first_of_month = today.replace(day=1)
            end = first_of_month - timedelta(days=1)
            start = end.replace(day=1)
        elif period_type == 'this_year':
            start = today.replace(month=1, day=1)
            end = today
        elif period_type == 'last_year':
            start = today.replace(year=today.year - 1, month=1, day=1)
            end = today.replace(year=today.year - 1, month=12, day=31)
        elif period_type == 'ytd':
            start = today.replace(month=1, day=1)
            end = today
        elif period_type == 'mtd':
            start = today.replace(day=1)
            end = today
        elif period_type == 'last_7_days':
            start = today - timedelta(days=7)
            end = today
        elif period_type == 'last_30_days':
            start = today - timedelta(days=30)
            end = today
        elif period_type == 'last_90_days':
            start = today - timedelta(days=90)
            end = today
        else:
            start = None
            end = None

        return (start, end)

    @staticmethod
    def _extract_comparisons(question: str) -> List[Dict[str, Any]]:
        """Extract comparison operators and values from question"""
        comparisons = []

        for comp_type, pattern in ConceptExtractionService.COMPARISON_PATTERNS.items():
            matches = re.findall(pattern, question, re.IGNORECASE)
            if matches:
                # Try to extract numeric values near the comparison
                value_pattern = r'(\d+(?:\.\d+)?)'
                values = re.findall(value_pattern, question)

                comparisons.append({
                    'type': comp_type,
                    'matched_text': matches[0] if isinstance(matches[0], str) else matches[0][0],
                    'values': values
                })

        return comparisons

    @staticmethod
    def _extract_filters(question: str) -> List[Dict[str, Any]]:
        """Extract filter conditions from question"""
        filters = []

        # Extract "where X = Y" patterns
        where_pattern = r'\bwhere\s+(\w+)\s+(is|equals|=)\s+["\']?(\w+)["\']?'
        where_matches = re.findall(where_pattern, question, re.IGNORECASE)

        for match in where_matches:
            filters.append({
                'field': match[0],
                'operator': 'equals',
                'value': match[2]
            })

        # Extract "for X" patterns
        for_pattern = r'\bfor\s+["\']?([^"\']+)["\']?'
        for_matches = re.findall(for_pattern, question, re.IGNORECASE)

        for match in for_matches:
            filters.append({
                'context': 'for',
                'value': match
            })

        # Extract "in X" patterns
        in_pattern = r'\bin\s+["\']?([^"\']+)["\']?'
        in_matches = re.findall(in_pattern, question, re.IGNORECASE)

        for match in in_matches:
            filters.append({
                'operator': 'in',
                'value': match
            })

        return filters

    @staticmethod
    def _extract_limit(question: str) -> Optional[int]:
        """Extract result limit from question"""
        # Look for "top N", "first N", "limit N"
        limit_patterns = [
            r'\btop\s+(\d+)\b',
            r'\bfirst\s+(\d+)\b',
            r'\blimit\s+(\d+)\b',
            r'\b(\d+)\s+results?\b'
        ]

        for pattern in limit_patterns:
            match = re.search(pattern, question, re.IGNORECASE)
            if match:
                return int(match.group(1))

        return None

    @staticmethod
    def _extract_order(question: str) -> Optional[str]:
        """Extract sort order from question"""
        if re.search(r'\b(highest|largest|top|descending|desc)\b', question, re.IGNORECASE):
            return 'DESC'
        elif re.search(r'\b(lowest|smallest|bottom|ascending|asc)\b', question, re.IGNORECASE):
            return 'ASC'
        return None

    @staticmethod
    async def _map_terms(db: Session, db_alias: str, question: str) -> Dict[str, str]:
        """Map terms in question to canonical terms using concept mappings"""
        mapped_terms = {}

        # Split question into words
        words = re.findall(r'\b\w+\b', question)

        for word in words:
            mapping = await ConceptMappingService.get_mapping_by_term(db, db_alias, word)
            if mapping:
                mapped_terms[word] = mapping.canonical_term

        return mapped_terms

    @staticmethod
    async def normalize_question(
        db: Session,
        db_alias: str,
        question: str
    ) -> str:
        """
        Normalize question by replacing synonyms with canonical terms
        """
        mapped_terms = await ConceptExtractionService._map_terms(db, db_alias, question.lower())

        normalized = question
        for synonym, canonical in mapped_terms.items():
            # Replace whole words only
            normalized = re.sub(
                r'\b' + re.escape(synonym) + r'\b',
                canonical,
                normalized,
                flags=re.IGNORECASE
            )

        return normalized

    @staticmethod
    async def extract_query_intent(
        db: Session,
        db_alias: str,
        question: str
    ) -> Dict[str, Any]:
        """
        Determine the intent of the query (aggregation, trend, comparison, etc.)
        """
        question_lower = question.lower()

        intent = {
            'type': 'unknown',
            'confidence': 0.0,
            'details': {}
        }

        # Trend analysis intent
        if any(word in question_lower for word in ['trend', 'over time', 'growth', 'change', 'evolution']):
            intent['type'] = 'trend_analysis'
            intent['confidence'] = 0.9

        # Comparison intent
        elif any(word in question_lower for word in ['compare', 'vs', 'versus', 'difference between']):
            intent['type'] = 'comparison'
            intent['confidence'] = 0.85

        # Aggregation intent
        elif any(word in question_lower for word in ['total', 'sum', 'count', 'average', 'max', 'min']):
            intent['type'] = 'aggregation'
            intent['confidence'] = 0.8

        # Ranking intent
        elif any(word in question_lower for word in ['top', 'bottom', 'best', 'worst', 'rank']):
            intent['type'] = 'ranking'
            intent['confidence'] = 0.85

        # Filter/search intent
        elif any(word in question_lower for word in ['show', 'list', 'find', 'where', 'filter']):
            intent['type'] = 'filter'
            intent['confidence'] = 0.75

        # Distribution intent
        elif any(word in question_lower for word in ['distribution', 'breakdown', 'by']):
            intent['type'] = 'distribution'
            intent['confidence'] = 0.8

        return intent
