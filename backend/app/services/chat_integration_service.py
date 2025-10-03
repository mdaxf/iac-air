"""
Chat Integration Service

Integrates progressive retrieval and business semantic layer with chat service.
"""
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from app.services.progressive_retrieval_service import ProgressiveRetrievalService
from app.services.concept_extraction_service import ConceptExtractionService
from app.services.enhanced_vector_service import EnhancedVectorService


class ChatIntegrationService:
    """Service for integrating semantic layer with chat"""

    def __init__(self, embedding_service):
        self.embedding_service = embedding_service
        self.vector_service = EnhancedVectorService(embedding_service)

    async def enhance_chat_context(
        self,
        db: Session,
        db_alias: str,
        user_question: str,
        conversation_history: List[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Enhance chat context using progressive retrieval and semantic layer.

        Returns enriched context for LLM including:
        - Relevant tables (progressive retrieval)
        - Business entities and metrics
        - Query templates
        - Normalized question
        - Query intent
        """

        enhanced_context = {
            'original_question': user_question,
            'normalized_question': user_question,
            'query_intent': {},
            'extracted_concepts': {},
            'relevant_context': {},
            'sql_schema': '',
            'business_context': '',
            'suggested_templates': []
        }

        try:
            # Step 1: Extract concepts from question
            concepts = await ConceptExtractionService.extract_concepts(
                db, db_alias, user_question
            )
            enhanced_context['extracted_concepts'] = concepts

            # Step 2: Normalize question with concept mappings
            normalized = await ConceptExtractionService.normalize_question(
                db, db_alias, user_question
            )
            enhanced_context['normalized_question'] = normalized

            # Step 3: Detect query intent
            intent = await ConceptExtractionService.extract_query_intent(
                db, db_alias, user_question
            )
            enhanced_context['query_intent'] = intent

            # Step 4: Generate query embedding
            query_embedding = await self.embedding_service.generate_embedding(
                user_question
            )

            # Step 5: Progressive retrieval of relevant context
            relevant_context = await ProgressiveRetrievalService.retrieve_relevant_context(
                db=db,
                db_alias=db_alias,
                question=user_question,
                query_embedding=query_embedding,
                max_tables=10,
                similarity_threshold=0.7
            )
            enhanced_context['relevant_context'] = relevant_context

            # Step 6: Assemble SQL schema context
            sql_schema = await ProgressiveRetrievalService.assemble_sql_context(
                relevant_context
            )
            enhanced_context['sql_schema'] = sql_schema

            # Step 7: Build business context description
            business_context = await self._build_business_context(
                relevant_context
            )
            enhanced_context['business_context'] = business_context

            # Step 8: Find matching query templates
            templates = await self.vector_service.search_similar_templates(
                db, user_question, db_alias, limit=3
            )
            enhanced_context['suggested_templates'] = [
                {
                    'name': t.template_name,
                    'description': t.description,
                    'example_questions': t.example_questions
                }
                for t in templates
            ]

        except Exception as e:
            enhanced_context['error'] = str(e)

        return enhanced_context

    async def _build_business_context(
        self,
        relevant_context: Dict[str, Any]
    ) -> str:
        """Build human-readable business context"""

        context_parts = []

        # Add business entities
        entities = relevant_context.get('business_entities', [])
        if entities:
            context_parts.append("Relevant Business Entities:")
            for entity in entities[:3]:
                context_parts.append(f"- {entity.entity_name}: {entity.description or 'No description'}")

        # Add business metrics
        metrics = relevant_context.get('business_metrics', [])
        if metrics:
            context_parts.append("\nRelevant Business Metrics:")
            for metric in metrics[:3]:
                definition = metric.metric_definition or {}
                context_parts.append(
                    f"- {metric.metric_name}: {definition.get('description', 'No description')}"
                )

        # Add table information
        relevant_tables = relevant_context.get('relevant_tables', [])
        if relevant_tables:
            context_parts.append(f"\nRelevant Tables ({len(relevant_tables)} found):")
            for table_ctx in relevant_tables[:5]:
                table = table_ctx['table']
                score = table_ctx['relevance_score']
                context_parts.append(
                    f"- {table.schema_name}.{table.table_name} "
                    f"(relevance: {score:.2f}, {table_ctx['column_count']} columns)"
                )

        return "\n".join(context_parts)

    async def suggest_query_improvements(
        self,
        db: Session,
        db_alias: str,
        user_question: str,
        extracted_concepts: Dict[str, Any]
    ) -> List[str]:
        """Suggest improvements to user's question"""

        suggestions = []

        # Check if metrics are mentioned
        metrics = extracted_concepts.get('metrics', [])
        if not metrics:
            suggestions.append(
                "Tip: Specify what metric you want to calculate (e.g., 'total revenue', 'count of customers')"
            )

        # Check if dimensions are mentioned
        dimensions = extracted_concepts.get('dimensions', [])
        if not dimensions:
            suggestions.append(
                "Tip: Add a grouping dimension (e.g., 'by region', 'by month')"
            )

        # Check if time period is mentioned
        time_periods = extracted_concepts.get('time_periods', [])
        if not time_periods:
            suggestions.append(
                "Tip: Specify a time period (e.g., 'last month', 'this quarter', 'YTD')"
            )

        return suggestions

    async def generate_sql_with_context(
        self,
        db: Session,
        db_alias: str,
        user_question: str,
        enhanced_context: Dict[str, Any],
        llm_service
    ) -> Dict[str, Any]:
        """Generate SQL using enhanced context"""

        # Build prompt with enhanced context
        prompt_parts = [
            f"User Question: {user_question}",
            f"\nNormalized Question: {enhanced_context['normalized_question']}",
            f"\nQuery Intent: {enhanced_context['query_intent'].get('type', 'unknown')}",
            f"\n\nBusiness Context:\n{enhanced_context['business_context']}",
            f"\n\nDatabase Schema:\n{enhanced_context['sql_schema']}"
        ]

        # Add template suggestions if available
        templates = enhanced_context.get('suggested_templates', [])
        if templates:
            prompt_parts.append("\n\nSimilar Query Templates:")
            for template in templates:
                prompt_parts.append(f"- {template['name']}: {template['description']}")

        # Add concept hints
        concepts = enhanced_context.get('extracted_concepts', {})
        if concepts.get('metrics'):
            prompt_parts.append(f"\n\nDetected Metrics: {', '.join(concepts['metrics'])}")
        if concepts.get('dimensions'):
            prompt_parts.append(f"Detected Dimensions: {', '.join(concepts['dimensions'])}")
        if concepts.get('time_periods'):
            prompt_parts.append(f"Time Period: {concepts['time_periods'][0].get('matched_text', '')}")

        prompt_parts.append("\n\nGenerate SQL query:")

        full_prompt = "\n".join(prompt_parts)

        # Generate SQL using LLM (placeholder - would integrate with actual LLM service)
        result = {
            'sql': '',  # Generated SQL
            'explanation': '',  # How the query works
            'confidence': 0.0,  # Confidence score
            'used_tables': [],  # Tables used
            'used_templates': [],  # Templates matched
            'prompt': full_prompt
        }

        return result
