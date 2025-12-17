import shutil
import os

# Удаляем все __pycache__ папки
for root, dirs, files in os.walk('.'):
    if '__pycache__' in dirs:
        pycache_path = os.path.join(root, '__pycache__')
        print(f"Удаляю кэш: {pycache_path}")
        shutil.rmtree(pycache_path)

# Удаляем старую папку handlers/hr/ которая конфликтует
old_hr_dir = "handlers/hr"
if os.path.exists(old_hr_dir) and os.path.isdir(old_hr_dir):
    print(f"\nУдаляю старую папку: {old_hr_dir}")
    shutil.rmtree(old_hr_dir)
    print(f"✅ Папка {old_hr_dir} удалена!")

print("\n✅ Кэш очищен! Теперь запускай бота.")

