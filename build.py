# -*- coding: utf-8 -*-
# smart_build_fixed.py — สคริปต์ build อัจฉริยะที่แก้ไข PyArmor compatibility
import subprocess
import sys
import ast
import re
from pathlib import Path

def run_cmd(cmd, errmsg):
    """รันคำสั่งและจับ error"""
    try:
        print(f"🔄 Run: {' '.join(cmd)}")
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error: {errmsg}")
        print(f"   Command: {' '.join(cmd)}")
        print(f"   Exit code: {e.returncode}")
        if e.stdout:
            print(f"   Stdout: {e.stdout}")
        if e.stderr:
            print(f"   Stderr: {e.stderr}")
        return False

def check_pyarmor_version():
    """ตรวจสอบเวอร์ชันของ PyArmor"""
    try:
        result = subprocess.run(['pyarmor', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            version = result.stdout.strip()
            print(f"📋 PyArmor version: {version}")
            return version
        else:
            print("⚠️  ไม่สามารถตรวจสอบเวอร์ชัน PyArmor")
            return None
    except Exception as e:
        print(f"⚠️  Error checking PyArmor version: {e}")
        return None

def get_pyarmor_help():
    """ดู help ของ PyArmor เพื่อตรวจสอบ arguments ที่ใช้ได้"""
    try:
        result = subprocess.run(['pyarmor', 'gen', '--help'], capture_output=True, text=True)
        if result.returncode == 0:
            return result.stdout
        return ""
    except:
        return ""

def extract_imports_from_file(file_path):
    """วิเคราะห์ไฟล์ Python และดึง imports ทั้งหมด"""
    imports = set()
    
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
    except:
        try:
            with open(file_path, 'r', encoding='cp1252', errors='ignore') as f:
                content = f.read()
        except:
            print(f"⚠️  ไม่สามารถอ่านไฟล์: {file_path}")
            return imports
    
    # Method 1: ใช้ AST (Abstract Syntax Tree)
    try:
        tree = ast.parse(content)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name and alias.name.strip():
                        imports.add(alias.name.strip())
            elif isinstance(node, ast.ImportFrom):
                if node.module and node.module.strip():
                    module_name = node.module.strip()
                    imports.add(module_name)
                    # เพิ่ม submodules ด้วย
                    for alias in node.names:
                        if alias.name and alias.name != '*' and alias.name.strip():
                            full_name = f"{module_name}.{alias.name.strip()}"
                            imports.add(full_name)
    except SyntaxError:
        print(f"⚠️  Syntax error ในไฟล์: {file_path}, ใช้ regex แทน")
    except Exception as e:
        print(f"⚠️  Error parsing {file_path}: {e}")
    
    # Method 2: ใช้ Regular Expression เป็น backup
    import_patterns = [
        r'^\s*import\s+([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)*)',
        r'^\s*from\s+([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)*)\s+import',
        r'__import__\([\'"]([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)*)[\'"]',
        r'importlib\.import_module\([\'"]([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)*)[\'"]'
    ]
    
    for pattern in import_patterns:
        matches = re.finditer(pattern, content, re.MULTILINE)
        for match in matches:
            module_name = match.group(1).strip()
            if module_name and not module_name.startswith('#'):
                imports.add(module_name)
    
    # ทำความสะอาด imports
    cleaned_imports = set()
    for imp in imports:
        if imp and imp.strip() and not imp.startswith('.') and imp.replace('.', '').replace('_', '').isalnum():
            cleaned_imports.add(imp.strip())
    
    return cleaned_imports

def get_all_imports_from_project(project_path, exclude_files=None):
    """ดึง imports ทั้งหมดจากโปรเจกต์"""
    if exclude_files is None:
        exclude_files = {'build.py', 'smart_build.py', 'smart_build_fixed.py', 'setup.py'}
    
    all_imports = set()
    py_files = []
    
    # หาไฟล์ .py ทั้งหมด
    for py_file in project_path.rglob('*.py'):
        if py_file.name not in exclude_files and 'venv' not in str(py_file) and '__pycache__' not in str(py_file):
            py_files.append(py_file)
            print(f"📁 วิเคราะห์: {py_file}")
            file_imports = extract_imports_from_file(py_file)
            all_imports.update(file_imports)
    
    return all_imports, py_files

def filter_standard_library_modules(imports):
    """กรอง modules ที่เป็น standard library"""
    import sys
    
    # รายการ standard library modules ที่รู้จัก
    known_stdlib = {
        'os', 'sys', 'subprocess', 'pathlib', 'json', 'io', 'shutil', 'tempfile',
        'urllib', 'http', 'ssl', 'socket', 'datetime', 'time', 'calendar',
        'threading', 'multiprocessing', 'concurrent', 'asyncio', 're', 'base64',
        'hashlib', 'hmac', 'uuid', 'random', 'secrets', 'zipfile', 'tarfile',
        'gzip', 'bz2', 'lzma', 'platform', 'signal', 'atexit', 'argparse',
        'configparser', 'logging', 'traceback', 'warnings', 'pdb', 'math',
        'decimal', 'fractions', 'statistics', 'collections', 'itertools',
        'functools', 'operator', 'copy', 'codecs', 'unicodedata', 'textwrap',
        'string', 'tkinter', 'pickle', 'csv', 'xml', 'html', 'email',
        'mimetypes', 'sqlite3', 'dbm', 'shelve', 'marshal', 'types',
        'inspect', 'dis', 'gc', 'weakref', 'array', 'struct', 'keyword',
        'ast', 'symtable', 'token', 'tokenize', 'tabnanny', 'pyclbr',
        'compileall', 'py_compile', 'importlib', 'pkgutil', 'modulefinder',
        'runpy', 'fileinput', 'linecache', 'filecmp', 'glob', 'fnmatch',
        'getopt', 'optparse', 'getpass', 'curses', 'locale', 'cmd', 'shlex',
        'ctypes', 'wmi', 'dataclasses', 'typing'
    }
    
    # Windows-specific modules
    if sys.platform == 'win32':
        known_stdlib.update({'winreg', 'winsound', 'msvcrt'})
    else:
        known_stdlib.update({'pwd', 'grp', 'crypt', 'termios', 'tty', 'pty', 'fcntl'})
    
    stdlib_imports = set()
    third_party_imports = set()
    
    for imp in imports:
        if not imp or not imp.strip() or imp.startswith('.'):
            continue
        
        root_module = imp.split('.')[0].strip()
        
        if not root_module or root_module.isdigit() or not root_module.isidentifier():
            continue
        
        if root_module in known_stdlib:
            stdlib_imports.add(imp)
        else:
            try:
                module = __import__(root_module)
                if hasattr(module, '__file__') and module.__file__:
                    if 'site-packages' in module.__file__ or 'dist-packages' in module.__file__:
                        third_party_imports.add(imp)
                    else:
                        stdlib_imports.add(imp)
                else:
                    stdlib_imports.add(imp)
            except (ImportError, ValueError, AttributeError):
                third_party_imports.add(imp)
    
    return stdlib_imports, third_party_imports

def create_comprehensive_imports_file(all_imports, project_path):
    """สร้างไฟล์ imports.py ที่ครอบคลุม"""
    stdlib_imports, third_party_imports = filter_standard_library_modules(all_imports)
    
    imports_content = '''# -*- coding: utf-8 -*-
# auto_imports.py - Auto-generated comprehensive imports file
"""
ไฟล์นี้ถูกสร้างขึ้นอัตโนมัติเพื่อรวม imports ทั้งหมดที่ใช้ในโปรเจกต์
"""

import sys
import warnings
warnings.filterwarnings('ignore')

# Standard Library Imports
'''
    
    # เพิ่ม standard library imports
    for imp in sorted(stdlib_imports):
        root_module = imp.split('.')[0]
        imports_content += f'''
try:
    import {imp}
except ImportError as e:
    print(f"Warning: Cannot import {imp}: {{e}}")
    {root_module} = None'''
    
    imports_content += '''

# Third-party Library Imports
'''
    
    # เพิ่ม third-party imports
    for imp in sorted(third_party_imports):
        root_module = imp.split('.')[0]
        imports_content += f'''
try:
    import {imp}
except ImportError as e:
    print(f"Warning: Cannot import {imp}: {{e}}")
    {root_module} = None'''
    
    imports_content += f'''

# Export all imported modules
__all__ = {sorted(list(all_imports))}

print("✅ Auto-imports loaded: {len(all_imports)} modules")
'''
    
    # เขียนไฟล์
    imports_file = project_path / 'auto_imports.py'
    with open(imports_file, 'w', encoding='utf-8') as f:
        f.write(imports_content)
    
    print(f"📝 สร้างไฟล์: {imports_file}")
    print(f"   - Standard Library: {len(stdlib_imports)} modules")
    print(f"   - Third-party: {len(third_party_imports)} modules")
    
    return imports_file, stdlib_imports, third_party_imports

def clean_pyarmor_dist(project_path):
    """ทำความสะอาด pyarmor_dist directory"""
    dist_path = project_path / 'pyarmor_dist'
    if dist_path.exists():
        import shutil
        try:
            shutil.rmtree(dist_path)
            print("🗑️  ลบ pyarmor_dist เก่าแล้ว")
        except Exception as e:
            print(f"⚠️  ไม่สามารถลบ pyarmor_dist: {e}")

def build_with_pyarmor_compatible(py_files, pack_modules, project_path):
    """Build ด้วย PyArmor ที่ compatible กับเวอร์ชันต่างๆ"""
    
    # ทำความสะอาดก่อน
    clean_pyarmor_dist(project_path)
    
    # ตรวจสอบ PyArmor help
    help_text = get_pyarmor_help()
    
    # ลองใช้คำสั่งง่ายๆ ก่อน
    print("🔄 ลองใช้ PyArmor แบบง่าย...")
    py_files_str = [str(f) for f in py_files]
    
    simple_cmd = [
        'pyarmor', 'gen',
        '-O', 'pyarmor_dist'
    ] + py_files_str
    
    if run_cmd(simple_cmd, 'PyArmor simple command ล้มเหลว'):
        print("✅ PyArmor simple command สำเร็จ")
        return True
    
    print("🔄 ลองใช้ PyArmor แบบละเอียด...")
    
    # สร้าง command พื้นฐาน
    cmd_pyarmor = [
        'pyarmor', 'gen',
        '-O', 'pyarmor_dist'
    ]
    
    # เพิ่ม pack modules (จำกัดจำนวนเพื่อไม่ให้ command line ยาวเกินไป)
    limited_modules = list(pack_modules)[:20]  # ลดจำนวนลง
    if limited_modules:
        cmd_pyarmor.extend(['--pack', ','.join(limited_modules)])
    
    # ตรวจสอบและเพิ่ม arguments ที่รองรับ (ระวังสั่งคำ)
    if '--mix-str' in help_text:
        cmd_pyarmor.append('--mix-str')
        print("✅ รองรับ --mix-str")
    
    if '--assert-call' in help_text:
        cmd_pyarmor.append('--assert-call')
        print("✅ รองรับ --assert-call")
    
    if '--assert-import' in help_text:
        cmd_pyarmor.append('--assert-import')
        print("✅ รองรับ --assert-import")
    
    # เพิ่มไฟล์ Python
    cmd_pyarmor.extend(py_files_str)
    
    return run_cmd(cmd_pyarmor, 'PyArmor detailed command ล้มเหลว')

def fix_pyarmor_runtime_imports(project_path):
    """แก้ไข imports ใน pyarmor_dist files"""
    dist_path = project_path / 'pyarmor_dist'
    if not dist_path.exists():
        return False
    
    # หา runtime directory
    runtime_dirs = list(dist_path.glob('pyarmor_runtime_*'))
    if not runtime_dirs:
        print("⚠️  ไม่พบ pyarmor_runtime directory")
        return False
    
    runtime_dir = runtime_dirs[0]
    runtime_name = runtime_dir.name
    print(f"🔍 พบ runtime: {runtime_name}")
    
    # แก้ไข imports ในไฟล์ทั้งหมด
    fixed_count = 0
    for py_file in dist_path.glob('*.py'):
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # แทนที่ import statements ที่ผิด
            old_import = f"from {runtime_name} import __pyarmor__"
            new_import = f"from {runtime_name} import __pyarmor__"
            
            # ตรวจสอบรูปแบบ import ที่อาจมีปัญหา
            import_patterns = [
                (rf'from {runtime_name} import \*\*pyarmor\*\*', f'from {runtime_name} import __pyarmor__'),
                (rf'from {runtime_name} import \*pyarmor\*', f'from {runtime_name} import __pyarmor__'),
                (rf'import \*\*pyarmor\*\*', f'from {runtime_name} import __pyarmor__')
            ]
            
            modified = False
            for old_pattern, new_pattern in import_patterns:
                if re.search(old_pattern, content):
                    content = re.sub(old_pattern, new_pattern, content)
                    modified = True
            
            if modified:
                with open(py_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                fixed_count += 1
                print(f"🔧 แก้ไข: {py_file.name}")
        
        except Exception as e:
            print(f"⚠️  ไม่สามารถแก้ไข {py_file.name}: {e}")
    
    if fixed_count > 0:
        print(f"✅ แก้ไข imports สำเร็จ: {fixed_count} ไฟล์")
    
    return True

def main():
    print("🚀 Smart PyArmor Build Script (Fixed Version)")
    print("=" * 60)
    
    # ตรวจสอบ PyArmor
    version = check_pyarmor_version()
    if not version:
        print("❌ ไม่พบ PyArmor หรือไม่สามารถเรียกใช้ได้")
        print("💡 ติดตั้งด้วย: pip install pyarmor")
        sys.exit(1)
    
    project_path = Path(__file__).parent
    
    # 1. วิเคราะห์ imports ทั้งหมด
    print("\n📊 วิเคราะห์ imports ในโปรเจกต์...")
    all_imports, py_files = get_all_imports_from_project(project_path)
    
    if not py_files:
        print("❌ ไม่พบไฟล์ .py ในโปรเจกต์")
        sys.exit(1)
    
    print(f"✅ พบ {len(all_imports)} imports ทั้งหมด")
    print(f"✅ พบ {len(py_files)} ไฟล์ Python")
    
    # 2. สร้างไฟล์ imports
    print("\n📝 สร้างไฟล์ auto_imports.py...")
    imports_file, stdlib_imports, third_party_imports = create_comprehensive_imports_file(all_imports, project_path)
    
    # 3. ตั้งค่า PyArmor
    print("\n⚙️  ตั้งค่า PyArmor...")
    if not run_cmd(['pyarmor', 'cfg', 'encoding=utf-8'], 'ตั้งค่า encoding ล้มเหลว'):
        print("⚠️  ไม่สามารถตั้งค่า encoding, ดำเนินการต่อ...")
    
    # 4. Obfuscate ด้วย PyArmor
    print("\n🔐 Obfuscating ด้วย PyArmor...")
    
    # รวมไฟล์ auto_imports.py เข้าไปด้วย
    all_py_files = py_files + [imports_file]
    
    # ใช้ฟังก์ชันที่ compatible
    if not build_with_pyarmor_compatible(all_py_files, stdlib_imports, project_path):
        print("❌ PyArmor obfuscation ล้มเหลว")
        sys.exit(1)
    
    print("✅ PyArmor: obfuscate สำเร็จ -> pyarmor_dist/")
    
    # 4.1 แก้ไข runtime imports
    print("\n🔧 แก้ไข PyArmor runtime imports...")
    if not fix_pyarmor_runtime_imports(project_path):
        print("⚠️  ไม่สามารถแก้ไข runtime imports")
    
    # 4.2 ตรวจสอบ runtime files
    dist_path = project_path / 'pyarmor_dist'
    runtime_dirs = list(dist_path.glob('pyarmor_runtime_*'))
    if runtime_dirs:
        runtime_dir = runtime_dirs[0]
        print(f"✅ พบ runtime directory: {runtime_dir.name}")
        
        # ตรวจสอบว่ามี __init__.py
        init_file = runtime_dir / '__init__.py'
        if not init_file.exists():
            print("⚠️  สร้าง __init__.py ใน runtime directory")
            with open(init_file, 'w', encoding='utf-8') as f:
                f.write('# PyArmor Runtime\n')
    else:
        print("⚠️  ไม่พบ runtime directory")
    
    # 5. Bundle ด้วย PyInstaller
    print("\n📦 Building ด้วย PyInstaller...")
    
    # หา entry file
    entry_candidates = ['autoupdate.py', 'main.py', 'app.py', 'launcher_main.py']
    entry = None
    
    for candidate in entry_candidates:
        potential_entry = project_path / 'pyarmor_dist' / candidate
        if potential_entry.exists():
            entry = potential_entry
            break
    
    if not entry:
        # ใช้ไฟล์แรกที่พบ
        obfuscated_files = list((project_path / 'pyarmor_dist').glob('*.py'))
        if obfuscated_files:
            entry = obfuscated_files[0]
    
    if not entry:
        print("❌ ไม่พบ entry file ใน pyarmor_dist/")
        print("📁 ไฟล์ใน pyarmor_dist:")
        for f in (project_path / 'pyarmor_dist').iterdir():
            print(f"   - {f.name}")
        sys.exit(1)
    
    print(f"🎯 Entry file: {entry}")
    
    # สร้าง hidden imports สำหรับ PyInstaller (จำกัดจำนวน)
    hidden_imports = []
    limited_imports = sorted(list(all_imports))[:80]  # จำกัดไม่เกิน 30 modules
    for imp in limited_imports:
        hidden_imports.extend(['--hidden-import', imp])
    
    cmd_pyinstaller = [
        'pyinstaller',
        '--onefile',
        '--noconsole',
        '--clean',
        '--name', f'{entry.stem}_obfuscated'
    ]
    
    # เพิ่ม assets ถ้ามี
    assets_path = project_path / 'assets'
    if assets_path.exists():
        cmd_pyinstaller.extend(['--add-data', f'{assets_path};assets'])
        icon_path = assets_path / 'icon.ico'
        if icon_path.exists():
            cmd_pyinstaller.extend(['--icon', str(icon_path)])
    
    # เพิ่ม hidden imports
    cmd_pyinstaller.extend(hidden_imports)
    cmd_pyinstaller.append(str(entry))
    
    if not run_cmd(cmd_pyinstaller, 'PyInstaller build ล้มเหลว'):
        print("⚠️  PyInstaller ล้มเหลว, ลองใช้คำสั่งง่ายๆ...")
        
        # ลองคำสั่งง่ายๆ
        simple_pyinstaller = [
            'pyinstaller',
            '--onefile',
            '--name', f'{entry.stem}_obfuscated',
            str(entry)
        ]
        
        if not run_cmd(simple_pyinstaller, 'PyInstaller simple command ล้มเหลว'):
            sys.exit(1)
    
    print("✅ PyInstaller: สร้างไฟล์ executable สำเร็จ")
    
    # 6. บีบอัดด้วย UPX (optional)
    print("\n🗜️  พยายามบีบอัดด้วย UPX...")
    exe_name = f'{entry.stem}_obfuscated.exe'
    upx_cmd = ['upx', '--best', '--lzma', f'dist/{exe_name}']
    
    if run_cmd(upx_cmd, 'UPX compress failed'):
        print("✅ UPX: บีบอัดสำเร็จ")
    else:
        print("⚠️  UPX: ไม่สามารถบีบอัดได้ (ข้ามขั้นตอนนี้)")
    
    print("\n🎉 Build Process เสร็จสมบูรณ์!")
    print(f"📁 Output: dist/{exe_name}")
    print(f"📊 Total imports processed: {len(all_imports)}")
    print(f"🔐 Files obfuscated: {len(all_py_files)}")

if __name__ == '__main__':
    main()