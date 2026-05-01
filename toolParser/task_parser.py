from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
import re
import os


@dataclass
class Operation:
    operation_id: int
    processing_times: Dict[str, int] = field(default_factory=dict)
    predecessors: List[int] = field(default_factory=list)


@dataclass
class Job:
    job_id: int
    operations: List[Operation] = field(default_factory=list)


@dataclass
class WorkBlock:
    metadata: str
    total_jobs: int = 0
    total_operations: int = 0
    predecessors: List[Tuple[int, int]] = field(default_factory=list)
    job_operation_ids: List[List[int]] = field(default_factory=list)


def parse_time_to_seconds(time_str: str) -> int:
    if time_str == '00:00:00':
        secondsInMonth = 31 * 24 * 60 * 60
        return secondsInMonth
    parts = time_str.split(':')
    return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])


def parse_times_block(lines: List[str], nr_machines: int) -> List[Operation]:
    operations = []
    for op_id, line in enumerate(lines):
        line = line.strip()
        if not line or line.startswith('TIMES') or line.isdigit():
            continue
        parts = line.split()
        if len(parts) != nr_machines:
            parts += ['0_00:00:00'] * (nr_machines - len(parts))
        proc_times = {}
        for machine_idx, part in enumerate(parts[:nr_machines]):
            if '_' in part:
                _, time_str = part.split('_', 1)
                seconds = parse_time_to_seconds(time_str)
            else:
                seconds = 0
            proc_times[str(machine_idx)] = seconds
        operations.append(Operation(operation_id=op_id, processing_times=proc_times))
    return operations


def parse_work_blocks(content: str) -> List[WorkBlock]:
    """
    Парсит блоки work.
    Формат:
    work
    <metadata>   (содержит как минимум 3 числа: ... total_jobs total_ops total_preds ...)
    <строки с числами>
    Первые total_jobs строк -> job_operation_ids (списки операций для каждого задания)
    Остальные строки (с двумя числами) -> predecessors
    """
    work_blocks = []
    # Ищем блоки от "work" до следующего "work" или конца файла
    pattern = r'work\s*\n([^\n]+)\n((?:(?!\nwork\s*\n).)*)'
    matches = re.findall(pattern, content, re.DOTALL | re.MULTILINE)
    
    for metadata, data in matches:
        block = WorkBlock(metadata=metadata.strip())
        meta_parts = metadata.strip().split()
        # По вашему описанию: первые два элемента — даты, третий — total_jobs
        if len(meta_parts) >= 3:
            block.total_jobs = int(meta_parts[2])
        if len(meta_parts) >= 4:
            block.total_operations = int(meta_parts[3])
        # (total_predecessors может быть в meta_parts[4], но необязательно)
        
        lines = [line.strip() for line in data.strip().split('\n') if line.strip()]
        # Читаем первые total_jobs строк как job_operation_ids
        for i in range(min(block.total_jobs, len(lines))):
            parts = list(map(int, lines[i].split()))
            block.job_operation_ids.append(parts)
        # Остальные строки (начиная с индекса total_jobs) — predecessors (если 2 числа)
        for i in range(block.total_jobs, len(lines)):
            parts = list(map(int, lines[i].split()))
            if len(parts) == 2:
                block.predecessors.append((parts[0], parts[1]))
            # Если вдруг строка содержит другое количество чисел — игнорируем или логируем
        work_blocks.append(block)
    return work_blocks


def parse_full_file(content: str, nr_machines: int) -> Tuple[List[Operation], List[WorkBlock]]:
    times_match = re.search(r'TIMES\n(.*?)(?=\n\s*work\s*\n|\n\s*$)', content, re.DOTALL)
    times_lines = times_match.group(1).strip().split('\n') if times_match else []
    times_data_lines = []
    for line in times_lines:
        line = line.strip()
        if line.isdigit():
            continue
        if line and all(c in '01 ' for c in line) and len(line.split()) > 10:
            continue
        times_data_lines.append(line)
    operations = parse_times_block(times_data_lines, nr_machines)
    work_blocks = parse_work_blocks(content)
    return operations, work_blocks


