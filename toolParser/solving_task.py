import sys
import os
import csv
import time

# Добавляем пути для импорта ваших модулей (если необходимо)
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from data.data_parsers.custom_instance_parser import parse
from solution_methods.CP_SAT.run_cp_sat import run_CP_SAT
from task_parser import create_processing_info

# Параметры решателя (можно менять)
SOLVER_PARAMS = {
    "solver": {"time_limit": 3600, "model": "fajsp"},
    "output": {"logbook": True}
}

def process_file(file_path, output_csv_writer, folder_name):
    """Обрабатывает один файл: парсит, решает, записывает результат в CSV."""
    try:
        print(f"Обработка файла: {file_path}")
        start_total = time.time()

        # Парсинг файла в нужный формат
        processing_info = create_processing_info(file_path)
        if not processing_info:
            print(f"  Предупреждение: файл {file_path} не дал данных (processing_info пуст). Пропускаем.")
            return

        # Если processing_info – список (несколько блоков), обрабатываем каждый блок как отдельный инстанс
        # Или объединяем? Обычно ожидается один словарь. Приводим к единому.
        if isinstance(processing_info, list):
            # Если список блоков – обрабатываем каждый отдельно
            for idx, block_info in enumerate(processing_info):
                instance_name = block_info.get("instance_name", f"{os.path.basename(file_path)}_block{idx+1}")
                print(f"  Решение блока {idx+1}: {instance_name}")
                # Сбрасываем instance_name для parse (ожидает поле instance_name)
                block_info["instance_name"] = instance_name
                _solve_and_write(block_info, instance_name, output_csv_writer, folder_name)
        else:
            # Один словарь
            instance_name = processing_info.get("instance_name", os.path.basename(file_path))
            _solve_and_write(processing_info, instance_name, output_csv_writer, folder_name)

        print(f"  Завершён за {time.time() - start_total:.2f} сек\n")

    except Exception as e:
        print(f"Ошибка при обработке {file_path}: {e}")
        output_csv_writer.writerow({
            "folder": folder_name,
            "file": os.path.basename(file_path),
            "instance_name": "ERROR",
            "makespan": None,
            "solver_time": None,
            "status": f"ERROR: {str(e)[:100]}"
        })

def _solve_and_write(processing_info, instance_name, csv_writer, folder_name):
    """Вспомогательная функция: решает один инстанс и пишет строку в CSV."""
    try:
        # Парсим в окружение задачи
        jobShopEnv = parse(processing_info)

        # Решаем
        start_solve = time.time()
        results, jobShopEnv = run_CP_SAT(jobShopEnv, **SOLVER_PARAMS)
        solver_time = time.time() - start_solve

        # Извлекаем результаты (зависит от вашей реализации run_CP_SAT)
        makespan = None
        status = "UNKNOWN"
        if isinstance(results, dict):
            makespan = results.get("makespan") or results.get("objective")
            status = results.get("status", "UNKNOWN")
        else:
            # Если results – не словарь, попробуем получить из окружения
            if hasattr(jobShopEnv, "makespan"):
                makespan = jobShopEnv.makespan
            elif hasattr(jobShopEnv, "objective_value"):
                makespan = jobShopEnv.objective_value
            status = "SOLVED" if makespan is not None else "FAILED"

        # Запись в CSV
        csv_writer.writerow({
            "folder": folder_name,
            "file": os.path.basename(file_path) if 'file_path' in locals() else instance_name,
            "instance_name": instance_name,
            "makespan": makespan,
            "solver_time": solver_time,
            "status": status
        })
        print(f"    Решено: makespan={makespan}, время={solver_time:.2f} сек")

    except Exception as e:
        print(f"    Ошибка решения {instance_name}: {e}")
        csv_writer.writerow({
            "folder": folder_name,
            "file": os.path.basename(file_path) if 'file_path' in locals() else instance_name,
            "instance_name": instance_name,
            "makespan": None,
            "solver_time": None,
            "status": f"ERROR_SOLVE: {str(e)[:100]}"
        })

