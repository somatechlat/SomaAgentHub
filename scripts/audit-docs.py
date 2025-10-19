#!/usr/bin/env python3
"""
Documentation Health Audit Script
Generates quarterly documentation health reports as required by the style guide.
"""

import os
import sys
import json
import requests
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any
import markdown
import re


class DocumentationAuditor:
    """Audits documentation health and generates reports."""
    
    def __init__(self, docs_path: str = "docs"):
        self.docs_path = Path(docs_path)
        self.report = {
            "audit_date": datetime.utcnow().isoformat(),
            "total_files": 0,
            "stale_files": [],
            "broken_links": [],
            "missing_metadata": [],
            "health_score": 0.0
        }
    
    def audit_all(self) -> Dict[str, Any]:
        """Run complete documentation audit."""
        print("🔍 Starting documentation audit...")
        
        self._scan_files()
        self._check_stale_content()
        self._check_broken_links()
        self._check_metadata()
        self._calculate_health_score()
        
        return self.report
    
    def _scan_files(self):
        """Scan all markdown files in docs directory."""
        md_files = list(self.docs_path.rglob("*.md"))
        self.report["total_files"] = len(md_files)
        print(f"📄 Found {len(md_files)} documentation files")
    
    def _check_stale_content(self):
        """Check for files not updated in >90 days."""
        stale_threshold = datetime.now() - timedelta(days=90)
        
        for md_file in self.docs_path.rglob("*.md"):
            try:
                stat = md_file.stat()
                modified_time = datetime.fromtimestamp(stat.st_mtime)
                
                if modified_time < stale_threshold:
                    self.report["stale_files"].append({
                        "file": str(md_file.relative_to(self.docs_path)),
                        "last_modified": modified_time.isoformat(),
                        "days_stale": (datetime.now() - modified_time).days
                    })
            except Exception as e:
                print(f"⚠️  Error checking {md_file}: {e}")
        
        print(f"📅 Found {len(self.report['stale_files'])} stale files (>90 days)")
    
    def _check_broken_links(self):
        """Check for broken internal and external links."""
        for md_file in self.docs_path.rglob("*.md"):
            try:
                content = md_file.read_text(encoding='utf-8')
                
                # Find markdown links
                links = re.findall(r'\[([^\]]+)\]\(([^)]+)\)', content)
                
                for link_text, link_url in links:
                    if self._is_broken_link(link_url, md_file):
                        self.report["broken_links"].append({
                            "file": str(md_file.relative_to(self.docs_path)),
                            "link_text": link_text,
                            "link_url": link_url,
                            "type": "external" if link_url.startswith("http") else "internal"
                        })
            except Exception as e:
                print(f"⚠️  Error checking links in {md_file}: {e}")
        
        print(f"🔗 Found {len(self.report['broken_links'])} broken links")
    
    def _is_broken_link(self, url: str, source_file: Path) -> bool:
        """Check if a link is broken."""
        if url.startswith("http"):
            # External link - check HTTP status
            try:
                response = requests.head(url, timeout=5, allow_redirects=True)
                return response.status_code >= 400
            except:
                return True
        else:
            # Internal link - check file exists
            if url.startswith("#"):
                # Anchor link - skip for now
                return False
            
            # Relative path
            target_path = (source_file.parent / url).resolve()
            return not target_path.exists()
    
    def _check_metadata(self):
        """Check for missing required metadata."""
        required_sections = ["Purpose statement", "Audience", "Prerequisites"]
        
        for md_file in self.docs_path.rglob("*.md"):
            try:
                content = md_file.read_text(encoding='utf-8')
                missing = []
                
                # Check for purpose statement (first paragraph after title)
                if not re.search(r'^#[^#].*?\n\n\*\*.*?\*\*', content, re.MULTILINE | re.DOTALL):
                    missing.append("Purpose statement")
                
                # Check for audience section
                if "audience" not in content.lower():
                    missing.append("Audience")
                
                # Check for prerequisites section
                if "prerequisite" not in content.lower():
                    missing.append("Prerequisites")
                
                if missing:
                    self.report["missing_metadata"].append({
                        "file": str(md_file.relative_to(self.docs_path)),
                        "missing": missing
                    })
            except Exception as e:
                print(f"⚠️  Error checking metadata in {md_file}: {e}")
        
        print(f"📋 Found {len(self.report['missing_metadata'])} files with missing metadata")
    
    def _calculate_health_score(self):
        """Calculate overall documentation health score."""
        total_files = self.report["total_files"]
        if total_files == 0:
            self.report["health_score"] = 0.0
            return
        
        # Scoring weights
        stale_penalty = len(self.report["stale_files"]) * 0.1
        broken_links_penalty = len(self.report["broken_links"]) * 0.2
        missing_metadata_penalty = len(self.report["missing_metadata"]) * 0.15
        
        total_penalty = stale_penalty + broken_links_penalty + missing_metadata_penalty
        max_score = 100.0
        
        self.report["health_score"] = max(0.0, max_score - (total_penalty / total_files * 100))
        
        print(f"📊 Documentation health score: {self.report['health_score']:.1f}/100")
    
    def generate_report(self, output_file: str = "documentation-health-report.json"):
        """Generate JSON report file."""
        with open(output_file, 'w') as f:
            json.dump(self.report, f, indent=2)
        
        print(f"📄 Report saved to {output_file}")
        
        # Print summary
        print("\n" + "="*60)
        print("DOCUMENTATION HEALTH REPORT SUMMARY")
        print("="*60)
        print(f"Audit Date: {self.report['audit_date']}")
        print(f"Total Files: {self.report['total_files']}")
        print(f"Stale Files (>90d): {len(self.report['stale_files'])}")
        print(f"Broken Links: {len(self.report['broken_links'])}")
        print(f"Missing Metadata: {len(self.report['missing_metadata'])}")
        print(f"Health Score: {self.report['health_score']:.1f}/100")
        
        if self.report['health_score'] < 80:
            print("\n⚠️  WARNING: Documentation health below 80%. Action required.")
        elif self.report['health_score'] < 90:
            print("\n💡 INFO: Documentation health good but could be improved.")
        else:
            print("\n✅ EXCELLENT: Documentation health is excellent!")
        
        print("="*60)


def main():
    """Main entry point."""
    if len(sys.argv) > 1:
        docs_path = sys.argv[1]
    else:
        docs_path = "docs"
    
    if not os.path.exists(docs_path):
        print(f"❌ Error: Documentation path '{docs_path}' not found")
        sys.exit(1)
    
    auditor = DocumentationAuditor(docs_path)
    report = auditor.audit_all()
    auditor.generate_report()
    
    # Exit with error code if health score is too low
    if report["health_score"] < 70:
        sys.exit(1)


if __name__ == "__main__":
    main()