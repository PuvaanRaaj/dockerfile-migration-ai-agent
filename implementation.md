# Docker Migration Agent with Claude Agent SDK

## Overview

This guide helps you build an AI agent that learns from your custom Dockerfile patterns and applies them consistently across your infrastructure. The agent will reference your established methods for installing NewRelic, Supervisor, Gearman, and other tools.

## Architecture

```
┌─────────────────────────────────────────┐
│   Your Local Development Machine       │
├─────────────────────────────────────────┤
│                                         │
│  [Reference Dockerfiles]                │
│  └─ examples/                           │
│     ├─ Dockerfile.reference            │
│     ├─ newrelic-install.snippet        │
│     └─ supervisor-setup.snippet        │
│                                         │
│  [Docker Migration Agent]               │
│  └─ Built with Claude Agent SDK        │
│      ├─ Context: Reference patterns    │
│      ├─ Tools: File read/write         │
│      └─ Memory: Previous migrations    │
│                                         │
│  [Target Repositories]                  │
│  └─ Projects to migrate                │
│                                         │
└─────────────────────────────────────────┘
```

## Project Structure

```
docker-migration-agent/
├── reference-dockerfiles/          # Your custom examples
│   ├── laravel-app.Dockerfile
│   ├── patterns/
│   │   ├── newrelic.md
│   │   ├── supervisor.md
│   │   └── gearman.md
│   └── best-practices.md
│
├── agent/
│   ├── main.py                     # Agent entry point
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── file_reader.py         # Read Dockerfiles
│   │   ├── file_writer.py         # Write updated files
│   │   └── pattern_matcher.py     # Find your patterns
│   ├── context/
│   │   ├── __init__.py
│   │   └── knowledge_loader.py    # Load reference docs
│   └── config.py
│
├── target-repos/                   # Repos to migrate
│   └── payment-api/
│       └── Dockerfile
│
├── .env.example
├── .env
├── .gitignore
├── requirements.txt
└── README.md
```

## Installation

### 1. Create Project Directory

```bash
mkdir docker-migration-agent
cd docker-migration-agent
```

### 2. Create Virtual Environment

```bash
python -m venv venv

# On Linux/Mac:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

### 3. Install Dependencies

Create `requirements.txt`:

```
anthropic==0.40.0
python-dotenv==1.0.0
```

Install:

```bash
pip install -r requirements.txt
```

### 4. Setup Environment

Create `.env.example`:

```
ANTHROPIC_API_KEY=your_api_key_here
```

Copy and configure:

```bash
cp .env.example .env
# Edit .env and add your actual Anthropic API key
```

Create `.gitignore`:

```
venv/
.env
__pycache__/
*.pyc
*.pyo
*.migrated.Dockerfile
.DS_Store
```

## Reference Pattern Documentation

### Create Pattern Files

#### `reference-dockerfiles/patterns/newrelic.md`

```markdown
# NewRelic Installation Pattern

## My Standard Approach
1. Install during build phase (not runtime)
2. Use specific version pinning
3. Configure via environment variables
4. Silent installation mode

## Dockerfile snippet:

```dockerfile
# NewRelic PHP Agent (version 10.11.0.3)
RUN curl -L https://download.newrelic.com/php_agent/release/newrelic-php5-10.11.0.3-linux.tar.gz | tar -C /tmp -zx && \
    export NR_INSTALL_USE_CP_NOT_LN=1 && \
    export NR_INSTALL_SILENT=1 && \
    /tmp/newrelic-php5-*/newrelic-install install && \
    rm -rf /tmp/newrelic-php5-* /tmp/nrinstall* && \
    sed -i "s/REPLACE_WITH_REAL_KEY/${NEWRELIC_LICENSE}/" /usr/local/etc/php/conf.d/newrelic.ini && \
    sed -i "s/\"PHP Application\"/${NEWRELIC_APPNAME}/" /usr/local/etc/php/conf.d/newrelic.ini
```

## Environment variables required:
- `NEWRELIC_LICENSE` - Your NewRelic license key
- `NEWRELIC_APPNAME` - Application name for APM

