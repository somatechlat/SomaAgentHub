        """
        ⚠️ WE DO NOT MOCK - Real GitHub API adapter.

        Provides comprehensive GitHub integration:
            - Repository management
            - Issues and pull requests
            - Actions workflows
            - Project boards
            - Team management
            """

            import base64
            import logging
            from typing import Any

            import requests
            from services.common.config.base_settings import resolve_env

            logger = logging.getLogger(__name__)


            class GitHubAdapter:
            """
            Adapter for GitHub API.

            API Documentation: https://docs.github.com/en/rest
            """

            def __init__(self, access_token: str, base_url: str = "https://api.github.com"):
                self.access_token = access_token
                self.base_url = base_url
                self.headers = {
                "Authorization": f"token {access_token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
                }

                def _request(self, method: str, endpoint: str, **kwargs) -> Any:
                    """Make authenticated API request."""
                    url = f"{self.base_url}/{endpoint}"

                    response = requests.request(
                    method=method, url=url, headers=self.headers, timeout=30, **kwargs
                    )

                    response.raise_for_status()
                    return response.json() if response.content else {}

                    pository Management

                    def create_repository(
                    self,
                    name: str,
                    description: str = "",
                    private: bool = True,
                    auto_init: bool = True,
                    gitignore_template: str | None = None,
                    license_template: str | None = None,
                    ) -> dict[str, Any]:
                        """
                        Create a new repository.

                        Args:
                            name: Repository name
                            description: Repository description
                            private: Whether repository is private
                            auto_init: Initialize with README
                            gitignore_template: .gitignore template (e.g., 'Python')
                            license_template: License template (e.g., 'mit')

                            Returns:
                                Created repository data
                                """
                                logger.info(f"Creating GitHub repository: {name}")

                                data = {
                                "name": name,
                                "description": description,
                                "private": private,
                                "auto_init": auto_init,
                                }

                                if gitignore_template:
                                    data["gitignore_template"] = gitignore_template
                                    if license_template:
                                        data["license_template"] = license_template

                                        return self._request("POST", "user/repos", json=data)

                                        def get_repository(self, owner: str, repo: str) -> dict[str, Any]:
                                            """Get repository details."""
                                            return self._request("GET", f"repos/{owner}/{repo}")

                                            def list_repositories(self, visibility: str = "all") -> list[dict[str, Any]]:
                                                """
                                                List user repositories.

                                                Args:
                                                    visibility: Filter by visibility (all, public, private)
                                                    """
                                                    return self._request("GET", "user/repos", params={"visibility": visibility})

                                                    def delete_repository(self, owner: str, repo: str) -> None:
                                                        """Delete a repository."""
                                                        logger.warning(f"Deleting repository: {owner}/{repo}")
                                                        self._request("DELETE", f"repos/{owner}/{repo}")

                                                        le Operations

                                                        def create_file(
                                                        self,
                                                        owner: str,
                                                        repo: str,
                                                        path: str,
                                                        content: str,
                                                        message: str,
                                                        branch: str = "main",
                                                        ) -> dict[str, Any]:
                                                            """
                                                            Create a new file in repository.

                                                            Args:
                                                                owner: Repository owner
                                                                repo: Repository name
                                                                path: File path
                                                                content: File content (will be base64 encoded)
                                                                message: Commit message
                                                                branch: Branch name

                                                                Returns:
                                                                    Commit data
                                                                    """
                                                                    logger.info(f"Creating file: {path}")

                                                                    content_encoded = base64.b64encode(content.encode()).decode()

                                                                    data = {
                                                                    "message": message,
                                                                    "content": content_encoded,
                                                                    "branch": branch,
                                                                    }

                                                                    return self._request("PUT", f"repos/{owner}/{repo}/contents/{path}", json=data)

                                                                    def update_file(
                                                                    self,
                                                                    owner: str,
                                                                    repo: str,
                                                                    path: str,
                                                                    content: str,
                                                                    message: str,
                                                                    sha: str,
                                                                    branch: str = "main",
                                                                    ) -> dict[str, Any]:
                                                                        """Update an existing file."""
                                                                        content_encoded = base64.b64encode(content.encode()).decode()

                                                                        data = {
                                                                        "message": message,
                                                                        "content": content_encoded,
                                                                        "sha": sha,
                                                                        "branch": branch,
                                                                        }

                                                                        return self._request("PUT", f"repos/{owner}/{repo}/contents/{path}", json=data)

                                                                        def get_file_content(self, owner: str, repo: str, path: str) -> dict[str, Any]:
                                                                            """Get file content."""
                                                                            return self._request("GET", f"repos/{owner}/{repo}/contents/{path}")

                                                                            sue Management

                                                                            def create_issue(
                                                                            self,
                                                                            owner: str,
                                                                            repo: str,
                                                                            title: str,
                                                                            body: str = "",
                                                                            assignees: list[str] | None = None,
                                                                            labels: list[str] | None = None,
                                                                            milestone: int | None = None,
                                                                            ) -> dict[str, Any]:
                                                                                """Create a new issue."""
                                                                                logger.info(f"Creating issue: {title}")

                                                                                data = {
                                                                                "title": title,
                                                                                "body": body,
                                                                                }

                                                                                if assignees:
                                                                                    data["assignees"] = assignees
                                                                                    if labels:
                                                                                        data["labels"] = labels
                                                                                        if milestone:
                                                                                            data["milestone"] = milestone

                                                                                            return self._request("POST", f"repos/{owner}/{repo}/issues", json=data)

                                                                                            def update_issue(
                                                                                            self, owner: str, repo: str, issue_number: int, **kwargs
                                                                                            ) -> dict[str, Any]:
                                                                                                """Update an issue."""
                                                                                                return self._request(
                                                                                                "PATCH", f"repos/{owner}/{repo}/issues/{issue_number}", json=kwargs
                                                                                                )

                                                                                                def list_issues(
                                                                                                self,
                                                                                                owner: str,
                                                                                                repo: str,
                                                                                                state: str = "open",
                                                                                                labels: str | None = None,
                                                                                                assignee: str | None = None,
                                                                                                ) -> list[dict[str, Any]]:
                                                                                                    """List repository issues."""
                                                                                                    params = {"state": state}
                                                                                                    if labels:
                                                                                                        params["labels"] = labels
                                                                                                        if assignee:
                                                                                                            params["assignee"] = assignee

                                                                                                            return self._request("GET", f"repos/{owner}/{repo}/issues", params=params)

                                                                                                            ll Request Management

                                                                                                            def create_pull_request(
                                                                                                            self,
                                                                                                            owner: str,
                                                                                                            repo: str,
                                                                                                            title: str,
                                                                                                            head: str,
                                                                                                            base: str = "main",
                                                                                                            body: str = "",
                                                                                                            draft: bool = False,
                                                                                                            ) -> dict[str, Any]:
                                                                                                                """
                                                                                                                Create a pull request.

                                                                                                                Args:
                                                                                                                    owner: Repository owner
                                                                                                                    repo: Repository name
                                                                                                                    title: PR title
                                                                                                                    head: Branch containing changes
                                                                                                                    base: Branch to merge into
                                                                                                                    body: PR description
                                                                                                                    draft: Create as draft PR
                                                                                                                    """
                                                                                                                    logger.info(f"Creating PR: {title}")

                                                                                                                    data = {
                                                                                                                    "title": title,
                                                                                                                    "head": head,
                                                                                                                    "base": base,
                                                                                                                    "body": body,
                                                                                                                    "draft": draft,
                                                                                                                    }

                                                                                                                    return self._request("POST", f"repos/{owner}/{repo}/pulls", json=data)

                                                                                                                    def merge_pull_request(
                                                                                                                    self,
                                                                                                                    owner: str,
                                                                                                                    repo: str,
                                                                                                                    pull_number: int,
                                                                                                                    merge_method: str = "merge",  # merge, squash, rebase
                                                                                                                    ) -> dict[str, Any]:
                                                                                                                        """Merge a pull request."""
                                                                                                                        logger.info(f"Merging PR #{pull_number}")

                                                                                                                        data = {"merge_method": merge_method}

                                                                                                                        return self._request(
                                                                                                                        "PUT", f"repos/{owner}/{repo}/pulls/{pull_number}/merge", json=data
                                                                                                                        )

                                                                                                                        anch Management

                                                                                                                        def create_branch(
                                                                                                                        self, owner: str, repo: str, branch: str, from_branch: str = "main"
                                                                                                                        ) -> dict[str, Any]:
                                                                                                                            """Create a new branch from existing branch."""
                                                                                                                            logger.info(f"Creating branch: {branch}")

                                                                                                                            t SHA of from_branch
                                                                                                                            ref_data = self._request(
                                                                                                                            "GET", f"repos/{owner}/{repo}/git/ref/heads/{from_branch}"
                                                                                                                            )
                                                                                                                            sha = ref_data["object"]["sha"]

                                                                                                                            eate new branch
                                                                                                                            data = {
                                                                                                                            "ref": f"refs/heads/{branch}",
                                                                                                                            "sha": sha,
                                                                                                                            }

                                                                                                                            return self._request("POST", f"repos/{owner}/{repo}/git/refs", json=data)

                                                                                                                            def delete_branch(self, owner: str, repo: str, branch: str) -> None:
                                                                                                                                """Delete a branch."""
                                                                                                                                logger.warning(f"Deleting branch: {branch}")
                                                                                                                                self._request("DELETE", f"repos/{owner}/{repo}/git/refs/heads/{branch}")

                                                                                                                                tHub Actions

                                                                                                                                def trigger_workflow(
                                                                                                                                self,
                                                                                                                                owner: str,
                                                                                                                                repo: str,
                                                                                                                                workflow_id: str,
                                                                                                                                ref: str = "main",
                                                                                                                                inputs: dict[str, Any] | None = None,
                                                                                                                                ) -> None:
                                                                                                                                    """
                                                                                                                                    Trigger a GitHub Actions workflow.

                                                                                                                                    Args:
                                                                                                                                        owner: Repository owner
                                                                                                                                        repo: Repository name
                                                                                                                                        workflow_id: Workflow file name or ID
                                                                                                                                        ref: Git reference (branch/tag)
                                                                                                                                        inputs: Workflow inputs
                                                                                                                                        """
                                                                                                                                        logger.info(f"Triggering workflow: {workflow_id}")

                                                                                                                                        data = {"ref": ref}
                                                                                                                                        if inputs:
                                                                                                                                            data["inputs"] = inputs

                                                                                                                                            self._request(
                                                                                                                                            "POST",
                                                                                                                                            f"repos/{owner}/{repo}/actions/workflows/{workflow_id}/dispatches",
                                                                                                                                            json=data,
                                                                                                                                            )

                                                                                                                                            def list_workflow_runs(
                                                                                                                                            self,
                                                                                                                                            owner: str,
                                                                                                                                            repo: str,
                                                                                                                                            workflow_id: str | None = None,
                                                                                                                                            status: str | None = None,
                                                                                                                                            ) -> dict[str, Any]:
                                                                                                                                                """List workflow runs."""
                                                                                                                                                params = {}
                                                                                                                                                if status:
                                                                                                                                                    params["status"] = status

                                                                                                                                                    endpoint = f"repos/{owner}/{repo}/actions/runs"
                                                                                                                                                    if workflow_id:
                                                                                                                                                        endpoint = f"repos/{owner}/{repo}/actions/workflows/{workflow_id}/runs"

                                                                                                                                                        return self._request("GET", endpoint, params=params)

                                                                                                                                                        oject Boards (Projects V2)

                                                                                                                                                        def create_project(self, owner: str, title: str, body: str = "") -> dict[str, Any]:
                                                                                                                                                            """Create a GitHub Project (V2)."""
                                                                                                                                                            logger.info(f"Creating project: {title}")

                                                                                                                                                            aphQL query for Projects V2
                                                                                                                                                            query = """
                                                                                                                                                            mutation($ownerId: ID!, $title: String!, $body: String) {
                                                                                                                                                            eateProjectV2(input: {ownerId: $ownerId, title: $title, body: $body}) {
                                                                                                                                                            ojectV2 {

                                                                                                                                                            tle
                                                                                                                                                            l
                                                                                                                                                            "

                                                                                                                                                            t owner ID first
                                                                                                                                                            ner_data = self._request("GET", f"users/{owner}")

                                                                                                                                                            riables = {
                                                                                                                                                            wnerId": owner_data["node_id"],
                                                                                                                                                            itle": title,
                                                                                                                                                            ody": body,

                                                                                                                                                            sponse = requests.post(
                                                                                                                                                            ttps://api.github.com/graphql",
                                                                                                                                                            aders=self.headers,
                                                                                                                                                            on={"query": query, "variables": variables},
                                                                                                                                                            meout=30,

                                                                                                                                                            sponse.raise_for_status()
                                                                                                                                                            turn response.json()["data"]["createProjectV2"]["projectV2"]

                                                                                                                                                            bels

                                                                                                                                                            f create_label(
                                                                                                                                                            lf, owner: str, repo: str, name: str, color: str, description: str = ""
                                                                                                                                                            -> dict[str, Any]:
          """Create an issue label."""
          data = {
          "name": name,
          "color": color,
          "description": description,
          }

          return self._request("POST", f"repos/{owner}/{repo}/labels", json=data)

          lestones

          def create_milestone(
          self,
          owner: str,
          repo: str,
          title: str,
          due_on: str | None = None,
          description: str = "",
          ) -> dict[str, Any]:
              """Create a milestone."""
              data = {
              "title": title,
              "description": description,
              }

              if due_on:
                  data["due_on"] = due_on

                  return self._request("POST", f"repos/{owner}/{repo}/milestones", json=data)

                  bhooks

                  def create_webhook(
                  self,
                  owner: str,
                  repo: str,
                  url: str,
                  events: list[str] = ["push", "pull_request"],
                  secret: str | None = None,
                  ) -> dict[str, Any]:
                      """Create a repository webhook."""
                      logger.info(f"Creating webhook for: {url}")

                      config = {
                      "url": url,
                      "content_type": "json",
                      }

                      if secret:
                          config["secret"] = secret

                          data = {
                          "name": "web",
                          "active": True,
                          "events": events,
                          "config": config,
                          }

                          return self._request("POST", f"repos/{owner}/{repo}/hooks", json=data)

                          ility Methods

                          def bootstrap_repository(
                          self, name: str, description: str, template: str = "python"
                          ) -> dict[str, Any]:
                              """
                              Bootstrap a complete repository with standard structure.

                              Args:
                                  name: Repository name
                                  description: Repository description
                                  template: Template type (python, node, react, etc.)

                                  Returns:
                                      Repository setup data
                                      """
                                      logger.info(f"Bootstrapping repository: {name}")

                                      eate repository
                                      repo = self.create_repository(
                                      name=name,
                                      description=description,
                                      private=True,
                                      auto_init=True,
                                      gitignore_template=template.capitalize(),
                                      license_template="mit",
                                      )

                                      owner = repo["owner"]["login"]
                                      repo_name = repo["name"]

                                      eate default labels
                                      labels = [
                                      {
                                      "name": "bug",
                                      "color": "d73a4a",
                                      "description": "Something isn't working",
                                      },
                                      {
                                      "name": "enhancement",
                                      "color": "a2eeef",
                                      "description": "New feature or request",
                                      },
                                      {
                                      "name": "documentation",
                                      "color": "0075ca",
                                      "description": "Documentation improvements",
                                      },
                                      {
                                      "name": "good first issue",
                                      "color": "7057ff",
                                      "description": "Good for newcomers",
                                      },
                                      ]

                                      for label in labels:
                                          try:
                                              self.create_label(owner, repo_name, **label)
                                              except Exception as e:
                                                  logger.warning(f"Failed to create label: {e}")

                                                  eate develop branch
                                                  try:
                                                      self.create_branch(owner, repo_name, "develop", "main")
                                                      except Exception as e:
                                                          logger.warning(f"Failed to create develop branch: {e}")

                                                          return {
                                                          "repository": repo,
                                                          "owner": owner,
                                                          "repo_name": repo_name,
                                                          "url": repo["html_url"],
                                                          }

                                                          otocol compliance method
                                                          def health_check(self) -> dict[str, Any]:
                                                              ghtweight check: attempt to fetch current user
                                                              try:
                                                                  user = self._request("GET", "user")
                                                                  return {
                                                                  "login": user.get("login"),
                                                                  "scopes": self.headers.get("X-OAuth-Scopes"),
                                                                  }
                                                                  except Exception as e:  # pragma: no cover - best effort
                                                                  return {"error": str(e)}
