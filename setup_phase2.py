#!/usr/bin/env python3
"""
Phase 2 Setup Script: LM Studio SDK + Enhanced Completion

Automated setup for NEAR Catalyst Framework Phase 2 migration.
Installs dependencies, configures environment, and validates setup.

Usage:
    python setup_phase2.py [--install-deps] [--configure-env] [--validate-setup]
"""

import subprocess
import sys
import os
import platform
import requests
import time
from pathlib import Path


class Phase2Setup:
    """
    Automated setup for Phase 2 LM Studio SDK integration
    """
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.requirements_file = self.project_root / "requirements.txt"
        self.env_file = self.project_root / ".env"
        self.env_example_file = self.project_root / ".env.example"
        
        print("🚀 NEAR Catalyst Framework - Phase 2 Setup")
        print("=" * 50)
        print("Setting up LM Studio SDK + Enhanced Completion...")
    
    def run_full_setup(self):
        """Run the complete Phase 2 setup process"""
        try:
            # Step 1: Install Python dependencies
            print("\n1️⃣ Installing Python Dependencies...")
            self.install_python_dependencies()
            
            # Step 2: Configure environment
            print("\n2️⃣ Configuring Environment...")
            self.configure_environment()
            
            # Step 3: Check LM Studio availability
            print("\n3️⃣ Checking LM Studio Setup...")
            self.check_lm_studio_setup()
            
            # Step 4: Validate installation
            print("\n4️⃣ Validating Setup...")
            self.validate_setup()
            
            # Step 5: Show next steps
            print("\n5️⃣ Next Steps...")
            self.show_next_steps()
            
            print("\n✅ Phase 2 setup completed successfully!")
            
        except Exception as e:
            print(f"\n❌ Setup failed: {e}")
            sys.exit(1)
    
    def install_python_dependencies(self):
        """Install Python dependencies for Phase 2"""
        try:
            # Check if we're in a virtual environment
            in_venv = (hasattr(sys, 'real_prefix') or 
                      (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix))
            
            if not in_venv:
                print("   ⚠️  Warning: Not in a virtual environment")
                print("   Consider running: python -m venv venv && source venv/bin/activate")
            
            # Install requirements
            if self.requirements_file.exists():
                print("   📦 Installing dependencies from requirements.txt...")
                result = subprocess.run([
                    sys.executable, "-m", "pip", "install", "-r", str(self.requirements_file)
                ], capture_output=True, text=True)
                
                if result.returncode != 0:
                    print(f"   ❌ Failed to install dependencies: {result.stderr}")
                    raise Exception("pip install failed")
                
                print("   ✅ Python dependencies installed successfully")
            else:
                print("   ❌ requirements.txt not found")
                raise Exception("requirements.txt missing")
                
        except Exception as e:
            print(f"   ❌ Python dependency installation failed: {e}")
            raise
    
    def configure_environment(self):
        """Configure environment variables for Phase 2"""
        try:
            # Create .env from .env.example if it doesn't exist
            if not self.env_file.exists() and self.env_example_file.exists():
                print("   📝 Creating .env from .env.example...")
                self.env_file.write_text(self.env_example_file.read_text())
                print("   ✅ .env file created")
            elif self.env_file.exists():
                print("   ℹ️  .env file already exists")
            else:
                print("   ⚠️  Neither .env nor .env.example found")
                print("   Creating basic .env file...")
                self.create_basic_env_file()
            
            # Verify key environment variables
            print("   🔍 Checking environment configuration...")
            self.verify_env_variables()
            
        except Exception as e:
            print(f"   ❌ Environment configuration failed: {e}")
            raise
    
    def create_basic_env_file(self):
        """Create a basic .env file with Phase 2 settings"""
        basic_env_content = """# NEAR Partnership Analysis - Environment Configuration

# OpenAI API Configuration (Phase 1)
OPENAI_API_KEY=your_openai_key_here

# Phase 2: LM Studio Python SDK Configuration
LM_STUDIO_API_BASE=http://localhost:1234/v1
LM_STUDIO_API_KEY=local-key
USE_LOCAL_MODELS=false
USE_LMSTUDIO_SDK=true
ENABLE_WEB_SEARCH=false

# Phase 3: Deep Research Enhancement 
USE_DEEP_RESEARCH_REPLACEMENT=false
TAVILY_API_KEY=your_tavily_key_here

# Environment Detection
REASONING_ENV=production
FLASK_ENV=development
DEBUG=False
"""
        self.env_file.write_text(basic_env_content)
        print("   ✅ Basic .env file created")
    
    def verify_env_variables(self):
        """Verify that key environment variables are present"""
        from dotenv import load_dotenv
        load_dotenv()
        
                         required_vars = [
            'LM_STUDIO_API_BASE',
            'LM_STUDIO_API_KEY', 
            'USE_LOCAL_MODELS',
            'USE_LMSTUDIO_SDK',
            'USE_REMOTE_LMSTUDIO'
        ]
        
        missing_vars = []
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            print(f"   ⚠️  Missing environment variables: {', '.join(missing_vars)}")
            print("   Please update your .env file")
        else:
            print("   ✅ Environment variables configured")
    
    def check_lm_studio_setup(self):
        """Check LM Studio installation and setup (local or remote)"""
        try:
            from dotenv import load_dotenv
            load_dotenv()
            
            # Check if using remote LM Studio
            use_remote = os.getenv('USE_REMOTE_LMSTUDIO', 'false').lower() == 'true'
            
            if use_remote:
                print("   🌐 Checking remote LM Studio server configuration...")
                self._check_remote_lm_studio()
            else:
                print("   🏠 Checking local LM Studio setup...")
                self._check_local_lm_studio()
                
        except Exception as e:
            print(f"   ❌ LM Studio setup check failed: {e}")
    
    def _check_remote_lm_studio(self):
        """Check remote LM Studio server"""
        remote_url = os.getenv('REMOTE_LMSTUDIO_URL', 'http://your-server:1234/v1')
        remote_key = os.getenv('REMOTE_LMSTUDIO_API_KEY', 'your-remote-key')
        
        if 'your-server' in remote_url or 'your-remote-key' in remote_key:
            print("   ⚠️  Remote LM Studio configuration not set")
            print("   Please update REMOTE_LMSTUDIO_URL and REMOTE_LMSTUDIO_API_KEY in .env")
            return
        
        # Test connection to remote server
        try:
            test_url = remote_url.replace('/v1', '/v1/models')
            headers = {'Authorization': f'Bearer {remote_key}'} if remote_key != 'local-key' else {}
            
            response = requests.get(test_url, headers=headers, timeout=10)
            if response.status_code == 200:
                models = response.json().get('data', [])
                print(f"   ✅ Remote LM Studio server accessible")
                print(f"   📊 {len(models)} models available on remote server")
                print(f"   🌐 URL: {remote_url}")
            else:
                print(f"   ❌ Remote server responded with status {response.status_code}")
        except requests.RequestException as e:
            print(f"   ❌ Cannot connect to remote LM Studio server: {e}")
            print(f"   🌐 Attempted URL: {remote_url}")
    
    def _check_local_lm_studio(self):
        """Check local LM Studio installation"""
        # Check if LM Studio Python SDK is available
        try:
            import lmstudio
            print("   ✅ LM Studio Python SDK available")
            sdk_available = True
        except ImportError:
            print("   ❌ LM Studio Python SDK not available")
            print("   Install with: pip install lmstudio")
            sdk_available = False
        
        # Check if LM Studio CLI is available
        try:
            result = subprocess.run(['lms', '--help'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                print("   ✅ LM Studio CLI available")
                cli_available = True
            else:
                print("   ❌ LM Studio CLI not working properly")
                cli_available = False
        except (subprocess.TimeoutExpired, FileNotFoundError):
            print("   ⚠️  LM Studio CLI not found in PATH")
            print("   Install from: https://lmstudio.ai/download")
            cli_available = False
        
        # Check if LM Studio server is running
        try:
            response = requests.get("http://localhost:1234/v1/models", timeout=5)
            if response.status_code == 200:
                print("   ✅ LM Studio server is running")
                models = response.json().get('data', [])
                print(f"   📊 {len(models)} models available")
                server_running = True
            else:
                print("   ⚠️  LM Studio server responded with error")
                server_running = False
        except requests.RequestException:
            print("   ⚠️  LM Studio server not running")
            print("   Start with: lms server start")
            server_running = False
        
        # Summary
        if sdk_available and cli_available and server_running:
            print("   🎉 Local LM Studio setup is complete!")
        elif sdk_available and cli_available:
            print("   ⚠️  LM Studio ready, but server needs to be started")
            print("   Run: lms server start")
        else:
            print("   ❌ Local LM Studio setup incomplete")
            self.show_lm_studio_install_instructions()
    
    def show_lm_studio_install_instructions(self):
        """Show LM Studio installation instructions"""
        print("\n   📋 LM Studio Installation Instructions:")
        
        system = platform.system().lower()
        
        if system == "darwin":  # macOS
            print("   • macOS: brew install --cask lm-studio")
        elif system == "linux":
            print("   • Linux: Download AppImage from https://lmstudio.ai/download")
        elif system == "windows":
            print("   • Windows: Download installer from https://lmstudio.ai/download")
        else:
            print("   • Download from: https://lmstudio.ai/download")
        
        print("   • After installation, install CLI: npx lmstudio install-cli")
        print("   • Start server: lms server start")
        print("   • Install SDK: pip install lmstudio")
    
    def validate_setup(self):
        """Validate the Phase 2 setup"""
        try:
            print("   🔍 Running validation tests...")
            
            # Test 1: Import key modules
            try:
                from agents.model_manager import get_model_manager
                from agents.enhanced_completion import get_enhanced_completion
                print("   ✅ Phase 2 modules import successfully")
            except ImportError as e:
                print(f"   ❌ Module import failed: {e}")
                return False
            
            # Test 2: Initialize components
            try:
                model_manager = get_model_manager()
                completion_handler = get_enhanced_completion()
                print("   ✅ Phase 2 components initialize successfully")
            except Exception as e:
                print(f"   ❌ Component initialization failed: {e}")
                return False
            
            # Test 3: Check configuration
            try:
                from config.config import LITELLM_CONFIG, LMSTUDIO_CONFIG
                if LITELLM_CONFIG and LMSTUDIO_CONFIG:
                    print("   ✅ Phase 2 configuration loaded successfully")
                else:
                    print("   ❌ Phase 2 configuration missing")
                    return False
            except Exception as e:
                print(f"   ❌ Configuration validation failed: {e}")
                return False
            
            print("   🎉 All validation tests passed!")
            return True
            
        except Exception as e:
            print(f"   ❌ Validation failed: {e}")
            return False
    
    def show_next_steps(self):
        """Show next steps after setup"""
        print("   📋 Next Steps:")
        print("   ")
        print("   1. 🔑 Configure your OpenAI API key in .env:")
        print("      OPENAI_API_KEY=your_actual_key_here")
        print("   ")
        print("   2. Choose your LM Studio setup:")
        print("      🏠 Local Setup (requires GPU):")
        print("         • Start server: lms server start")
        print("         • Download models: lms get qwen2.5-72b-instruct")
        print("         • Download models: lms get deepseek-r1-distill-qwen-32b")
        print("   ")
        print("      🌐 Remote Setup (use another server's GPU):")
        print("         • Set USE_REMOTE_LMSTUDIO=true in .env")
        print("         • Set REMOTE_LMSTUDIO_URL=http://your-server:1234/v1")
        print("         • Set REMOTE_LMSTUDIO_API_KEY=your-key (if needed)")
        print("   ")
        print("   3. 🧪 Test the integration:")
        print("      python test_phase2_integration.py --verbose")
        print("   ")
        print("   4. 🔄 Enable local models when ready:")
        print("      Set USE_LOCAL_MODELS=true in .env")
        print("   ")
        print("   5. 🎯 Run your agents:")
        print("      python analyze_projects_multi_agent_v2.py")


def main():
    """Main setup function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Phase 2 Setup Script')
    parser.add_argument('--install-deps', action='store_true', 
                       help='Only install Python dependencies')
    parser.add_argument('--configure-env', action='store_true', 
                       help='Only configure environment')
    parser.add_argument('--validate-setup', action='store_true', 
                       help='Only validate existing setup')
    
    args = parser.parse_args()
    
    setup = Phase2Setup()
    
    try:
        if args.install_deps:
            setup.install_python_dependencies()
        elif args.configure_env:
            setup.configure_environment()
        elif args.validate_setup:
            setup.validate_setup()
        else:
            # Run full setup
            setup.run_full_setup()
            
    except KeyboardInterrupt:
        print("\n\n⏹️ Setup interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()