## Important notes:
- Always use `NR_INSTALL_USE_CP_NOT_LN=1` to avoid symlink issues
- Pin specific version for reproducibility
- Clean up installation files to reduce image size
```

#### `reference-dockerfiles/patterns/supervisor.md`

```markdown
# Supervisor Installation Pattern

## My Standard Approach
1. Install via system package manager
2. Configuration files in `/etc/supervisor/conf.d/`
3. Always include logging configuration
4. Run as non-root user when possible

## Dockerfile snippet:

```dockerfile
# Install Supervisor
RUN apt-get update && apt-get install -y supervisor && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy supervisor configuration
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Create log directory
RUN mkdir -p /var/log/supervisor && \
    chown -R www-data:www-data /var/log/supervisor
```

## Example supervisord.conf:

```ini
[supervisord]
nodaemon=true
user=root
logfile=/var/log/supervisor/supervisord.log
pidfile=/var/run/supervisord.pid

[program:laravel-worker]
process_name=%(program_name)s_%(process_num)02d
command=php /var/www/html/artisan queue:work --sleep=3 --tries=3
autostart=true
autorestart=true
user=www-data
numprocs=2
redirect_stderr=true
stdout_logfile=/var/log/supervisor/worker.log
```

## Important notes:
- Always set `nodaemon=true` for Docker containers
- Use `www-data` user for PHP processes
- Configure proper logging paths
```

#### `reference-dockerfiles/patterns/gearman.md`

```markdown
# Gearman Installation Pattern

## My Standard Approach
1. Install libgearman-dev first
2. Install PHP extension via PECL
3. Enable extension in php.ini
4. Verify installation

## Dockerfile snippet:

```dockerfile
# Install Gearman dependencies
RUN apt-get update && \
    apt-get install -y libgearman-dev && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install Gearman PHP extension
RUN pecl install gearman-2.1.0 && \
    docker-php-ext-enable gearman && \
    php -m | grep gearman
```

## Important notes:
- Pin PECL version for reproducibility
- Use `docker-php-ext-enable` for official PHP images
- Verify installation with `php -m`
- Clean up apt lists to reduce image size
```

### `reference-dockerfiles/laravel-app.Dockerfile`

```dockerfile
# Multi-stage build example for Laravel application
FROM php:8.3-fpm as base

# Set working directory
WORKDIR /var/www/html

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    libpng-dev \
    libonig-dev \
    libxml2-dev \
    libzip-dev \
    zip \
    unzip \
    libgearman-dev \
    supervisor \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install PHP extensions
RUN docker-php-ext-install pdo_mysql mbstring exif pcntl bcmath gd zip

# Install Gearman PHP extension
RUN pecl install gearman-2.1.0 && \
    docker-php-ext-enable gearman

# Install NewRelic PHP Agent
ARG NEWRELIC_LICENSE
ARG NEWRELIC_APPNAME
RUN curl -L https://download.newrelic.com/php_agent/release/newrelic-php5-10.11.0.3-linux.tar.gz | tar -C /tmp -zx && \
    export NR_INSTALL_USE_CP_NOT_LN=1 && \
    export NR_INSTALL_SILENT=1 && \
    /tmp/newrelic-php5-*/newrelic-install install && \
    rm -rf /tmp/newrelic-php5-* /tmp/nrinstall*

# Install Composer
COPY --from=composer:latest /usr/bin/composer /usr/bin/composer

# Copy supervisor configuration
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Create necessary directories
RUN mkdir -p /var/log/supervisor && \
    chown -R www-data:www-data /var/log/supervisor

# Copy application
COPY --chown=www-data:www-data . /var/www/html

# Install dependencies
RUN composer install --no-dev --optimize-autoloader --no-interaction

# Set permissions
RUN chown -R www-data:www-data /var/www/html/storage /var/www/html/bootstrap/cache

EXPOSE 9000

CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
```

## Agent Implementation

### `agent/config.py`

```python
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    # API Configuration
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
    MODEL = "claude-sonnet-4-5-20250929"
    MAX_TOKENS = 4000
    
    # Paths
    BASE_DIR = Path(__file__).parent.parent
    REFERENCE_DIR = BASE_DIR / "reference-dockerfiles"
    PATTERNS_DIR = REFERENCE_DIR / "patterns"
    TARGET_REPOS_DIR = BASE_DIR / "target-repos"
    
    # Agent Settings
    TEMPERATURE = 0.3  # Lower for more consistent outputs
    
    @classmethod
    def validate(cls):
        """Validate configuration"""
        if not cls.ANTHROPIC_API_KEY:
            raise ValueError("ANTHROPIC_API_KEY not set in .env file")
        
        if not cls.REFERENCE_DIR.exists():
            raise ValueError(f"Reference directory not found: {cls.REFERENCE_DIR}")
        
        return True
```

### `agent/context/knowledge_loader.py`

```python
from pathlib import Path
from typing import Dict
from agent.config import Config

class KnowledgeLoader:
    """Load and manage reference patterns and Dockerfiles"""
    
    def __init__(self):
        self.config = Config()
        self.patterns = {}
        
    def load_all_patterns(self) -> Dict[str, str]:
        """Load all pattern files from reference directory"""
        patterns = {}
        
        # Load pattern markdown files
        if self.config.PATTERNS_DIR.exists():
            for pattern_file in self.config.PATTERNS_DIR.glob("*.md"):
                with open(pattern_file, 'r', encoding='utf-8') as f:
                    patterns[pattern_file.stem] = f.read()
                    print(f"✓ Loaded pattern: {pattern_file.stem}")
        
        # Load reference Dockerfile
        ref_dockerfile = self.config.REFERENCE_DIR / "laravel-app.Dockerfile"
        if ref_dockerfile.exists():
            with open(ref_dockerfile, 'r', encoding='utf-8') as f:
                patterns['reference_dockerfile'] = f.read()
                print(f"✓ Loaded reference Dockerfile")
        
        self.patterns = patterns
        return patterns
    
    def get_pattern(self, pattern_name: str) -> str:
        """Get a specific pattern by name"""
        return self.patterns.get(pattern_name, "")
    
    def list_patterns(self) -> list:
        """List all available pattern names"""
        return list(self.patterns.keys())
```

### `agent/tools/file_reader.py`

```python
from pathlib import Path
from typing import Optional

class FileReader:
    """Tool for reading Dockerfiles and related files"""
    
    @staticmethod
    def read_dockerfile(filepath: str) -> Optional[str]:
        """Read a Dockerfile from given path"""
        try:
            path = Path(filepath)
            if not path.exists():
                print(f"❌ File not found: {filepath}")
                return None
            
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            print(f"✓ Read {len(content)} characters from {filepath}")
            return content
            
        except Exception as e:
            print(f"❌ Error reading file: {e}")
            return None
    
    @staticmethod
    def read_file(filepath: str) -> Optional[str]:
        """Read any text file"""
        try:
            path = Path(filepath)
            if not path.exists():
                return None
            
            with open(path, 'r', encoding='utf-8') as f:
                return f.read()
                
        except Exception as e:
            print(f"❌ Error reading file: {e}")
            return None
```

### `agent/tools/file_writer.py`

```python
from pathlib import Path
from typing import Optional

class FileWriter:
    """Tool for writing updated Dockerfiles"""
    
    @staticmethod
    def write_dockerfile(filepath: str, content: str, suffix: str = ".migrated") -> bool:
        """Write migrated Dockerfile"""
        try:
            path = Path(filepath)
            
            # Create output filename
            if suffix:
                output_path = path.parent / f"{path.stem}{suffix}{path.suffix}"
            else:
                output_path = path
            
            # Write content
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"✓ Wrote {len(content)} characters to {output_path}")
            return True
            
        except Exception as e:
            print(f"❌ Error writing file: {e}")
            return False
    
    @staticmethod
    def backup_file(filepath: str) -> bool:
        """Create backup of original file"""
        try:
            path = Path(filepath)
            if not path.exists():
                return False
            
            backup_path = path.parent / f"{path.stem}.backup{path.suffix}"
            
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            with open(backup_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"✓ Created backup: {backup_path}")
            return True
            
        except Exception as e:
            print(f"❌ Error creating backup: {e}")
            return False
