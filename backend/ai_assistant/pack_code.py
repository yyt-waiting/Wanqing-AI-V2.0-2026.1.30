import os

# --- 配置区域 ---
OUTPUT_FILE = 'project_snapshot.txt'
IGNORE_DIRS = {
    'venv', '.venv', 'venv2.0', 'env', '__pycache__', '.git', '.vscode', '.idea',
    'assets', 'output', 'build', 'dist', 'ai_assistant.egg-info'
}
ALLOWED_EXTENSIONS = {
    '.py', '.md', '.txt', '.json', '.jsonl', '.gitignore'
}
# ----------------

def pack_project():
    project_root = os.getcwd()
    print(f"--- [START] Packing project from: {project_root}")
    print(f"--- [INFO] Ignoring directories: {IGNORE_DIRS}")
    
    file_count = 0
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as outfile:
        outfile.write(f"=== PROJECT CODE SNAPSHOT ===\n")
        outfile.write(f"Generated from: {project_root}\n")
        outfile.write(f"Note: Libraries (venv) and Assets are excluded.\n\n")

        for root, dirs, files in os.walk(project_root):
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]

            for file in files:
                if file == OUTPUT_FILE or file == os.path.basename(__file__):
                    continue

                ext = os.path.splitext(file)[1].lower()
                if ext in ALLOWED_EXTENSIONS:
                    file_path = os.path.join(root, file)
                    rel_path = os.path.relpath(file_path, project_root)

                    try:
                        print(f"--- [PROCESSING] {rel_path}")
                        
                        outfile.write(f"\n{'='*40}\n")
                        outfile.write(f"FILE_PATH: {rel_path}\n")
                        outfile.write(f"{'='*40}\n\n")

                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as infile:
                            outfile.write(infile.read())
                        
                        outfile.write("\n")
                        file_count += 1
                        
                    except Exception as e:
                        print(f"--- [ERROR] Failed to read {rel_path}: {e}")

    print(f"\n--- [DONE] ---")
    print(f"--- [SUMMARY] Total files packed: {file_count}")
    print(f"--- [OUTPUT] File created: {OUTPUT_FILE}")
    print("--- Please send this file to the new AI conversation. ---")

if __name__ == '__main__':
    pack_project()