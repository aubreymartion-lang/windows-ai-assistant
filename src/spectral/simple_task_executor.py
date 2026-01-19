"""
Simple task executor module for immediate task execution.

Handles simple, immediate tasks without involving the coding AI or complex execution system.
These are tasks that can be completed quickly and should return results in the same response.
"""

import logging
import os
import platform
import subprocess
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class SimpleTaskExecutor:
    """
    Execute simple, immediate tasks without involving coding AI.

    This executor handles common, quick operations like listing files,
    getting IP addresses, running simple commands, etc. These tasks
    should complete quickly and return results directly in the chat response.
    """

    def __init__(self) -> None:
        """Initialize the simple task executor."""
        # Simple task patterns
        self.ip_address_patterns = ["ip", "ipconfig", "address", "network", "wifi", "connection"]
        self.list_files_patterns = ["list", "files", "folder", "directory", "show me"]
        self.read_file_patterns = ["read", "open", "show", "display", "view"]
        self.run_command_patterns = ["run", "execute", "command"]

        logger.info("SimpleTaskExecutor initialized")

    def can_handle(self, user_input: str) -> bool:
        """
        Check if this is a simple task we can handle immediately.

        Args:
            user_input: User's input string

        Returns:
            True if this matches simple task patterns
        """
        user_lower = user_input.lower()

        # Check if this is a simple query (not a complex code request)
        # Exclude code-related keywords that indicate complex tasks
        complex_keywords = [
            "write",
            "create",
            "generate",
            "build",
            "program",
            "app",
            "application",
            "script",
            "code",
            "develop",
            "implement",
        ]

        if any(keyword in user_lower for keyword in complex_keywords):
            return False

        # Check for IP address queries
        if self._matches_pattern(user_input, self.ip_address_patterns):
            return True

        # Check for list files queries
        if self._matches_pattern(user_input, self.list_files_patterns):
            # Must mention a folder (desktop, downloads, documents)
            if any(folder in user_lower for folder in ["desktop", "downloads", "documents"]):
                return True

        # Check for read file queries
        if self._matches_pattern(user_input, self.read_file_patterns):
            # Either has "file" keyword OR looks like a file path (has extension)
            if "file" in user_lower or self._detect_file_path(user_input):
                return True

        return False

    def _detect_file_path(self, user_input: str) -> bool:
        """
        Detect if user input contains a file path.

        Args:
            user_input: User's input string

        Returns:
            True if file path detected
        """
        # Look for file extensions
        import re

        # Pattern: path/to/file.ext or file.ext
        # Common extensions
        extensions = [
            r"\.(txt|md|py|js|html|css|json|xml|csv|log|yaml|yml|ini|cfg|conf)",
            r"\.(pdf|doc|docx|xls|xlsx|ppt|pptx)",
            r"\.(jpg|jpeg|png|gif|bmp|svg|ico)",
            r"\.(mp3|mp4|avi|mov|wav|flac)",
            r"\.(zip|tar|gz|rar|7z)",
        ]

        user_lower = user_input.lower()

        for ext_pattern in extensions:
            if re.search(ext_pattern, user_lower):
                return True

        return False

    def execute(self, user_input: str) -> Optional[str]:
        """
        Execute the simple task and return result.

        Args:
            user_input: User's input string

        Returns:
            Execution result string or None if task not handled
        """
        logger.info(f"Attempting to execute simple task: {user_input}")

        user_lower = user_input.lower()

        # IP address patterns
        if self._matches_pattern(user_input, self.ip_address_patterns):
            result = self._get_ip_address()
            if result and "error" not in result.lower():
                return result

        # List files patterns
        if self._matches_pattern(user_input, self.list_files_patterns):
            result = self._list_files(user_input)
            if result and "not found" not in result.lower():
                return result

        # Read file patterns
        if self._matches_pattern(user_input, self.read_file_patterns):
            if "file" in user_lower or self._detect_file_path(user_input):
                result = self._read_file(user_input)
                if result and "please provide" not in result.lower():
                    return result

        # Run command patterns
        if self._matches_pattern(user_input, self.run_command_patterns):
            result = self._run_command(user_input)
            if result:
                return result

        return None

    def _get_ip_address(self) -> Optional[str]:
        """
        Get local IP address by running appropriate command for the OS.

        Returns:
            IP address string or None if error
        """
        try:
            system = platform.system()

            if system == "Windows":
                # Use ipconfig on Windows
                result = subprocess.run(
                    ["ipconfig"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                    check=False,
                )
                output = result.stdout

                # Parse and extract IPv4 addresses
                lines = output.split("\n")
                ips = []
                for i, line in enumerate(lines):
                    if "IPv4 Address" in line:
                        ip = line.split(":")[-1].strip()
                        if ip:
                            ips.append(ip)

                if ips:
                    if len(ips) == 1:
                        return f"Your IP address is: {ips[0]}"
                    ip_list = "\n".join(f"- {ip}" for ip in ips)
                    return f"Your IP addresses:\n{ip_list}"

            elif system == "Linux" or system == "Darwin":
                # Use ifconfig or ip addr on Linux/Mac
                result = subprocess.run(
                    ["ip", "addr", "show"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                    check=False,
                )
                output = result.stdout

                # Parse IPv4 addresses
                import re

                ip_pattern = r"inet (\d+\.\d+\.\d+\.\d+)"
                ips = re.findall(ip_pattern, output)
                # Filter out loopback
                ips = [ip for ip in ips if not ip.startswith("127.")]

                if ips:
                    if len(ips) == 1:
                        return f"Your IP address is: {ips[0]}"
                    ip_list = "\n".join(f"- {ip}" for ip in ips)
                    return f"Your IP addresses:\n{ip_list}"

            return None

        except subprocess.TimeoutExpired:
            logger.warning("IP address lookup timed out")
            return None
        except Exception as e:
            logger.warning(f"Error getting IP address: {e}")
            return None

    def _list_files(self, user_input: str) -> Optional[str]:
        """
        List files from a folder (Desktop, Downloads, or custom path).

        Args:
            user_input: User's input string

        Returns:
            File list string or None if folder not found
        """
        try:
            # Determine which folder
            user_lower = user_input.lower()

            home = str(Path.home())

            folder = None
            folder_name = None

            if "desktop" in user_lower:
                folder = os.path.join(home, "Desktop")
                folder_name = "Desktop"
            elif "downloads" in user_lower:
                folder = os.path.join(home, "Downloads")
                folder_name = "Downloads"
            elif "documents" in user_lower:
                folder = os.path.join(home, "Documents")
                folder_name = "Documents"

            if not folder or not os.path.exists(folder):
                return None

            files = os.listdir(folder)

            # Sort files: directories first, then files
            dirs = []
            regular_files = []

            for f in files:
                full_path = os.path.join(folder, f)
                if os.path.isdir(full_path):
                    dirs.append(f + "/")
                else:
                    regular_files.append(f)

            sorted_files = sorted(dirs) + sorted(regular_files)

            if not sorted_files:
                return f"The {folder_name} folder is empty."

            file_list = "\n".join(f"  - {f}" for f in sorted_files)
            return f"Files in {folder_name}:\n{file_list}"

        except PermissionError:
            logger.warning("Permission denied listing files")
            return None
        except Exception as e:
            logger.warning(f"Error listing files: {e}")
            return None

    def _read_file(self, user_input: str) -> Optional[str]:
        """
        Read and display file contents.

        Args:
            user_input: User's input string

        Returns:
            File contents string or None if file not found
        """
        try:
            # Try to extract file path from user input
            # Look for quoted paths or paths with extensions
            import re

            file_path = None

            # Pattern for quoted paths (both single and double quotes)
            quoted_path = re.search(r'["\']([^"\']+)["\']', user_input)
            if quoted_path:
                file_path = quoted_path.group(1)
            else:
                # Try to find path with extension - look at end of string or after keywords
                # Pattern: file.ext or path/to/file.ext
                path_patterns = [
                    r"(?:show|read|open|display|view)\s+(?:the\s+)?(?:file\s+)?([/\w\-./]+\.\w+)",
                    r"([/\w\-./]+\.\w+)$",  # At end of string
                ]

                for pattern in path_patterns:
                    path_match = re.search(pattern, user_input, re.IGNORECASE)
                    if path_match:
                        file_path = path_match.group(1)
                        break

            if not file_path:
                return None

            # Expand user home directory if present
            if file_path.startswith("~"):
                file_path = os.path.expanduser(file_path)

            # Check if file exists
            if not os.path.exists(file_path):
                return None

            # Read file content (limit to avoid huge outputs)
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            # Limit content length
            max_length = 2000
            if len(content) > max_length:
                content = (
                    content[:max_length]
                    + f"\n... (truncated, showing first {max_length} characters)"
                )

            return f"Contents of {os.path.basename(file_path)}:\n{content}"

        except UnicodeDecodeError:
            logger.warning("Binary file or encoding issue")
            return None
        except Exception as e:
            logger.warning(f"Error reading file: {e}")
            return None

    def _run_command(self, user_input: str) -> Optional[str]:
        """
        Execute a simple shell/terminal command.

        Args:
            user_input: User's input string

        Returns:
            Command output or None if command extraction failed
        """
        try:
            # Extract command from input
            # Look for patterns like "run <command>" or "execute <command>"
            user_lower = user_input.lower()

            # Find where the command starts
            cmd_start = None
            for marker in ["run ", "execute ", "command "]:
                idx = user_lower.find(marker)
                if idx != -1:
                    cmd_start = idx + len(marker)
                    break

            if cmd_start is None:
                return None

            # Extract command
            command = user_input[cmd_start:].strip()

            if not command:
                return None

            # Safety check: only allow simple, safe commands
            dangerous_commands = ["rm", "del", "format", "shutdown", "reboot"]
            for dangerous in dangerous_commands:
                if dangerous in command.lower():
                    logger.warning(f"Blocked potentially dangerous command: {command}")
                    return None

            # Execute command
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )

            output = result.stdout or result.stderr

            # Limit output length
            max_length = 1000
            if len(output) > max_length:
                output = (
                    output[:max_length]
                    + f"\n... (truncated, showing first {max_length} characters)"
                )

            return output if output.strip() else "Command executed successfully (no output)"

        except subprocess.TimeoutExpired:
            logger.warning("Command execution timed out")
            return None
        except Exception as e:
            logger.warning(f"Error running command: {e}")
            return None

    def _matches_pattern(self, user_input: str, keywords: list) -> bool:
        """
        Check if user input contains any of the keywords.

        Args:
            user_input: User's input string
            keywords: List of keywords to match

        Returns:
            True if any keyword matches
        """
        user_lower = user_input.lower()
        return any(keyword in user_lower for keyword in keywords)
