#!/usr/bin/env python3
"""
IDKit SDK Generator

Automatically generates client SDKs for multiple programming languages
from the OpenAPI specification.

Usage:
    python generate_sdk.py [language] [--output DIR] [--version VERSION]

Languages:
    typescript  - TypeScript/JavaScript SDK
    python      - Python SDK
    go          - Go SDK
    ruby        - Ruby SDK
    all         - Generate all SDKs
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional


# SDK configuration per language
SDK_CONFIG = {
    "typescript": {
        "generator": "typescript-fetch",
        "package_name": "@idkit/sdk",
        "output_dir": "sdks/typescript",
        "additional_properties": {
            "npmName": "@idkit/sdk",
            "supportsES6": True,
            "typescriptThreePlus": True,
            "withInterfaces": True,
        },
        "post_generate": ["npm install", "npm run build"],
    },
    "python": {
        "generator": "python",
        "package_name": "idkit",
        "output_dir": "sdks/python",
        "additional_properties": {
            "projectName": "idkit",
            "packageName": "idkit",
            "packageVersion": "2.0.0",
        },
        "post_generate": ["pip install -e .", "python -m pytest tests/"],
    },
    "go": {
        "generator": "go",
        "package_name": "idkit",
        "output_dir": "sdks/go",
        "additional_properties": {
            "packageName": "idkit",
            "isGoSubmodule": True,
            "generateInterfaces": True,
        },
        "post_generate": ["go mod tidy", "go build ./..."],
    },
    "ruby": {
        "generator": "ruby",
        "package_name": "idkit",
        "output_dir": "sdks/ruby",
        "additional_properties": {
            "gemName": "idkit",
            "moduleName": "Idkit",
            "gemVersion": "2.0.0",
        },
        "post_generate": ["bundle install", "rake build"],
    },
}


class SDKGenerator:
    """Generate client SDKs from OpenAPI specification."""
    
    def __init__(
        self,
        openapi_path: str = "openapi.yaml",
        output_base: str = ".",
        version: str = "2.0.0"
    ):
        self.openapi_path = Path(openapi_path)
        self.output_base = Path(output_base)
        self.version = version
        
        # Verify OpenAPI spec exists
        if not self.openapi_path.exists():
            print(f"Error: OpenAPI specification not found: {self.openapi_path}")
            sys.exit(1)
    
    def generate(self, language: str) -> bool:
        """Generate SDK for a specific language."""
        if language not in SDK_CONFIG:
            print(f"Error: Unsupported language: {language}")
            print(f"Supported: {', '.join(SDK_CONFIG.keys())}")
            return False
        
        config = SDK_CONFIG[language]
        output_dir = self.output_base / config["output_dir"]
        
        print(f"\n{'='*60}")
        print(f"Generating {language.upper()} SDK")
        print(f"{'='*60}")
        
        # Create output directory
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Build openapi-generator command
        cmd = [
            "openapi-generator-cli",
            "generate",
            "-i", str(self.openapi_path),
            "-g", config["generator"],
            "-o", str(output_dir),
            "--package-name", config["package_name"],
        ]
        
        # Add additional properties
        for key, value in config.get("additional_properties", {}).items():
            if isinstance(value, bool):
                value = str(value).lower()
            cmd.extend(["--additional-properties", f"{key}={value}"])
        
        # Update version
        cmd.extend(["--additional-properties", f"packageVersion={self.version}"])
        
        print(f"Running: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                print(f"Error generating SDK: {result.stderr}")
                return False
            print(f"✓ SDK generated to {output_dir}")
        except FileNotFoundError:
            print("Error: openapi-generator-cli not found")
            print("Install with: npm install -g @openapitools/openapi-generator-cli")
            return False
        
        # Add custom tweaks for each language
        self._apply_customizations(language, output_dir)
        
        # Run post-generation commands
        if config.get("post_generate"):
            print("\nRunning post-generation steps...")
            for cmd in config["post_generate"]:
                try:
                    subprocess.run(cmd.split(), cwd=output_dir, check=True)
                    print(f"✓ {cmd}")
                except subprocess.CalledProcessError as e:
                    print(f"Warning: {cmd} failed: {e}")
        
        return True
    
    def _apply_customizations(self, language: str, output_dir: Path):
        """Apply language-specific customizations after generation."""
        if language == "typescript":
            self._customize_typescript(output_dir)
        elif language == "python":
            self._customize_python(output_dir)
        elif language == "go":
            self._customize_go(output_dir)
        elif language == "ruby":
            self._customize_ruby(output_dir)
    
    def _customize_typescript(self, output_dir: Path):
        """Add TypeScript-specific enhancements."""
        # Add custom README
        readme_content = f"""# IDKit TypeScript SDK

