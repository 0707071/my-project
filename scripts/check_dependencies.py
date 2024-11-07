import pkg_resources
import sys

def check_dependencies():
    """Проверяет все зависимости на точное соответствие версий."""
    with open('requirements.txt') as f:
        requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]
    
    try:
        pkg_resources.require(requirements)
        print("✅ All dependencies are correct!")
        return True
    except pkg_resources.VersionConflict as e:
        print(f"❌ Version conflict: {e}")
        return False
    except pkg_resources.DistributionNotFound as e:
        print(f"❌ Package not found: {e}")
        return False

if __name__ == '__main__':
    sys.exit(0 if check_dependencies() else 1) 