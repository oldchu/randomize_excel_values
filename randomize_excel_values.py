#!/usr/bin/env python3
"""
Скрипт для рандомизации значений моментов затяжки в Excel файлах.
Обрабатывает столбцы: МЗ 1/60, МЗ 2/60, МЗ 3/60, УЗ 3/60, МЗ 1/40, МЗ 2/40, МЗ 3/40
Диапазон значений: от 20.9 до 22.1 с высокой точностью (до 13 знаков после запятой)
"""

import pandas as pd
import numpy as np
import os
import glob
import random
import shutil
from pathlib import Path

# Настройки
INPUT_DIR = "src/xlsx"  # Папка с исходными файлами
OUTPUT_DIR = "output"   # Папка для сохранения обработанных файлов
BACKUP_DIR = "backup"   # Папка для резервных копий

# Столбцы для обработки
TARGET_COLUMNS = [
    "МЗ 1/60",
    "МЗ 2/60", 
    "МЗ 3/60",
    "УЗ 3/60",
    "МЗ 1/40",
    "МЗ 2/40",
    "МЗ 3/40"
]

# Диапазон значений (можно настроить под любые нужды)
MIN_VALUE = 20.9
MAX_VALUE = 22.1

# Альтернативные диапазоны для разных типов данных
# Раскомментируйте нужный или задайте свой:
# MIN_VALUE, MAX_VALUE = 0.0, 100.0      # Проценты
# MIN_VALUE, MAX_VALUE = 10.0, 50.0      # Температура
# MIN_VALUE, MAX_VALUE = 1.0, 10.0       # Коэффициенты
# MIN_VALUE, MAX_VALUE = 100.0, 1000.0   # Большие значения

# Опция сохранения временных меток файлов
PRESERVE_FILE_DATES = True  # Сохранять дату создания/изменения файлов
def generate_random_value(min_val=MIN_VALUE, max_val=MAX_VALUE):
    """
    Генерирует случайное значение в заданном диапазоне с высокой точностью.
    Возвращает число с 13 знаками после запятой.
    """
    return round(random.uniform(min_val, max_val), 13)

def create_directories():
    """Создает необходимые директории если они не существуют."""
    for directory in [OUTPUT_DIR, BACKUP_DIR]:
        Path(directory).mkdir(exist_ok=True)
        print(f"Создана/проверена директория: {directory}")

def backup_file(file_path):
    """Создает резервную копию файла."""
    filename = os.path.basename(file_path)
    backup_path = os.path.join(BACKUP_DIR, filename)
    
    if not os.path.exists(backup_path):
        shutil.copy2(file_path, backup_path)
        print(f"Создана резервная копия: {backup_path}")
    else:
        print(f"Резервная копия уже существует: {backup_path}")

def preserve_file_timestamps(source_file, target_file):
    """
    Копирует временные метки (дата создания/изменения) с исходного файла на целевой.
    
    Args:
        source_file (str): Путь к исходному файлу
        target_file (str): Путь к целевому файлу
    """
    try:
        # Получаем статистику исходного файла
        stat = os.stat(source_file)
        
        # Применяем временные метки к целевому файлу
        # atime - время последнего доступа, mtime - время последнего изменения
        os.utime(target_file, (stat.st_atime, stat.st_mtime))
        
        print(f"  Сохранены временные метки файла")
    except Exception as e:
        print(f"  ⚠️  Не удалось сохранить временные метки: {str(e)}")

def process_excel_file(file_path, test_mode=False):
    """
    Обрабатывает один Excel файл.
    
    Args:
        file_path (str): Путь к файлу
        test_mode (bool): Если True, выводит информацию о найденных столбцах без изменений
    
    Returns:
        bool: True если файл успешно обработан, False в случае ошибки
    """
    try:
        print(f"\nОбработка файла: {file_path}")
        
        # Создаем резервную копию
        if not test_mode:
            backup_file(file_path)
        
        # Читаем Excel файл
        df = pd.read_excel(file_path)
        
        print(f"Размер таблицы: {df.shape[0]} строк, {df.shape[1]} столбцов")
        print(f"Столбцы в файле: {list(df.columns)}")
        
        # Находим столбцы для обработки
        found_columns = []
        for target_col in TARGET_COLUMNS:
            if target_col in df.columns:
                found_columns.append(target_col)
            else:
                # Попробуем найти похожие столбцы (с учетом возможных различий в пробелах)
                similar_cols = [col for col in df.columns if target_col.replace(" ", "").lower() in col.replace(" ", "").lower()]
                if similar_cols:
                    found_columns.extend(similar_cols)
                    print(f"Найден похожий столбец для '{target_col}': {similar_cols}")
        
        if not found_columns:
            print(f"⚠️  В файле не найдено ни одного целевого столбца!")
            return False
        
        print(f"Найденные столбцы для обработки: {found_columns}")
        
        if test_mode:
            # В тестовом режиме только показываем информацию
            for col in found_columns:
                if col in df.columns:
                    non_null_count = df[col].notna().sum()
                    if non_null_count > 0:
                        current_min = df[col].min()
                        current_max = df[col].max()
                        print(f"  {col}: {non_null_count} значений, диапазон: {current_min:.4f} - {current_max:.4f}")
                    else:
                        print(f"  {col}: нет данных")
            return True
        
        # Обрабатываем найденные столбцы
        changes_made = False
        for col in found_columns:
            if col in df.columns:
                # Находим строки с числовыми значениями
                numeric_mask = pd.to_numeric(df[col], errors='coerce').notna()
                numeric_count = numeric_mask.sum()
                
                if numeric_count > 0:
                    print(f"  Обновляем {numeric_count} значений в столбце '{col}'")
                    
                    # Генерируем новые случайные значения
                    new_values = [generate_random_value() for _ in range(numeric_count)]
                    
                    # Применяем новые значения
                    df.loc[numeric_mask, col] = new_values
                    changes_made = True
                    
                    # Показываем примеры новых значений
                    sample_values = new_values[:3]
                    print(f"    Примеры новых значений: {sample_values}")
                else:
                    print(f"  В столбце '{col}' нет числовых значений для обновления")
        
        if not changes_made:
            print("⚠️  Изменения не были внесены - не найдено числовых данных в целевых столбцах")
            return False
        
        # Сохраняем обработанный файл
        filename = os.path.basename(file_path)
        output_path = os.path.join(OUTPUT_DIR, filename)
        
        df.to_excel(output_path, index=False)
        print(f"✅ Файл сохранен: {output_path}")
        
        # Сохраняем временные метки исходного файла, если включена опция
        if PRESERVE_FILE_DATES:
            preserve_file_timestamps(file_path, output_path)
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при обработке файла {file_path}: {str(e)}")
        return False

