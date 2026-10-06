# 📁 Orion File Manager & Workspace Organizer Agent

A high-performance file management, disk cleaning, and workspace organization agent for Orion.

---

## 🚀 Key Features

1. **🧹 Smart Desktop & Downloads Auto-Cleaner**
   - Automatically categorizes and moves loose clutter files into clean subdirectories (`Documents/`, `Images/`, `Code/`, `Archives/`, `Media/`, `Installers/`).
   - Example: `clean desktop`, `clean downloads`, `clean workspace`.

2. **🔍 MD5 Duplicate File Detector & Space Reclaimer**
   - Rapid hash-based byte comparison to find exact duplicate files wasting disk space.
   - Example: `find duplicates`, `clean duplicates`.

3. **📊 Heavy Files & Storage Hog Detector**
   - Scans directory tree to find the top space-consuming files (>10MB / >100MB).
   - Example: `large files`, `find files > 500MB`.

4. **⚡ Smart Batch File Renamer**
   - Safe multi-file renaming with prefix, suffix, and substring replacement with a dry-run preview.
   - Example: `rename old.txt to new.txt`, `batch rename`.

5. **📦 Zip Compression & Archive Extraction**
   - Instantly create `.zip` archives or extract files into dedicated directories.
   - Example: `zip my_project`, `unzip archive.zip`.

6. **🕒 Recently Modified File Tracker**
   - Find files modified within the last N hours.
   - Example: `recent files`, `what changed today?`.

7. **📑 Deep Text File Inspection & Summary**
   - Structural line, word count, and content preview for code, markdown, logs, and text files.
   - Example: `inspect report.txt`, `summarize notes.md`.

---

## 💻 Natural Language Command Examples

| Category | Example Commands |
|---|---|
| **Clean & Organize** | `clean desktop`, `clean downloads`, `clean <folder_name>` |
| **Duplicates** | `find duplicates`, `clean duplicates`, `reclaim duplicate space` |
| **Large Files** | `large files`, `big files`, `find files larger than 50MB` |
| **Recent Activity** | `recent files`, `what changed today?`, `recent 12 hours` |
| **Search Files** | `search *.pdf`, `find invoice*`, `search *.py` |
| **Archive Tools** | `zip <folder>`, `unzip <archive.zip>` |
| **Inspect File** | `inspect <file.txt>`, `summarize <notes.md>` |
| **File Operations** | `rename <old> to <new>`, `move <src> to <dest>`, `delete <file>` |
| **Workspace Stats** | `summary .`, `disk usage`, `folder info` |

---

## 🏃 Quick Start

Run standalone from Command Prompt:
```cmd
E:\Agent's\file_manager_agent\run.bat
```
Or launch from the main menu:
```cmd
E:\Agent's\run_menu.bat
```
Select **`[4] File Manager Agent`**.
