from __future__ import annotations

import ast
import struct
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent


class WindowsPackagingTests(unittest.TestCase):
    def test_icon_contains_multiple_windows_sizes(self) -> None:
        icon = (PROJECT_ROOT / "assets" / "app_icon.ico").read_bytes()
        reserved, icon_type, count = struct.unpack("<HHH", icon[:6])
        self.assertEqual(reserved, 0)
        self.assertEqual(icon_type, 1)
        self.assertEqual(count, 7)

    def test_version_resource_is_valid_python_expression(self) -> None:
        version_file = PROJECT_ROOT / "windows_version_info.txt"
        ast.parse(version_file.read_text(encoding="utf-8"), filename=str(version_file))
        self.assertIn("1.1.0", version_file.read_text(encoding="utf-8"))

    def test_installer_references_built_executable(self) -> None:
        script = (PROJECT_ROOT / "installer" / "NOK_Product_Insight.iss").read_text(
            encoding="utf-8"
        )
        self.assertIn('Source: "..\\dist\\{#MyAppExeName}"', script)
        self.assertIn("NOK_Product_Insight_Setup_v1.1.0_x64", script)
        self.assertIn("UninstallDisplayIcon", script)


if __name__ == "__main__":
    unittest.main()