def process_folder(folder_path, output_csv="results.csv"):
    """Обходит все файлы в папке и обрабатывает каждый."""
    if not os.path.isdir(folder_path):
        print(f"Ошибка: {folder_path} не является папкой.")
        return

    # Собираем все файлы (можно фильтровать по расширению)
    files = []
    for root, dirs, filenames in os.walk(folder_path):
        for fname in filenames:
            # Парсер, вероятно, работает с текстовыми файлами. Добавьте другие расширения при необходимости.
            if fname.endswith(".txt") or fname.endswith(".dat") or "." not in fname:
                files.append(os.path.join(root, fname))

    if not files:
        print(f"В папке {folder_path} не найдено подходящих файлов.")
        return

    # Открываем CSV для записи
    with open(output_csv, mode='w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ["folder", "file", "instance_name", "makespan", "solver_time", "status"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for file_path in files:
            # Передаём writer и имя папки (для записи в CSV)
            # Но _solve_and_write ожидает csv_writer, а process_file – writer и folder_name
            # Немного переделаем вызов
            try:
                print(f"Обработка файла: {file_path}")
                start_total = time.time()
                processing_info = create_processing_info(file_path)
                if not processing_info:
                    print(f"  Предупреждение: файл {file_path} не дал данных. Пропускаем.")
                    continue

                # Если список блоков
                if isinstance(processing_info, list):
                    for idx, block_info in enumerate(processing_info):
                        inst_name = block_info.get("instance_name", f"{os.path.basename(file_path)}_block{idx+1}")
                        block_info["instance_name"] = inst_name
                        _solve_and_write_for_csv(block_info, inst_name, writer, folder_path, file_path)
                else:
                    inst_name = processing_info.get("instance_name", os.path.basename(file_path))
                    _solve_and_write_for_csv(processing_info, inst_name, writer, folder_path, file_path)

                print(f"  Завершён за {time.time() - start_total:.2f} сек\n")
            except Exception as e:
                print(f"Ошибка файла {file_path}: {e}")
                writer.writerow({
                    "folder": folder_path,
                    "file": os.path.basename(file_path),
                    "instance_name": "ERROR",
                    "makespan": None,
                    "solver_time": None,
                    "status": f"ERROR_FILE: {str(e)[:100]}"
                })

def _solve_and_write_for_csv(processing_info, instance_name, csv_writer, folder_name, file_path):
    """Вспомогательная функция для записи в CSV одного инстанса."""
    try:
        jobShopEnv = parse(processing_info)
        start_solve = time.time()
        results, jobShopEnv = run_CP_SAT(jobShopEnv, **SOLVER_PARAMS)
        solver_time = time.time() - start_solve

        makespan = None
        status = "UNKNOWN"
        if isinstance(results, dict):
            makespan = results.get("makespan") or results.get("objective")
            status = results.get("status", "UNKNOWN")
        else:
            if hasattr(jobShopEnv, "makespan"):
                makespan = jobShopEnv.makespan
            elif hasattr(jobShopEnv, "objective_value"):
                makespan = jobShopEnv.objective_value
            status = "SOLVED" if makespan is not None else "FAILED"

        csv_writer.writerow({
            "folder": folder_name,
            "file": os.path.basename(file_path),
            "instance_name": instance_name,
            "makespan": makespan,
            "solver_time": solver_time,
            "status": status
        })
        print(f"    Решено: makespan={makespan}, время={solver_time:.2f} сек")

    except Exception as e:
        print(f"    Ошибка решения {instance_name}: {e}")
        csv_writer.writerow({
            "folder": folder_name,
            "file": os.path.basename(file_path),
            "instance_name": instance_name,
            "makespan": None,
            "solver_time": None,
            "status": f"ERROR_SOLVE: {str(e)[:100]}"
        })

folderPath = "/home/samoh/database/"
resultFileName = "result.csv"

if __name__ == "__main__":
    process_folder(folderPath, resultFileName)
    print(f"Результаты сохранены в {resultFileName}")