```

### `agent/tools/__init__.py`

```python
from .file_reader import FileReader
from .file_writer import FileWriter

__all__ = ['FileReader', 'FileWriter']
```

### `agent/context/__init__.py`

```python
from .knowledge_loader import KnowledgeLoader

__all__ = ['KnowledgeLoader']
```

### `agent/main.py`

```python
import anthropic
from agent.config import Config
from agent.context.knowledge_loader import KnowledgeLoader
from agent.tools.file_reader import FileReader
from agent.tools.file_writer import FileWriter

class DockerMigrationAgent:
    """AI Agent for migrating Dockerfiles using custom patterns"""
    
    def __init__(self):
        # Validate configuration
        Config.validate()
        
        # Initialize Anthropic client
        self.client = anthropic.Anthropic(api_key=Config.ANTHROPIC_API_KEY)
        
        # Load reference patterns
        self.knowledge = KnowledgeLoader()
        self.reference_patterns = self.knowledge.load_all_patterns()
        
        # Initialize tools
        self.file_reader = FileReader()
        self.file_writer = FileWriter()
        
    def create_system_prompt(self) -> str:
        """Build system prompt with reference patterns"""
        
        prompt_parts = [
            "You are a Docker migration specialist with expertise in Laravel applications.",
            "",
            "You MUST follow these custom patterns from the user's infrastructure:",
            ""
        ]
        
        # Add reference Dockerfile if available
        if 'reference_dockerfile' in self.reference_patterns:
            prompt_parts.extend([
                "## Reference Dockerfile (ALWAYS use as template):",
                "```dockerfile",
                self.reference_patterns['reference_dockerfile'],
                "```",
                ""
            ])
        
        # Add all other patterns
        for pattern_name, pattern_content in self.reference_patterns.items():
            if pattern_name != 'reference_dockerfile':
                prompt_parts.extend([
                    f"## {pattern_name.title()} Pattern:",
                    pattern_content,
                    ""
                ])
        
        # Add rules
        prompt_parts.extend([
            "## MIGRATION RULES:",
            "1. Always follow the EXACT installation methods shown above",
            "2. Maintain version pinning strategy from reference patterns",
            "3. Use multi-stage builds as shown in reference Dockerfile",
            "4. Never deviate from these patterns without explicit approval",
            "5. Preserve user's established conventions and structure",
            "6. Clean up package lists and temporary files to reduce image size",
            "7. Use specific version numbers, not 'latest' tags",
            "8. Include comments explaining significant changes",
            "",
            "When presenting the migrated Dockerfile:",
            "- First explain what you're changing and why",
            "- Then provide the complete updated Dockerfile in a code block",
            "- Highlight any differences from the original",
            "- Note any potential issues or recommendations"
        ])
        
        return "\n".join(prompt_parts)
    
    def migrate_dockerfile(self, target_dockerfile_path: str, task: str) -> dict:
        """Migrate a Dockerfile using reference patterns"""
        
        # Read target Dockerfile
        target_content = self.file_reader.read_dockerfile(target_dockerfile_path)
        if not target_content:
            return {
                'success': False,
                'error': 'Could not read target Dockerfile'
            }
        
        print(f"\n🤖 Analyzing Dockerfile...")
        print(f"📋 Task: {task}\n")
        
        # Create messages
        messages = [
            {
                "role": "user",
                "content": f"""Task: {task}

Current Dockerfile:
```dockerfile
{target_content}
```

Please migrate this Dockerfile following my custom patterns.
Explain what you're changing and why, then provide the complete updated Dockerfile."""
            }
        ]
        
        try:
            # Call Claude API
            response = self.client.messages.create(
                model=Config.MODEL,
                max_tokens=Config.MAX_TOKENS,
                temperature=Config.TEMPERATURE,
                system=self.create_system_prompt(),
                messages=messages
            )
            
            # Extract response
            response_text = response.content[0].text
            
            return {
                'success': True,
                'response': response_text,
                'original_content': target_content
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f"API Error: {str(e)}"
            }
    
    def extract_dockerfile_from_response(self, response: str) -> str:
        """Extract Dockerfile code from Claude's response"""
        # Look for code blocks with dockerfile or no language specified
        import re
        
        # Try to find dockerfile code block
        pattern = r'```dockerfile\n(.*?)```'
        match = re.search(pattern, response, re.DOTALL)
        
        if match:
            return match.group(1).strip()
        
        # Try generic code block
        pattern = r'```\n(.*?)```'
        match = re.search(pattern, response, re.DOTALL)
        
        if match:
            content = match.group(1).strip()
            # Check if it looks like a Dockerfile
            if content.startswith('FROM '):
                return content
        
        return ""
    
    def interactive_session(self):
        """Run interactive migration session"""
        print("\n" + "="*60)
        print("🐳 Docker Migration Agent")
        print("="*60)
        print("\n📚 Loaded custom patterns:")
        for pattern in self.knowledge.list_patterns():
            print(f"  ✓ {pattern}")
        print("\n")
        
        # Get target Dockerfile
        target = input("📁 Enter Dockerfile path to migrate: ").strip()
        
        # Get task description
        print("\n💡 Examples:")
        print("  - Update to PHP 8.3 and latest NewRelic")
        print("  - Add Gearman support using my standard method")
        print("  - Migrate to multi-stage build with my patterns")
        task = input("\n🎯 What should I do? ").strip()
        
        # Perform migration
        result = self.migrate_dockerfile(target, task)
        
        if not result['success']:
            print(f"\n❌ Migration failed: {result['error']}")
            return
        
        # Display response
        print("\n" + "="*60)
        print("📝 Migration Analysis & Result:")
        print("="*60 + "\n")
        print(result['response'])
        
        # Ask to save
        print("\n" + "="*60)
        save = input("\n💾 Save changes? (y/n): ").strip().lower()
        
        if save == 'y':
            # Create backup first
            self.file_writer.backup_file(target)
            
            # Extract Dockerfile content
            dockerfile_content = self.extract_dockerfile_from_response(result['response'])
            
            if dockerfile_content:
                # Save migrated version
                success = self.file_writer.write_dockerfile(target, dockerfile_content)
                if success:
                    print("\n✅ Migration saved successfully!")
                    print(f"   Original backed up with .backup suffix")
                else:
                    print("\n❌ Failed to save migration")
            else:
                print("\n⚠️  Could not extract Dockerfile from response")
                print("   Please copy manually from the response above")
        else:
            print("\n👍 Changes discarded")
    
    def batch_migrate(self, dockerfile_paths: list, task: str):
        """Migrate multiple Dockerfiles with the same task"""
        print(f"\n🔄 Batch migration: {len(dockerfile_paths)} files")
        print(f"📋 Task: {task}\n")
        
        results = []
        for i, path in enumerate(dockerfile_paths, 1):
            print(f"\n[{i}/{len(dockerfile_paths)}] Processing: {path}")
            result = self.migrate_dockerfile(path, task)
            results.append({'path': path, 'result': result})
            
            if result['success']:
                print("✓ Success")
            else:
                print(f"✗ Failed: {result['error']}")
        
        return results


