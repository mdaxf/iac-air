from typing import Optional, Dict, Any, List
import asyncio
from abc import ABC, abstractmethod
import openai
import anthropic
from app.core.config import settings


class LLMProvider(ABC):
    @abstractmethod
    async def generate_completion(self, prompt: str, max_tokens: int = 1000) -> str:
        pass


class OpenAIProvider(LLMProvider):
    def __init__(self, api_key: str, model: str = "gpt-4"):
        self.client = openai.AsyncOpenAI(api_key=api_key)
        self.model = model

    async def generate_completion(self, prompt: str, max_tokens: int = 1000) -> str:
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=0.1
        )
        return response.choices[0].message.content


class AnthropicProvider(LLMProvider):
    def __init__(self, api_key: str, model: str = "claude-3-sonnet-20240229"):
        self.client = anthropic.AsyncAnthropic(api_key=api_key)
        self.model = model

    async def generate_completion(self, prompt: str, max_tokens: int = 1000) -> str:
        response = await self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1
        )
        return response.content[0].text


class LLMService:
    def __init__(self, provider: Optional[LLMProvider] = None):
        if provider is None:
            # Default to OpenAI if available, then Anthropic
            if settings.OPENAI_API_KEY:
                provider = OpenAIProvider(api_key=settings.OPENAI_API_KEY)
            elif settings.ANTHROPIC_API_KEY:
                provider = AnthropicProvider(api_key=settings.ANTHROPIC_API_KEY)
            else:
                raise ValueError("No LLM provider configured. Please set OPENAI_API_KEY or ANTHROPIC_API_KEY.")

        self.provider = provider

    async def generate_sql(self, user_query: str, context: str, db_alias: str) -> Optional[str]:
        """Generate SQL query from natural language query with context"""
        prompt = self._build_sql_generation_prompt(user_query, context, db_alias)

        try:
            response = await self.provider.generate_completion(prompt, max_tokens=500)
            sql_query = self._extract_sql_from_response(response)
            return sql_query
        except Exception as e:
            print(f"Failed to generate SQL: {e}")
            return None

    async def generate_narrative(self, user_query: str, data: List[Dict], context: str) -> str:
        """Generate narrative explanation of query results"""
        prompt = self._build_narrative_prompt(user_query, data, context)

        try:
            response = await self.provider.generate_completion(prompt, max_tokens=300)
            return response.strip()
        except Exception as e:
            return f"Unable to generate narrative explanation: {str(e)}"

    async def modify_sql_for_drilldown(
        self,
        original_sql: str,
        original_query: str,
        filter_criteria: Dict[str, Any]
    ) -> Optional[str]:
        """Modify SQL query for drill-down analysis"""
        prompt = self._build_drilldown_prompt(original_sql, original_query, filter_criteria)

        try:
            response = await self.provider.generate_completion(prompt, max_tokens=400)
            modified_sql = self._extract_sql_from_response(response)
            return modified_sql
        except Exception as e:
            print(f"Failed to modify SQL for drill-down: {e}")
            return None

    async def generate_drilldown_narrative(
        self,
        original_query: str,
        filter_criteria: Dict[str, Any],
        data: List[Dict]
    ) -> str:
        """Generate narrative for drill-down results"""
        prompt = f"""
        Original query: {original_query}
        Drill-down filters: {filter_criteria}
        Results: {data[:5] if data else 'No results found'}

        Generate a concise narrative explaining the drill-down analysis results:
        """

        try:
            response = await self.provider.generate_completion(prompt, max_tokens=200)
            return response.strip()
        except Exception as e:
            return f"Drill-down analysis completed with {len(data)} results."

    async def generate_analysis(self, analysis_prompt: str) -> str:
        """Generate AI analysis for query intent and table identification"""
        try:
            response = await self.provider.generate_completion(analysis_prompt, max_tokens=400)
            return response.strip()
        except Exception as e:
            print(f"Failed to generate analysis: {e}")
            return f"Analysis error: {str(e)}"

    def _build_sql_generation_prompt(self, user_query: str, context: str, db_alias: str) -> str:
        """Build prompt for SQL generation"""
        return f"""
        You are a SQL expert. Generate a safe, read-only SQL query based on the user's natural language request.

        Database: {db_alias}
        User Query: {user_query}

        Available Tables and Columns:
        {context}

        Rules:
        1. Only use SELECT statements
        2. No DDL/DML operations (INSERT, UPDATE, DELETE, DROP, ALTER, CREATE)
        3. Use appropriate JOINs when needed
        4. Include reasonable LIMIT clauses for large result sets
        5. Use proper WHERE clauses for filtering
        6. Return only the SQL query, no explanations

        SQL Query:
        """

    def _build_narrative_prompt(self, user_query: str, data: List[Dict], context: str) -> str:
        """Build prompt for narrative generation"""
        data_summary = f"Found {len(data)} results" if data else "No results found"
        sample_data = data[:3] if data else []

        return f"""
        User asked: {user_query}
        Query results: {data_summary}
        Sample data: {sample_data}

        Generate a concise, business-friendly narrative explanation of these results.
        Focus on key insights and patterns. Keep it under 100 words.

        Narrative:
        """

    def _build_drilldown_prompt(
        self,
        original_sql: str,
        original_query: str,
        filter_criteria: Dict[str, Any]
    ) -> str:
        """Build prompt for drill-down SQL modification"""
        return f"""
        Modify the following SQL query to add drill-down filters:

        Original Query: {original_query}
        Original SQL: {original_sql}
        Additional Filters: {filter_criteria}

        Add the new filters to the WHERE clause while maintaining the original logic.
        Return only the modified SQL query.

        Modified SQL:
        """

    def _extract_sql_from_response(self, response: str) -> Optional[str]:
        """Extract SQL query from LLM response"""
        if not response:
            return None

        # Remove common prefixes and suffixes
        response = response.strip()

        # Look for SQL between code blocks
        if "```sql" in response:
            start = response.find("```sql") + 6
            end = response.find("```", start)
            if end > start:
                sql = response[start:end].strip()
                return sql

        if "```" in response:
            start = response.find("```") + 3
            end = response.find("```", start)
            if end > start:
                sql = response[start:end].strip()
                return sql

        # If no code blocks, try to find SQL keywords
        sql_keywords = ['SELECT', 'WITH', 'FROM']
        for keyword in sql_keywords:
            if keyword in response.upper():
                # Find the line containing the keyword and take from there
                lines = response.split('\n')
                for i, line in enumerate(lines):
                    if keyword in line.upper():
                        sql_lines = lines[i:]
                        sql = '\n'.join(sql_lines).strip()
                        # Remove any trailing explanations
                        if '\n\n' in sql:
                            sql = sql.split('\n\n')[0]
                        return sql

        return response.strip() if response.strip() else None