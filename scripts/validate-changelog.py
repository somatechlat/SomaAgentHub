#!/usr/bin/env python3
"""
Changelog Validator Script
Ensures version bumps match git tags as required by the style guide.
"""

import os
import sys
import re
import subprocess
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple


class ChangelogValidator:
    """Validates changelog format and version consistency."""
    
    def __init__(self, changelog_path: str = "docs/changelog.md"):
        self.changelog_path = Path(changelog_path)
        self.errors = []
        self.warnings = []
    
    def validate(self) -> bool:
        """Run complete changelog validation."""
        print("🔍 Validating changelog...")
        
        if not self.changelog_path.exists():
            self.errors.append(f"Changelog file not found: {self.changelog_path}")
            return False
        
        content = self.changelog_path.read_text(encoding='utf-8')
        
        self._validate_format(content)
        self._validate_version_consistency()
        self._validate_unreleased_section(content)
        self._validate_entry_format(content)
        
        return len(self.errors) == 0
    
    def _validate_format(self, content: str):
        """Validate changelog follows Keep a Changelog format."""
        required_sections = [
            r"# Changelog",
            r"## \[Unreleased\]",
            r"### Added|### Changed|### Deprecated|### Removed|### Fixed|### Security"
        ]
        
        for section in required_sections:
            if not re.search(section, content, re.IGNORECASE):
                self.errors.append(f"Missing required section: {section}")
    
    def _validate_version_consistency(self):
        """Validate that changelog versions match git tags."""
        try:
            # Get git tags
            result = subprocess.run(
                ["git", "tag", "--sort=-version:refname"],
                capture_output=True,
                text=True,
                check=True
            )
            git_tags = [tag.strip() for tag in result.stdout.split('\n') if tag.strip()]
            
            # Extract versions from changelog
            content = self.changelog_path.read_text(encoding='utf-8')
            changelog_versions = re.findall(r'## \[(\d+\.\d+\.\d+)\]', content)
            
            # Check if latest changelog version matches latest git tag
            if git_tags and changelog_versions:
                latest_tag = git_tags[0].lstrip('v')
                latest_changelog = changelog_versions[0]
                
                if latest_tag != latest_changelog:
                    self.errors.append(
                        f"Version mismatch: git tag '{latest_tag}' != changelog '{latest_changelog}'"
                    )
            
            # Check for missing versions
            for tag in git_tags[:5]:  # Check last 5 tags
                clean_tag = tag.lstrip('v')
                if clean_tag not in changelog_versions:
                    self.warnings.append(f"Git tag '{clean_tag}' not found in changelog")
                    
        except subprocess.CalledProcessError:
            self.warnings.append("Could not retrieve git tags for validation")
    
    def _validate_unreleased_section(self, content: str):
        """Validate unreleased section format."""
        unreleased_match = re.search(
            r'## \[Unreleased\](.*?)(?=## \[|\Z)', 
            content, 
            re.DOTALL
        )
        
        if not unreleased_match:
            self.errors.append("Missing [Unreleased] section")
            return
        
        unreleased_content = unreleased_match.group(1)
        
        # Check for proper subsections
        required_subsections = ["Added", "Changed", "Fixed"]
        for subsection in required_subsections:
            if f"### {subsection}" not in unreleased_content:
                self.warnings.append(f"Consider adding '### {subsection}' subsection to Unreleased")
    
    def _validate_entry_format(self, content: str):
        """Validate individual changelog entries."""
        # Find all version sections
        version_sections = re.findall(
            r'## \[(\d+\.\d+\.\d+)\] - (\d{4}-\d{2}-\d{2})(.*?)(?=## \[|\Z)',
            content,
            re.DOTALL
        )
        
        for version, date, section_content in version_sections:
            # Validate date format
            try:
                datetime.strptime(date, '%Y-%m-%d')
            except ValueError:
                self.errors.append(f"Invalid date format in version {version}: {date}")
            
            # Check for proper subsections
            if not re.search(r'### (Added|Changed|Deprecated|Removed|Fixed|Security)', section_content):
                self.warnings.append(f"Version {version} has no categorized changes")
            
            # Check for empty sections
            subsections = re.findall(r'### (Added|Changed|Deprecated|Removed|Fixed|Security)(.*?)(?=### |\Z)', section_content, re.DOTALL)
            for subsection_name, subsection_content in subsections:
                if not subsection_content.strip():
                    self.warnings.append(f"Empty {subsection_name} section in version {version}")
    
    def _get_latest_version(self) -> Optional[str]:
        """Get the latest version from changelog."""
        content = self.changelog_path.read_text(encoding='utf-8')
        versions = re.findall(r'## \[(\d+\.\d+\.\d+)\]', content)
        return versions[0] if versions else None
    
    def suggest_next_version(self) -> str:
        """Suggest next version based on unreleased changes."""
        content = self.changelog_path.read_text(encoding='utf-8')
        current_version = self._get_latest_version()
        
        if not current_version:
            return "1.0.0"
        
        # Parse current version
        major, minor, patch = map(int, current_version.split('.'))
        
        # Analyze unreleased changes
        unreleased_match = re.search(
            r'## \[Unreleased\](.*?)(?=## \[|\Z)', 
            content, 
            re.DOTALL
        )
        
        if not unreleased_match:
            return f"{major}.{minor}.{patch + 1}"
        
        unreleased_content = unreleased_match.group(1)
        
        # Suggest version bump based on change types
        if "### Added" in unreleased_content and "### Changed" in unreleased_content:
            # Minor version bump for new features
            return f"{major}.{minor + 1}.0"
        elif "### Fixed" in unreleased_content:
            # Patch version bump for bug fixes
            return f"{major}.{minor}.{patch + 1}"
        else:
            # Default to patch bump
            return f"{major}.{minor}.{patch + 1}"
    
    def print_results(self):
        """Print validation results."""
        print("\n" + "="*60)
        print("CHANGELOG VALIDATION RESULTS")
        print("="*60)
        
        if self.errors:
            print("❌ ERRORS:")
            for error in self.errors:
                print(f"  • {error}")
        
        if self.warnings:
            print("⚠️  WARNINGS:")
            for warning in self.warnings:
                print(f"  • {warning}")
        
        if not self.errors and not self.warnings:
            print("✅ Changelog validation passed!")
        
        # Suggest next version
        next_version = self.suggest_next_version()
        print(f"\n💡 Suggested next version: {next_version}")
        
        print("="*60)


def main():
    """Main entry point."""
    changelog_path = "docs/changelog.md"
    
    if len(sys.argv) > 1:
        changelog_path = sys.argv[1]
    
    validator = ChangelogValidator(changelog_path)
    is_valid = validator.validate()
    validator.print_results()
    
    # Exit with error code if validation failed
    if not is_valid:
        sys.exit(1)


if __name__ == "__main__":
    main()