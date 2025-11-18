#!/usr/bin/env python3
"""
Version Bump Script for Tirith

This script automatically bumps the version in all necessary files:
- setup.py
- src/tirith/__init__.py
- CHANGELOG.md

Usage:
    python bump_version.py <new_version> [--change-type TYPE] [--description DESC]

Examples:
    python bump_version.py 1.0.5 --change-type Fixed --description "Bug fix for provider"
    python bump_version.py 1.1.0 --change-type Added --description "New feature"

"""

import re
import sys
import argparse
from datetime import date
from pathlib import Path


class VersionBumper:
    def __init__(self, root_dir=None):
        # If no root_dir provided, use parent directory of the script (project root)
        self.root_dir = Path(root_dir) if root_dir else Path(__file__).parent.parent
        self.setup_py = self.root_dir / "setup.py"
        self.init_py = self.root_dir / "src" / "tirith" / "__init__.py"
        self.changelog = self.root_dir / "CHANGELOG.md"

    def get_current_version(self):
        """Extract current version from setup.py"""
        content = self.setup_py.read_text()
        match = re.search(r'version="([^"]+)"', content)
        if match:
            return match.group(1)
        raise ValueError("Could not find version in setup.py")

    def validate_version(self, version):
        """Validate version format (semantic versioning)"""
        pattern = r"^\d+\.\d+\.\d+(-[a-zA-Z0-9.]+)?$"
        if not re.match(pattern, version):
            raise ValueError(f"Invalid version format: {version}. Expected format: X.Y.Z or X.Y.Z-beta.N")
        return True

    def update_setup_py(self, new_version):
        """Update version in setup.py"""
        content = self.setup_py.read_text()
        updated = re.sub(r'version="[^"]+"', f'version="{new_version}"', content)
        self.setup_py.write_text(updated)
        print(f"✓ Updated {self.setup_py.relative_to(self.root_dir)}")

    def update_init_py(self, new_version):
        """Update version in src/tirith/__init__.py"""
        content = self.init_py.read_text()
        updated = re.sub(r'__version__ = "[^"]+"', f'__version__ = "{new_version}"', content)
        self.init_py.write_text(updated)
        print(f"✓ Updated {self.init_py.relative_to(self.root_dir)}")

    def update_changelog(self, new_version, change_type=None, description=None):
        """Add new version entry to CHANGELOG.md"""
        content = self.changelog.read_text()
        today = date.today().strftime("%Y-%m-%d")

        # Find the position after the header
        header_end = content.find("## [")
        if header_end == -1:
            raise ValueError("Could not find version entries in CHANGELOG.md")

        # Create new version entry
        new_entry = f"\n## [{new_version}] - {today}\n\n"

        if change_type and description:
            new_entry += f"### {change_type}\n- {description}\n"
        else:
            new_entry += "### Changed\n- Version bump\n"

        # Insert the new entry
        updated = content[:header_end] + new_entry + "\n" + content[header_end:]
        self.changelog.write_text(updated)
        print(f"✓ Updated {self.changelog.relative_to(self.root_dir)}")

    def bump_version(self, new_version, change_type=None, description=None):
        """Bump version in all files"""
        # Validate version format
        self.validate_version(new_version)

        # Get current version
        current_version = self.get_current_version()
        print(f"Current version: {current_version}")
        print(f"New version: {new_version}\n")

        # Update all files
        self.update_setup_py(new_version)
        self.update_init_py(new_version)
        self.update_changelog(new_version, change_type, description)

        print(f"\n✓ Successfully bumped version from {current_version} to {new_version}")
        print("\nNext steps:")
        print("1. Review the changes")
        print("2. Commit with: git add -A && git commit -m 'Bump version'")
        print("3. Create a tag: git tag -a v{} -m 'Release v{}'".format(new_version, new_version))
        print("4. Push: git push && git push --tags")


def main():
    parser = argparse.ArgumentParser(
        description="Bump version for Tirith project",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s 1.0.5
  %(prog)s 1.0.5 --change-type Fixed --description "Bug fix for provider"
  %(prog)s 1.1.0 --change-type Added --description "New feature X"
  %(prog)s 2.0.0-beta.1 --change-type Added --description "Beta release"

Change types:
  Added, Changed, Deprecated, Removed, Fixed, Security
        """,
    )

    parser.add_argument("version", help="New version number (e.g., 1.0.5, 1.1.0, 2.0.0-beta.1)")

    parser.add_argument(
        "--change-type",
        "-t",
        choices=["Added", "Changed", "Deprecated", "Removed", "Fixed", "Security"],
        help="Type of change (for CHANGELOG.md)",
    )

    parser.add_argument("--description", "-d", help="Description of changes (for CHANGELOG.md)")

    args = parser.parse_args()

    # If one of change-type or description is provided, both must be provided
    if (args.change_type or args.description) and not (args.change_type and args.description):
        parser.error("--change-type and --description must be used together")

    try:
        bumper = VersionBumper()
        bumper.bump_version(args.version, args.change_type, args.description)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
