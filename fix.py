# -*- coding: utf-8 -*-
# fix_pyarmor_runtime.py - แก้ไขปัญหา PyArmor runtime
import re
from pathlib import Path

def fix_pyarmor_runtime_issue():
    """แก้ไขปัญหา PyArmor runtime imports"""
    
    project_path = Path(__file__).parent
    dist_path = project_path / 'pyarmor_dist'
    
    if not dist_path.exists():
        print("❌ ไม่พบ pyarmor_dist directory")
        print("💡 รัน PyArmor ก่อน: pyarmor gen -O pyarmor_dist *.py")
        return False
    
    print("🔍 ตรวจสอบ pyarmor_dist...")
    
    # หา runtime directory
    runtime_dirs = list(dist_path.glob('pyarmor_runtime_*'))
    if not runtime_dirs:
        print("❌ ไม่พบ pyarmor_runtime directory")
        print("💡 PyArmor อาจไม่ได้สร้าง runtime ให้")
        
        # ลองสร้าง runtime ใหม่
        print("🔄 พยายามสร้าง runtime ใหม่...")
        import subprocess
        
        # หาไฟล์ .py ทั้งหมดในโฟลเดอร์หลัก
        py_files = list(project_path.glob('*.py'))
        if py_files:
            py_files_str = [str(f) for f in py_files if f.name != 'fix.py' | f.name != 'build.py']
            cmd = ['pyarmor', 'gen', '-O', 'pyarmor_dist'] + py_files_str
            
            try:
                subprocess.run(cmd, check=True)
                print("✅ สร้าง PyArmor runtime ใหม่สำเร็จ")
                runtime_dirs = list(dist_path.glob('pyarmor_runtime_*'))
            except subprocess.CalledProcessError as e:
                print(f"❌ ไม่สามารถสร้าง runtime ใหม่: {e}")
                return False
        else:
            print("❌ ไม่พบไฟล์ .py ในโฟลเดอร์หลัก")
            return False
    
    if not runtime_dirs:
        print("❌ ยังคงไม่พบ runtime directory")
        return False
    
    runtime_dir = runtime_dirs[0]
    runtime_name = runtime_dir.name
    print(f"✅ พบ runtime: {runtime_name}")
    
    # ตรวจสอบว่ามี __init__.py ใน runtime
    init_file = runtime_dir / '__init__.py'
    if not init_file.exists():
        print("🔧 สร้าง __init__.py ใน runtime directory")
        with open(init_file, 'w', encoding='utf-8') as f:
            f.write(f'''# -*- coding: utf-8 -*-
# PyArmor Runtime {runtime_name}
"""PyArmor Runtime Module"""

# Import the actual runtime
try:
    from . import __pyarmor__
except ImportError:
    # Fallback import
    import __pyarmor__

__all__ = ['__pyarmor__']
''')
    
    # แก้ไข imports ในไฟล์ทั้งหมด
    fixed_count = 0
    error_patterns = [
        r'from\s+' + re.escape(runtime_name) + r'\s+import\s+\*\*pyarmor\*\*',
        r'from\s+' + re.escape(runtime_name) + r'\s+import\s+\*pyarmor\*',
        r'import\s+\*\*pyarmor\*\*',
        r'from\s+' + re.escape(runtime_name) + r'\s+import\s+\*\*__pyarmor__\*\*'
    ]
    
    correct_import = f'from {runtime_name} import __pyarmor__'
    
    print("🔧 แก้ไข import statements...")
    
    for py_file in dist_path.glob('*.py'):
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            
            # แก้ไขรูปแบบ import ที่ผิด
            for pattern in error_patterns:
                content = re.sub(pattern, correct_import, content)
            
            # ตรวจสอบรูปแบบ import อื่นๆ ที่อาจมีปัญหา
            lines = content.split('\n')
            fixed_lines = []
            
            for line in lines:
                # ถ้าเจอ import ที่มี **pyarmor**
                if '**pyarmor**' in line:
                    if runtime_name in line:
                        fixed_line = correct_import
                        print(f"   🔧 แก้ไข: {line.strip()} -> {fixed_line}")
                        fixed_lines.append(fixed_line)
                    else:
                        fixed_lines.append(line)
                # ถ้าเจอ import ที่มี *pyarmor*
                elif '*pyarmor*' in line:
                    if runtime_name in line:
                        fixed_line = correct_import
                        print(f"   🔧 แก้ไข: {line.strip()} -> {fixed_line}")
                        fixed_lines.append(fixed_line)
                    else:
                        fixed_lines.append(line)
                else:
                    fixed_lines.append(line)
            
            content = '\n'.join(fixed_lines)
            
            # เขียนไฟล์ถ้ามีการเปลี่ยนแปลง
            if content != original_content:
                with open(py_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                fixed_count += 1
                print(f"✅ แก้ไข: {py_file.name}")
        
        except Exception as e:
            print(f"⚠️  ไม่สามารถแก้ไข {py_file.name}: {e}")
    
    if fixed_count > 0:
        print(f"\n✅ แก้ไข imports สำเร็จ: {fixed_count} ไฟล์")
    else:
        print("\n✅ ไม่พบ imports ที่ต้องแก้ไข")
    
    # ตรวจสอบการทำงาน
    print("\n🧪 ทดสอบการ import...")
    test_file = dist_path / 'autoupdate.py'
    if test_file.exists():
        try:
            # เพิ่ม runtime directory เข้า Python path
            import sys
            sys.path.insert(0, str(dist_path))
            
            # ลองอ่านและตรวจสอบไฟล์
            with open(test_file, 'r', encoding='utf-8') as f:
                first_lines = f.readlines()[:5]
            
            print("📄 บรรทัดแรกของ autoupdate.py:")
            for i, line in enumerate(first_lines, 1):
                print(f"   {i}: {line.rstrip()}")
            
            # ตรวจสอบว่ามี runtime directory อยู่หรือไม่
            if runtime_dir.exists():
                runtime_files = list(runtime_dir.glob('*'))
                print(f"\n📁 ไฟล์ใน {runtime_name}:")
                for rf in runtime_files:
                    print(f"   - {rf.name}")
            
        except Exception as e:
            print(f"⚠️  การทดสอบล้มเหลว: {e}")
    
    print("\n🎉 เสร็จสิ้นการแก้ไข PyArmor runtime!")
    print("💡 ลองรัน autoupdate.py อีกครั้ง")
    
    return True

if __name__ == '__main__':
    print("🔧 PyArmor Runtime Fixer")
    print("=" * 40)
    fix_pyarmor_runtime_issue()