import os
from pathlib import Path
from datetime import datetime

def scan_project():
    # 프로젝트 루트 디렉토리 (현재 스크립트의 상위 디렉토리)
    project_root = Path(__file__).parent
    
    # 결과를 저장할 리스트
    files_content = []
    
    # 무시할 디렉토리와 파일
    ignore_dirs = {'.git', '__pycache__', 'venv', 'env', '.pytest_cache', '.vscode'}
    ignore_files = {'.pyc', '.pyo', '.pyd', '.so', '.dll', '.db', '.sqlite3'}
    
    def should_ignore(path):
        # '전체 코드 출력.py' 파일은 제외
        if path.is_file() and path.name == Path(__file__).name:
            return True
        # 무시해야 할 경로인지 확인 (디렉토리 및 확장자 기준)
        parts = path.parts
        return any(part in ignore_dirs for part in parts) or \
               path.suffix in ignore_files
    
    # 모든 파일을 재귀적으로 스캔
    for path in sorted(project_root.rglob('*')):
        if should_ignore(path):
            continue
            
        if path.is_file():
            try:
                # 파일 경로를 프로젝트 루트로부터의 상대 경로로 변환
                relative_path = path.relative_to(project_root)
                
                # 파일 내용 읽기
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                files_content.append(f"\n[파일 경로: {relative_path}]\n")
                files_content.append("```")
                files_content.append(content)
                files_content.append("```")
                files_content.append("\n" + "="*50 + "\n")
            except Exception as e:
                print(f"Error reading {path}: {e}")
    
    # 현재 시간을 파일명에 포함
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"project_structure_{timestamp}.txt"
    
    # 프로젝트 구조 출력
    with open(output_filename, 'w', encoding='utf-8') as f:
        f.write("프로젝트 구조 및 코드 모음\n")
        f.write("="*50 + "\n")
        f.write(f"생성 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("="*50 + "\n\n")
        
        # 디렉토리 구조 출력
        f.write("[ 프로젝트 디렉토리 구조 ]\n")
        for path in sorted(project_root.rglob('*')):
            if not should_ignore(path):
                relative_path = path.relative_to(project_root)
                indent = '    ' * (len(relative_path.parts) - 1)
                f.write(f"{indent}{'📁 ' if path.is_dir() else '📄 '}{relative_path.name}\n")
        
        f.write("\n" + "="*50 + "\n")
        f.write("[ 파일별 코드 ]\n")
        
        # 각 파일의 내용 출력
        f.write(''.join(files_content))

if __name__ == "__main__":
    try:
        scan_project()
        print("프로젝트 구조와 코드가 성공적으로 출력되었습니다.")
    except Exception as e:
        print(f"오류 발생: {e}")
