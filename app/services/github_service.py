"""GitHub API integration service."""

import base64
from typing import Optional
from github import Github, GithubException
from github.Repository import Repository as GithubRepo

from app.config import settings


class GitHubService:
    """Service for interacting with GitHub API."""

    def __init__(self, token: Optional[str] = None):
        self.token = token or settings.GITHUB_TOKEN
        self.client = Github(self.token) if self.token else Github()

    def search_repositories(
        self,
        language: Optional[str] = None,
        min_stars: int = 100,
        max_results: int = 50,
        query: Optional[str] = None
    ) -> list[dict]:
        """
        Search GitHub repositories by language and criteria.
        
        Args:
            language: Programming language filter
            min_stars: Minimum star count
            max_results: Maximum number of results to return
            query: Additional search terms
            
        Returns:
            List of repository metadata dictionaries
        """
        # Build search query
        search_parts = []
        
        if query:
            search_parts.append(query)
        
        if language:
            search_parts.append(f"language:{language}")
        
        search_parts.append(f"stars:>={min_stars}")
        
        search_query = " ".join(search_parts)
        
        results = []
        try:
            repos = self.client.search_repositories(
                query=search_query,
                sort="stars",
                order="desc"
            )
            
            # Safely iterate without slicing (PyGithub PaginatedList quirk)
            count = 0
            for repo in repos:
                if count >= max_results:
                    break
                results.append(self._repo_to_dict(repo))
                count += 1
                
        except GithubException as e:
            print(f"GitHub API error: {e}")
        except (IndexError, StopIteration):
            # Handle empty results gracefully
            pass
            
        return results

    def get_repository(self, full_name: str) -> Optional[dict]:
        """
        Get a single repository by full name (owner/repo).
        
        Args:
            full_name: Repository full name like 'facebook/react'
            
        Returns:
            Repository metadata dictionary or None
        """
        try:
            repo = self.client.get_repo(full_name)
            return self._repo_to_dict(repo)
        except GithubException as e:
            print(f"Error fetching repo {full_name}: {e}")
            return None

    def get_readme_content(self, full_name: str) -> Optional[str]:
        """
        Fetch README content for a repository.
        
        Args:
            full_name: Repository full name like 'facebook/react'
            
        Returns:
            README content as string or None
        """
        try:
            repo = self.client.get_repo(full_name)
            readme = repo.get_readme()
            content = base64.b64decode(readme.content).decode('utf-8')
            return content
        except GithubException:
            return None

    def get_file_tree(self, full_name: str, path: str = "", depth: int = 2) -> list[str]:
        """
        Get directory structure of a repository.
        
        Args:
            full_name: Repository full name
            path: Starting path (empty for root)
            depth: How deep to traverse
            
        Returns:
            List of file/folder paths
        """
        try:
            repo = self.client.get_repo(full_name)
            contents = repo.get_contents(path)
            
            paths = []
            for content in contents:
                paths.append(content.path)
                if content.type == "dir" and depth > 0:
                    paths.extend(self.get_file_tree(full_name, content.path, depth - 1))
            
            return paths
        except GithubException:
            return []

    def _repo_to_dict(self, repo: GithubRepo) -> dict:
        """Convert GitHub repo object to dictionary."""
        return {
            "name": repo.name,
            "full_name": repo.full_name,
            "url": repo.html_url,
            "language": repo.language,
            "stars": repo.stargazers_count,
            "description": repo.description or "",
        }


# Singleton instance
github_service = GitHubService()