def main():
    """Основная функция."""
    global PRESERVE_FILE_DATES
    
    print("🔧 Скрипт рандомизации значений в Excel файлах")
    print("=" * 50)
    print(f"📊 Диапазон значений: {MIN_VALUE} - {MAX_VALUE}")
    print(f"📅 Сохранение временных меток: {'ВКЛЮЧЕНО' if PRESERVE_FILE_DATES else 'ВЫКЛЮЧЕНО'}")
    
    # Создаем необходимые директории
    create_directories()
    
    # Находим все Excel файлы
    excel_files = glob.glob(os.path.join(INPUT_DIR, "*.xlsx"))
    
    if not excel_files:
        print(f"❌ В папке {INPUT_DIR} не найдено Excel файлов!")
        return
    
    print(f"Найдено {len(excel_files)} Excel файлов")
    
    # Спрашиваем пользователя о режиме работы
    print("\nВыберите режим работы:")
    print("1. Тестовый режим (анализ без изменений)")
    print("2. Обработка всех файлов")
    print("3. Обработка одного файла для теста")
    print("4. Настройки")
    
    try:
        choice = input("Введите номер (1-4): ").strip()
        
        if choice == "1":
            # Тестовый режим
            print("\n🔍 ТЕСТОВЫЙ РЕЖИМ - анализ файлов без изменений")
            for i, file_path in enumerate(excel_files[:5], 1):  # Анализируем первые 5 файлов
                print(f"\n--- Файл {i}/5 ---")
                process_excel_file(file_path, test_mode=True)
                
        elif choice == "2":
            # Обработка всех файлов
            print(f"\n🚀 Начинаем обработку {len(excel_files)} файлов...")
            
            successful = 0
            failed = 0
            
            for i, file_path in enumerate(excel_files, 1):
                print(f"\n--- Файл {i}/{len(excel_files)} ---")
                if process_excel_file(file_path):
                    successful += 1
                else:
                    failed += 1
            
            print(f"\n📊 РЕЗУЛЬТАТЫ:")
            print(f"✅ Успешно обработано: {successful}")
            print(f"❌ Ошибок: {failed}")
            
        elif choice == "3":
            # Обработка одного файла для теста
            print(f"\n🧪 Тестовая обработка первого файла: {excel_files[0]}")
            if process_excel_file(excel_files[0]):
                print("✅ Тестовая обработка завершена успешно!")
            else:
                print("❌ Ошибка при тестовой обработке")
                
        elif choice == "4":
            # Настройки сохранения временных меток
            print(f"\n⚙️  НАСТРОЙКИ")
            print(f"Диапазон значений: {MIN_VALUE} - {MAX_VALUE}")
            print(f"Сохранение временных меток: {'ВКЛЮЧЕНО' if PRESERVE_FILE_DATES else 'ВЫКЛЮЧЕНО'}")
            print("\nОпция сохранения временных меток позволяет:")
            print("- Сохранить дату создания и изменения исходных файлов")
            print("- Обработанные файлы будут иметь те же временные метки, что и исходные")
            print("- Полезно для сохранения хронологии данных")
            
            toggle_choice = input(f"\nИзменить настройку временных меток? (y/n): ").strip().lower()
            if toggle_choice in ['y', 'yes', 'д', 'да']:
                PRESERVE_FILE_DATES = not PRESERVE_FILE_DATES
                print(f"✅ Сохранение временных меток: {'ВКЛЮЧЕНО' if PRESERVE_FILE_DATES else 'ВЫКЛЮЧЕНО'}")
            
            # Возвращаемся к главному меню
            print("\nВозврат к главному меню...")
            main()
            return
                
        else:
            print("❌ Неверный выбор!")
            
    except KeyboardInterrupt:
        print("\n\n⏹️  Операция прервана пользователем")
    except Exception as e:
        print(f"\n❌ Неожиданная ошибка: {str(e)}")

if __name__ == "__main__":
    main()