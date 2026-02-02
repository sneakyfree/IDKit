#!/usr/bin/env python3
"""
Import Chain Auditor for IDKit Backend

Identifies circular import dependencies in Python files.
Uses AST parsing to build dependency graph and detect cycles.

Usage:
    python scripts/audit_imports.py

Output:
    Writes findings to import_audit.txt
"""

import ast
import os
import sys
from pathlib import Path
from collections import defaultdict
from typing import Set, List, Dict, Tuple


class ImportAuditor:
    """Analyze Python imports and detect circular dependencies."""
    
    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        self.imports: Dict[str, Set[str]] = defaultdict(set)
        self.errors: List[str] = []
    
    def get_module_name(self, file_path: Path) -> str:
        """Convert file path to module name."""
        rel_path = file_path.relative_to(self.base_path)
        # Remove .py and convert path separators to dots
        module = str(rel_path).replace("/", ".").replace("\\", ".").replace(".py", "")
        if module.endswith(".__init__"):
            module = module[:-9]  # Remove .__init__
        return f"app.{module}" if not module.startswith("app") else module
    
    def parse_imports(self, file_path: Path) -> Set[str]:
        """Extract all imports from a Python file."""
        imports = set()
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name.startswith("app."):
                            imports.add(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module and node.module.startswith("app."):
                        imports.add(node.module)
        except SyntaxError as e:
            self.errors.append(f"Syntax error in {file_path}: {e}")
        except Exception as e:
            self.errors.append(f"Error parsing {file_path}: {e}")
        
        return imports
    
    def scan_directory(self, directory: str) -> None:
        """Scan all Python files in directory."""
        dir_path = self.base_path / directory
        
        if not dir_path.exists():
            print(f"Warning: Directory not found: {dir_path}")
            return
        
        for py_file in dir_path.rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue
            
            module_name = self.get_module_name(py_file)
            imports = self.parse_imports(py_file)
            self.imports[module_name] = imports
    
    def find_cycles(self) -> List[List[str]]:
        """Find all import cycles using DFS."""
        cycles = []
        visited = set()
        rec_stack = []
        
        def dfs(module: str, path: List[str]) -> None:
            if module in rec_stack:
                # Found a cycle
                cycle_start = rec_stack.index(module)
                cycle = rec_stack[cycle_start:] + [module]
                if cycle not in cycles:
                    cycles.append(cycle)
                return
            
            if module in visited:
                return
            
            visited.add(module)
            rec_stack.append(module)
            
            for imported in self.imports.get(module, set()):
                if imported in self.imports:  # Only check modules we've scanned
                    dfs(imported, path + [imported])
            
            rec_stack.pop()
        
        for module in self.imports:
            visited.clear()
            rec_stack.clear()
            dfs(module, [module])
        
        return cycles
    
    def get_import_chain(self, from_module: str, to_module: str) -> List[str]:
        """Get the import path from one module to another."""
        from collections import deque
        
        queue = deque([(from_module, [from_module])])
        visited = {from_module}
        
        while queue:
            current, path = queue.popleft()
            
            if current == to_module:
                return path
            
            for imported in self.imports.get(current, set()):
                if imported not in visited and imported in self.imports:
                    visited.add(imported)
                    queue.append((imported, path + [imported]))
        
        return []
    
    def audit(self) -> str:
        """Run full audit and return report."""
        print("Scanning directories...")
        
        # Scan all relevant directories
        self.scan_directory("models")
        self.scan_directory("api")
        self.scan_directory("services")
        self.scan_directory("core")
        self.scan_directory("middleware")
        
        print(f"Found {len(self.imports)} modules")
        
        # Find cycles
        print("Detecting cycles...")
        cycles = self.find_cycles()
        
        # Build report
        report = []
        report.append("=" * 60)
        report.append("IDKit Backend Import Audit Report")
        report.append("=" * 60)
        report.append("")
        report.append(f"Modules scanned: {len(self.imports)}")
        report.append(f"Circular import chains found: {len(cycles)}")
        report.append("")
        
        if self.errors:
            report.append("PARSE ERRORS:")
            for error in self.errors:
                report.append(f"  - {error}")
            report.append("")
        
        if cycles:
            report.append("CIRCULAR IMPORTS DETECTED:")
            report.append("")
            for i, cycle in enumerate(cycles, 1):
                report.append(f"Cycle {i}:")
                report.append(f"  {' -> '.join(cycle)}")
                report.append("")
        else:
            report.append("✅ No circular imports detected!")
        
        report.append("")
        report.append("=" * 60)
        report.append("MODULE DEPENDENCY SUMMARY")
        report.append("=" * 60)
        
        # Show modules with most imports (potential problem areas)
        sorted_modules = sorted(
            self.imports.items(),
            key=lambda x: len(x[1]),
            reverse=True
        )[:20]
        
        report.append("")
        report.append("Top 20 modules by import count:")
        for module, imports in sorted_modules:
            report.append(f"  {module}: {len(imports)} imports")
        
        return "\n".join(report)


def main():
    # Find the app directory
    script_dir = Path(__file__).parent
    app_dir = script_dir.parent / "app"
    
    if not app_dir.exists():
        print(f"Error: app directory not found at {app_dir}")
        sys.exit(1)
    
    print(f"Auditing imports in: {app_dir}")
    
    auditor = ImportAuditor(app_dir)
    report = auditor.audit()
    
    # Print to console
    print(report)
    
    # Write to file
    output_file = script_dir.parent / "import_audit.txt"
    with open(output_file, "w") as f:
        f.write(report)
    
    print(f"\nReport saved to: {output_file}")
    
    # Return exit code based on findings
    cycles = auditor.find_cycles()
    return 1 if cycles else 0


if __name__ == "__main__":
    sys.exit(main())
