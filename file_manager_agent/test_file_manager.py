"""
test_file_manager.py
Automated test suite for Orion's File Manager Agent.
"""

import sys
import os
import shutil
import tempfile
import time

# Enable UTF-8 encoding on Windows console
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

try:
    import file_manager_agent as fm
    import file_ops
    import config
except ImportError:
    from . import file_manager_agent as fm
    from . import file_ops
    from . import config


def run_tests():
    print("==================================================")
    print("Testing Orion File Manager Agent")
    print("==================================================")

    temp_dir = tempfile.mkdtemp(prefix="orion_test_fm_")
    print(f"\n[Environment] Created isolated test sandbox: {temp_dir}")

    try:
        # Create mock file structure
        # 1. Documents
        with open(os.path.join(temp_dir, "report.txt"), "w", encoding="utf-8") as f:
            f.write("Annual sales report and financial breakdown.\nTotal revenue: $1,000,000.\nTarget met.")
        with open(os.path.join(temp_dir, "invoice.pdf"), "w", encoding="utf-8") as f:
            f.write("%PDF-1.4 Mock invoice content")

        # 2. Images & Code
        with open(os.path.join(temp_dir, "logo.png"), "wb") as f:
            f.write(b"PNG_MOCK_BYTES_12345")
        with open(os.path.join(temp_dir, "script.py"), "w", encoding="utf-8") as f:
            f.write("print('Hello from Orion!')\n")

        # 3. Duplicate files (exact same content)
        with open(os.path.join(temp_dir, "duplicate_original.dat"), "wb") as f:
            f.write(b"EXACT_SAME_DATA_PADDING_" * 50)
        with open(os.path.join(temp_dir, "duplicate_copy.dat"), "wb") as f:
            f.write(b"EXACT_SAME_DATA_PADDING_" * 50)

        # Test [1] Search Files
        print("\n[1] Testing File Search:")
        results = fm.search("*.txt", root=temp_dir)
        print(f"   ✓ Search '*.txt' found {len(results)} file(s): {[r['name'] for r in results]}")
        assert any(r["name"] == "report.txt" for r in results)

        # Test [2] Folder Summary & Category Breakdown
        print("\n[2] Testing Folder Summary & Smart Categories:")
        summary = fm.folder_summary(temp_dir)
        print(f"   ✓ Total Files: {summary['file_count']}, Total Size: {summary['total_size_mb']} MB")
        print(f"   ✓ Categories: {summary['by_category']}")
        assert summary["file_count"] >= 5
        assert "Documents" in summary["by_category"]

        # Test [3] File Summarizer / Inspector
        print("\n[3] Testing File Summarization (Offline & Fast)::")
        sum_text = fm.summarize_file(os.path.join(temp_dir, "report.txt"), force_offline=True)
        print(f"   ✓ Summary generated successfully:\n{sum_text}")
        assert "report.txt" in sum_text

        # Test [4] Duplicate Detection
        print("\n[4] Testing MD5 Duplicate File Detection:")
        dup_res = fm.duplicates(temp_dir)
        print(f"   ✓ Duplicate sets found: {dup_res['group_count']} ({dup_res['total_wasted_mb']} MB wasted)")
        assert dup_res["group_count"] >= 1
        assert len(dup_res["groups"][0]["files"]) == 2

        # Test [5] Zip & Unzip
        print("\n[5] Testing Zip Compression & Archive Extraction:")
        zip_out = os.path.join(temp_dir, "archive.zip")
        z_res = fm.zip_folder(temp_dir, output_zip=zip_out)
        print(f"   ✓ Zip created: {z_res['message']}")
        assert os.path.exists(zip_out)

        extract_folder = os.path.join(temp_dir, "extracted")
        uz_res = fm.unzip_archive(zip_out, extract_to=extract_folder)
        print(f"   ✓ Unzip extracted: {uz_res['message']}")
        assert os.path.exists(extract_folder)

        # Test [6] Smart Folder Cleaner / Organizer
        print("\n[6] Testing Smart Folder Cleaner:")
        clean_res = fm.clean_folder(temp_dir, confirm=True)
        print(f"   ✓ Clean result: {clean_res['message']}")
        # Check that categorized folders were created
        assert os.path.exists(os.path.join(temp_dir, "Documents"))
        assert os.path.exists(os.path.join(temp_dir, "Images"))
        assert os.path.exists(os.path.join(temp_dir, "Code"))

        # Test [7] Recently Modified Tracker
        print("\n[7] Testing Recently Modified File Tracker:")
        recent = fm.recent_files(temp_dir, hours=1)
        print(f"   ✓ Recent files found: {len(recent)}")
        assert len(recent) > 0

        # Test [8] NLP Command Parser
        print("\n[8] Testing Offline NLP Command Parser:")
        test_commands = [
            ("clean desktop", "clean_folder"),
            ("clean downloads", "clean_folder"),
            ("find duplicates", "duplicates"),
            ("clean duplicates", "reclaim_duplicates"),
            ("large files", "large_files"),
            ("recent files", "recent_files"),
            ("search *.py", "search"),
            ("zip my_project", "zip"),
            ("unzip archive.zip", "unzip"),
            ("rename old.txt to new.txt", "rename"),
            ("move data.csv to archive", "move"),
            ("delete temp.log", "delete"),
            ("delete all file's in download", "empty_folder"),
            ("empty downloads", "empty_folder"),
            ("create folder named images in pictures", "create_folder"),
            ("make a folder projects in desktop", "create_folder"),
            ("create file notes.txt in desktop", "create_file"),
            ("copy report.txt to backup", "copy"),
            ("open folder downloads", "open_explorer"),
            ("open a screen shot from D:\\OneDrive\\Pictures", "open_file"),
            ("open a scrrn shot from pictures", "open_file"),
            ("view report.txt", "open_file"),
            ("show files in pictures", "search"),
            ("summary .", "folder_summary"),
            ("inspect report.txt", "summarize_file")
        ]




        for cmd, expected_act in test_commands:
            parsed = fm.parse_command(cmd)
            act = parsed.get("action")
            assert act == expected_act, f"For '{cmd}', expected '{expected_act}', got '{act}'"
            print(f"   ✓ '{cmd}' -> action '{act}'")

        print("\n==================================================")
        print(" ALL TESTS PASSED SUCCESSFULLY! (100% Zero Error)")
        print("==================================================")

    finally:
        # Cleanup temp directory
        try:
            shutil.rmtree(temp_dir, ignore_errors=True)
        except Exception:
            pass


if __name__ == "__main__":
    run_tests()