def main():
    """Main entry point"""
    try:
        agent = DockerMigrationAgent()
        agent.interactive_session()
        
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
    except Exception as e:
        print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    main()
```

## Usage Examples

### Basic Usage

```bash
# Activate virtual environment
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Run the agent
python agent/main.py
```

### Example Session

```
============================================================
🐳 Docker Migration Agent
============================================================

📚 Loaded custom patterns:
  ✓ newrelic
  ✓ supervisor
  ✓ gearman
  ✓ reference_dockerfile


📁 Enter Dockerfile path to migrate: target-repos/payment-api/Dockerfile

💡 Examples:
  - Update to PHP 8.3 and latest NewRelic
  - Add Gearman support using my standard method
  - Migrate to multi-stage build with my patterns

🎯 What should I do? Update to PHP 8.3 and add NewRelic using my pattern

🤖 Analyzing Dockerfile...
📋 Task: Update to PHP 8.3 and add NewRelic using my pattern

============================================================
📝 Migration Analysis & Result:
============================================================

[Claude's detailed analysis and migrated Dockerfile will appear here]

============================================================

💾 Save changes? (y/n): y

✓ Created backup: target-repos/payment-api/Dockerfile.backup
✓ Wrote migrated Dockerfile

✅ Migration saved successfully!
   Original backed up with .backup suffix
```

### Batch Migration (Advanced)

Create `batch_migrate.py`:

```python
from agent.main import DockerMigrationAgent

# List of Dockerfiles to migrate
dockerfiles = [
    "target-repos/api-service/Dockerfile",
    "target-repos/worker-service/Dockerfile",
    "target-repos/scheduler-service/Dockerfile",
]

# Common task for all
task = "Update to PHP 8.3 and ensure NewRelic is installed using standard method"

# Run batch migration
agent = DockerMigrationAgent()
results = agent.batch_migrate(dockerfiles, task)

# Summary
print("\n" + "="*60)
print("📊 Batch Migration Summary")
print("="*60)
for item in results:
    status = "✓" if item['result']['success'] else "✗"
    print(f"{status} {item['path']}")
```

Run:

```bash
python batch_migrate.py
```

## README.md

```markdown
# Docker Migration Agent

AI-powered agent for migrating Dockerfiles using your custom patterns and best practices.

## Features

- 🎯 Learns from your reference Dockerfiles
- 📚 Follows your custom installation patterns (NewRelic, Supervisor, Gearman, etc.)
- 🔄 Maintains consistency across all your infrastructure
- 💾 Automatic backups before migration
- 🤖 Powered by Claude Sonnet 4.5

## Quick Start

1. **Install dependencies**
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Configure**
   ```bash
   cp .env.example .env
   # Add your ANTHROPIC_API_KEY to .env
   ```

3. **Add your reference patterns**
   - Place your reference Dockerfile in `reference-dockerfiles/`
   - Document your patterns in `reference-dockerfiles/patterns/`

4. **Run**
   ```bash
   python agent/main.py
   ```

## Documentation

See pattern files in `reference-dockerfiles/patterns/` for examples of how to document your custom installation methods.

## Safety

- ✅ All operations create backups automatically
- ✅ You review changes before applying
- ✅ Runs 100% locally
- ✅ No production data involved

## License

MIT
```

## Next Steps

1. **Create the directory structure**
2. **Add your actual reference Dockerfile and patterns**
3. **Install dependencies and configure .env**
4. **Test with a non-critical Dockerfile first**
5. **Iterate and refine your patterns**

## Tips for Success

1. **Start small** - Begin with just one pattern (e.g., NewRelic)
2. **Be specific** - Include exact commands, version numbers, and reasons in your patterns
3. **Test incrementally** - Migrate one Dockerfile at a time initially
4. **Review carefully** - Always check the agent's output before applying
5. **Refine patterns** - Update your reference patterns based on migration results

## Troubleshooting

### "ANTHROPIC_API_KEY not set"
- Make sure you've created `.env` file and added your API key

### "Reference directory not found"
- Create `reference-dockerfiles/` directory in project root
- Add at least one pattern or reference Dockerfile

### Agent produces incorrect migrations
- Review and improve your pattern documentation
- Be more specific about version numbers and exact commands
- Add more examples to your reference Dockerfile

## Advanced: Adding New Patterns

To add a new pattern (e.g., Redis):

1. Create `reference-dockerfiles/patterns/redis.md`:

```markdown
# Redis Installation Pattern

## My Standard Approach
1. Install via apt for system Redis
2. Use phpredis extension for PHP
3. Configure persistence and memory limits

## Dockerfile snippet:
```dockerfile
# Install Redis
RUN apt-get update && apt-get install -y redis-server && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Install phpredis extension
RUN pecl install redis-5.3.7 && \
    docker-php-ext-enable redis
```

## Important notes:
- Pin phpredis version
- Configure maxmemory in redis.conf
- Use Unix socket for better performance
```

2. Restart the agent - it will automatically load the new pattern

---

**You're ready to build your Docker Migration Agent! 🚀**