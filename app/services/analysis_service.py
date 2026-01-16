"""GPT-5 powered architectural analysis service."""

import json
from typing import Optional
from openai import OpenAI

from app.config import settings
from app.schemas import AnalysisResult


class AnalysisService:
    """Service for analyzing repository architecture using GPT-5."""

    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.OPENAI_MODEL

    def analyze_architecture(
        self,
        readme_content: str,
        repo_name: str,
        file_tree: Optional[list[str]] = None
    ) -> AnalysisResult:
        """
        Analyze repository architecture using GPT-5.
        
        Args:
            readme_content: README file content
            repo_name: Repository name for context
            file_tree: Optional list of file paths in the repo
            
        Returns:
            AnalysisResult with detected patterns and confidence scores
        """
        # Build context with file tree if available
        context = f"Repository: {repo_name}\n\n"
        
        if file_tree:
            context += "File Structure:\n"
            context += "\n".join(file_tree[:100])  # Limit to first 100 files
            context += "\n\n"
        
        context += f"README Content:\n{readme_content[:8000]}"  # Limit README size

        response = self.client.chat.completions.create(
            model=self.model,
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "system",
                    "content": """You are an expert software architect. Analyze repositories and return structured JSON.
Your task is to identify architectural patterns, design patterns, infrastructure approaches, and frameworks used.
Be specific and provide confidence scores between 0.0 and 1.0 based on evidence found."""
                },
                {
                    "role": "user",
                    "content": f"""Analyze this repository and identify:
- Architectural patterns (microservices, monolith, serverless, event-driven, hexagonal, clean architecture, etc.)
- Design patterns mentioned or evident (repository pattern, factory, singleton, observer, etc.)
- Infrastructure approach (containerized, cloud-native, kubernetes, serverless, etc.)
- Notable frameworks or libraries

Return JSON with this exact structure:
{{
    "architectural_patterns": [{{"name": "pattern name", "confidence": 0.0-1.0}}],
    "design_patterns": [{{"name": "pattern name", "confidence": 0.0-1.0}}],
    "infrastructure": [{{"approach": "approach name", "confidence": 0.0-1.0}}],
    "frameworks": ["framework1", "framework2"],
    "summary": "Brief 1-2 sentence summary of the architecture"
}}

{context}"""
                }
            ],
            max_tokens=1500,
            temperature=0.3
        )

        result_text = response.choices[0].message.content
        result_data = json.loads(result_text)
        
        return AnalysisResult(**result_data)

    def analyze_with_heuristics(self, file_tree: list[str]) -> dict:
        """
        Quick heuristic-based analysis from file structure.
        
        Args:
            file_tree: List of file paths
            
        Returns:
            Dictionary of detected patterns with confidence scores
        """
        patterns = {}
        file_set = set(f.lower() for f in file_tree)
        file_str = " ".join(file_tree).lower()

        # Microservices indicators
        if any(x in file_str for x in ["services/", "microservices/", "api-gateway"]):
            patterns["microservices"] = 0.7
        
        # Event-driven indicators
        if any(x in file_str for x in ["kafka", "rabbitmq", "event", "message", "queue"]):
            patterns["event-driven"] = 0.6
        
        # Containerization
        if "dockerfile" in file_set or "docker-compose.yml" in file_set:
            patterns["containerized"] = 0.9
        
        # Kubernetes
        if any("kubernetes" in f or "k8s" in f or "helm" in f for f in file_tree):
            patterns["kubernetes"] = 0.85
        
        # Clean/Hexagonal architecture
        if all(x in file_str for x in ["domain", "application", "infrastructure"]):
            patterns["clean-architecture"] = 0.7
        
        # Serverless
        if any(x in file_str for x in ["serverless", "lambda", "functions/"]):
            patterns["serverless"] = 0.75

        return patterns


# Singleton instance
analysis_service = AnalysisService()