def get_nr_machines_from_content(content: str) -> int:
    match = re.search(r'TOOLS\s*\n\s*(\d+)', content)
    if match:
        return int(match.group(1))
    return 0


def create_processing_info(fileName: str) -> dict:   # теперь возвращает dict, а не list
    with open(fileName, 'r', encoding='utf-8') as f:
        content = f.read()

    nr_machines = get_nr_machines_from_content(content)
    if nr_machines == 0:
        nr_machines = 20

    global_operations, work_blocks = parse_full_file(content, nr_machines)
    if not work_blocks:
        return {}

    base_name = os.path.splitext(os.path.basename(fileName))[0]

    # Объединяем все jobs из всех work-блоков в один список
    all_jobs = []
    global_op_id_to_local_index = {}  # для построения матрицы setup_times
    current_op_index = 0

    for idx, block in enumerate(work_blocks):
        # Определяем используемые operation_id в блоке
        used_op_ids = set()
        for job_ops in block.job_operation_ids:
            used_op_ids.update(job_ops)
        for pred_id, succ_id in block.predecessors:
            used_op_ids.add(pred_id)
            used_op_ids.add(succ_id)

        # Создаём копии операций блока
        block_ops = {}
        for op_id in used_op_ids:
            if op_id < len(global_operations):
                original = global_operations[op_id]
                block_ops[op_id] = Operation(
                    operation_id=original.operation_id,
                    processing_times=original.processing_times.copy(),
                    predecessors=[]
                )

        # Добавляем predecessors
        for pred_id, succ_id in block.predecessors:
            if pred_id in block_ops and succ_id in block_ops:
                if pred_id not in block_ops[succ_id].predecessors:
                    block_ops[succ_id].predecessors.append(pred_id)

        # Строим задания блока
        for job_id, op_ids in enumerate(block.job_operation_ids):
            job_ops = [block_ops[oid] for oid in op_ids if oid in block_ops]
            if job_ops:
                # ----- СОРТИРОВКА: операции без предшественников идут первыми -----
                job_ops.sort(key=lambda op: 0 if not op.predecessors else 1)
                all_jobs.append(Job(job_id=len(all_jobs), operations=job_ops))  # новый job_id глобально

        # Запоминаем соответствие глобальных operation_id -> локальный индекс для setup_times
        for op_id in block_ops:
            if op_id not in global_op_id_to_local_index:
                global_op_id_to_local_index[op_id] = current_op_index
                current_op_index += 1

    # После обработки всех блоков строим единую матрицу sequence_dependent_setup_times
    total_unique_ops = len(global_op_id_to_local_index)
    zero_matrix = [[0] * total_unique_ops for _ in range(total_unique_ops)]
    setup_times = {f"machine_{m+1}": [row[:] for row in zero_matrix] for m in range(nr_machines)}

    # Преобразуем all_jobs в нужный формат
    jobs_list = []
    for job in all_jobs:
        ops_list = []
        for op in job.operations:
            proc_times = {f"machine_{int(m)+1}": t for m, t in op.processing_times.items()}
            ops_list.append({
                "operation_id": op.operation_id,
                "processing_times": proc_times,
                "predecessors": op.predecessors if op.predecessors else None
            })
        jobs_list.append({"job_id": job.job_id, "operations": ops_list})

    processing_info = {
        "instance_name": base_name,
        "nr_machines": nr_machines,
        "jobs": jobs_list,
        "sequence_dependent_setup_times": setup_times
    }
    return processing_info


if __name__ == '__main__':
    infos = create_processing_info("test.txt")
    # for info in infos:
    #     print(f"\nInstance: {info['instance_name']}, machines: {info['nr_machines']}, jobs: {len(info['jobs'])}")
    #     for job in info['jobs']:
    #         for op in job['operations']:
    #             print(f"  Op {op['operation_id']}: predecessors {op['predecessors']}")

    print(infos)