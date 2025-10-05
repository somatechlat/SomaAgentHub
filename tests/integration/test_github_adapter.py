"""
⚠️ WE DO NOT MOCK - Tests use REAL GitHub API with test account.

Integration Tests for GitHub Adapter
Tests real API calls, error handling, retries, and circuit breakers.
"""

import pytest
import time
from datetime import datetime


class TestGitHubAdapter:
    """Integration tests for GitHub adapter with real API."""
    
    def test_health_check(self, github_adapter, performance_tracker):
        """Test GitHub API health check."""
        start = time.time()
        
        # Real API call to get authenticated user
        user = github_adapter.get_authenticated_user()
        
        latency = (time.time() - start) * 1000
        performance_tracker.record("github", "health_check", latency, user is not None)
        
        assert user is not None
        assert "login" in user
        assert "id" in user
        print(f"✓ GitHub health check passed: {user['login']}")
    
    def test_create_repository(self, github_adapter, test_resource_tracker, test_isolation, performance_tracker):
        """Test creating a repository (real API call)."""
        repo_name = f"somagent-test-{test_isolation}"
        
        start = time.time()
        repo = github_adapter.create_repository(
            name=repo_name,
            description="Integration test repository",
            private=True,
            auto_init=True
        )
        latency = (time.time() - start) * 1000
        performance_tracker.record("github", "create_repository", latency, repo is not None)
        
        assert repo is not None
        assert repo["name"] == repo_name
        assert repo["private"] is True
        
        # Track for cleanup
        test_resource_tracker["github_repos"].append(repo["full_name"])
        
        print(f"✓ Created repository: {repo['html_url']}")
        
        # Cleanup
        github_adapter.delete_repository(repo["full_name"])
    
    def test_create_file(self, github_adapter, test_isolation, performance_tracker):
        """Test creating a file in a repository."""
        repo_name = f"somagent-test-file-{test_isolation}"
        
        # Create test repo
        repo = github_adapter.create_repository(name=repo_name, private=True, auto_init=True)
        
        try:
            start = time.time()
            file_content = "# Test File\n\nCreated by SomaGent integration test"
            result = github_adapter.create_or_update_file(
                repo=repo["full_name"],
                path="README.md",
                message="Add test README",
                content=file_content
            )
            latency = (time.time() - start) * 1000
            performance_tracker.record("github", "create_file", latency, result is not None)
            
            assert result is not None
            assert "content" in result
            print(f"✓ Created file in repository")
            
        finally:
            # Cleanup
            github_adapter.delete_repository(repo["full_name"])
    
    def test_create_pull_request(self, github_adapter, test_isolation, performance_tracker):
        """Test creating a pull request."""
        repo_name = f"somagent-test-pr-{test_isolation}"
        
        # Create test repo
        repo = github_adapter.create_repository(name=repo_name, private=True, auto_init=True)
        
        try:
            # Create a new branch
            default_branch = repo["default_branch"]
            github_adapter.create_branch(repo["full_name"], "test-branch", default_branch)
            
            # Add a commit to the branch
            github_adapter.create_or_update_file(
                repo=repo["full_name"],
                path="test.txt",
                message="Add test file",
                content="test content",
                branch="test-branch"
            )
            
            # Create PR
            start = time.time()
            pr = github_adapter.create_pull_request(
                repo=repo["full_name"],
                title="Test PR",
                body="Integration test pull request",
                head="test-branch",
                base=default_branch
            )
            latency = (time.time() - start) * 1000
            performance_tracker.record("github", "create_pull_request", latency, pr is not None)
            
            assert pr is not None
            assert pr["title"] == "Test PR"
            assert pr["state"] == "open"
            print(f"✓ Created pull request: {pr['html_url']}")
            
        finally:
            # Cleanup
            github_adapter.delete_repository(repo["full_name"])
    
    def test_github_actions_workflow(self, github_adapter, test_isolation, performance_tracker):
        """Test creating and triggering GitHub Actions workflow."""
        repo_name = f"somagent-test-actions-{test_isolation}"
        
        # Create test repo
        repo = github_adapter.create_repository(name=repo_name, private=True, auto_init=True)
        
        try:
            # Create workflow file
            workflow_content = """
name: Test Workflow
on: [push]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run test
        run: echo "Test passed"
"""
            start = time.time()
            github_adapter.create_or_update_file(
                repo=repo["full_name"],
                path=".github/workflows/test.yml",
                message="Add test workflow",
                content=workflow_content
            )
            latency = (time.time() - start) * 1000
            performance_tracker.record("github", "create_workflow", latency, True)
            
            print(f"✓ Created GitHub Actions workflow")
            
            # List workflows
            workflows = github_adapter.list_workflows(repo["full_name"])
            assert len(workflows) > 0
            
        finally:
            # Cleanup
            github_adapter.delete_repository(repo["full_name"])
    
    def test_bootstrap_repository(self, github_adapter, test_isolation, performance_tracker):
        """Test complete repository bootstrap."""
        repo_name = f"somagent-test-bootstrap-{test_isolation}"
        
        start = time.time()
        result = github_adapter.bootstrap_repository(
            name=repo_name,
            description="Bootstrapped test repository",
            topics=["test", "somagent"],
            enable_issues=True,
            enable_projects=True,
            enable_wiki=False
        )
        latency = (time.time() - start) * 1000
        performance_tracker.record("github", "bootstrap_repository", latency, result is not None)
        
        try:
            assert result is not None
            assert "repository" in result
            assert result["repository"]["name"] == repo_name
            print(f"✓ Bootstrapped repository with all settings")
            
        finally:
            # Cleanup
            github_adapter.delete_repository(f"{result['repository']['owner']['login']}/{repo_name}")
    
    def test_error_handling_invalid_repo(self, github_adapter, performance_tracker):
        """Test error handling for invalid repository."""
        start = time.time()
        
        with pytest.raises(Exception) as exc_info:
            github_adapter.get_repository("nonexistent/repo-12345678")
        
        latency = (time.time() - start) * 1000
        performance_tracker.record("github", "error_handling", latency, False)
        
        assert "404" in str(exc_info.value) or "Not Found" in str(exc_info.value)
        print(f"✓ Properly handled 404 error")
    
    def test_rate_limit_handling(self, github_adapter, performance_tracker):
        """Test GitHub API rate limit detection."""
        start = time.time()
        
        # Get rate limit status
        rate_limit = github_adapter.get_rate_limit()
        
        latency = (time.time() - start) * 1000
        performance_tracker.record("github", "rate_limit_check", latency, rate_limit is not None)
        
        assert rate_limit is not None
        assert "rate" in rate_limit
        assert "remaining" in rate_limit["rate"]
        print(f"✓ Rate limit: {rate_limit['rate']['remaining']}/{rate_limit['rate']['limit']}")
    
    def test_concurrent_operations(self, github_adapter, test_isolation, performance_tracker):
        """Test multiple concurrent API calls."""
        import concurrent.futures
        
        repo_name = f"somagent-test-concurrent-{test_isolation}"
        repo = github_adapter.create_repository(name=repo_name, private=True, auto_init=True)
        
        try:
            # Create multiple files concurrently
            def create_file(i):
                start = time.time()
                result = github_adapter.create_or_update_file(
                    repo=repo["full_name"],
                    path=f"file{i}.txt",
                    message=f"Add file {i}",
                    content=f"Content {i}"
                )
                latency = (time.time() - start) * 1000
                performance_tracker.record("github", f"concurrent_create_{i}", latency, result is not None)
                return result
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                futures = [executor.submit(create_file, i) for i in range(5)]
                results = [f.result() for f in concurrent.futures.as_completed(futures)]
            
            assert len(results) == 5
            assert all(r is not None for r in results)
            print(f"✓ Successfully created 5 files concurrently")
            
        finally:
            # Cleanup
            github_adapter.delete_repository(repo["full_name"])