Official TypeScript/JavaScript SDK for the IDKit API.

## Installation

```bash
npm install @idkit/sdk
```

## Quick Start

```typescript
import {{ IDKit }} from '@idkit/sdk';

const client = new IDKit({{
  apiKey: 'your-api-key'
}});

// Generate content
const content = await client.content.generate({{
  prompt: 'Write a tweet about AI',
  twin_id: 'twin_123'
}});

console.log(content.text);
```

## Authentication

Set your API key when creating the client:

```typescript
const client = new IDKit({{ apiKey: process.env.IDKIT_API_KEY }});
```

## Version

SDK Version: {self.version}
API Version: v2

## Documentation

Full documentation: https://docs.idkit.io/sdks/typescript
"""
        (output_dir / "README.md").write_text(readme_content)
    
    def _customize_python(self, output_dir: Path):
        """Add Python-specific enhancements."""
        readme_content = f"""# IDKit Python SDK

Official Python SDK for the IDKit API.

## Installation

```bash
pip install idkit
```

## Quick Start

```python
from idkit import IDKit

client = IDKit(api_key="your-api-key")

# Generate content
content = client.content.generate(
    prompt="Write a tweet about AI",
    twin_id="twin_123"
)

print(content.text)
```

## Async Support

```python
import asyncio
from idkit import AsyncIDKit

async def main():
    client = AsyncIDKit(api_key="your-api-key")
    content = await client.content.generate(
        prompt="Write a tweet",
        twin_id="twin_123"
    )
    print(content.text)

asyncio.run(main())
```

## Version

SDK Version: {self.version}
API Version: v2

## Documentation

Full documentation: https://docs.idkit.io/sdks/python
"""
        (output_dir / "README.md").write_text(readme_content)
    
    def _customize_go(self, output_dir: Path):
        """Add Go-specific enhancements."""
        readme_content = f"""# IDKit Go SDK

Official Go SDK for the IDKit API.

## Installation

```bash
go get github.com/idkit/go-sdk
```

## Quick Start

```go
package main

import (
    "fmt"
    "github.com/idkit/go-sdk"
)

func main() {{
    client := idkit.NewClient("your-api-key")
    
    content, err := client.Content.Generate(&idkit.GenerateRequest{{
        Prompt:  "Write a tweet about AI",
        TwinID:  "twin_123",
    }})
    
    if err != nil {{
        panic(err)
    }}
    
    fmt.Println(content.Text)
}}
```

## Version

SDK Version: {self.version}
API Version: v2

## Documentation

Full documentation: https://docs.idkit.io/sdks/go
"""
        (output_dir / "README.md").write_text(readme_content)
    
    def _customize_ruby(self, output_dir: Path):
        """Add Ruby-specific enhancements."""
        readme_content = f"""# IDKit Ruby SDK

Official Ruby SDK for the IDKit API.

## Installation

```ruby
gem 'idkit'
```

## Quick Start

```ruby
require 'idkit'

client = Idkit::Client.new(api_key: 'your-api-key')

content = client.content.generate(
  prompt: 'Write a tweet about AI',
  twin_id: 'twin_123'
)

puts content.text
```

## Version

SDK Version: {self.version}
API Version: v2

## Documentation

Full documentation: https://docs.idkit.io/sdks/ruby
"""
        (output_dir / "README.md").write_text(readme_content)
    
    def generate_all(self) -> Dict[str, bool]:
        """Generate SDKs for all supported languages."""
        results = {}
        for language in SDK_CONFIG.keys():
            results[language] = self.generate(language)
        return results


def main():
    parser = argparse.ArgumentParser(
        description="Generate IDKit client SDKs from OpenAPI specification"
    )
    parser.add_argument(
        "language",
        choices=list(SDK_CONFIG.keys()) + ["all"],
        help="Target language for SDK generation"
    )
    parser.add_argument(
        "--openapi",
        default="openapi.yaml",
        help="Path to OpenAPI specification file"
    )
    parser.add_argument(
        "--output",
        default=".",
        help="Output base directory"
    )
    parser.add_argument(
        "--version",
        default="2.0.0",
        help="SDK version"
    )
    
    args = parser.parse_args()
    
    generator = SDKGenerator(
        openapi_path=args.openapi,
        output_base=args.output,
        version=args.version
    )
    
    if args.language == "all":
        results = generator.generate_all()
        print("\n" + "="*60)
        print("SDK Generation Summary")
        print("="*60)
        for lang, success in results.items():
            status = "✓" if success else "✗"
            print(f"  {status} {lang}")
    else:
        success = generator.generate(args.language)
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
