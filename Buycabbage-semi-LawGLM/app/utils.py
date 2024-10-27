import concurrent.futures
from tqdm import tqdm


def multi_thread_excute(all_tasks, parralle_num=20):
    """
    多线程运行任务，注意，返回结果序并不和all_tasks一致，请设计好task的输出，能够通过map的形式找到对应的答案
    """

    def multi_thread_excute_helper(tasks):
        with concurrent.futures.ThreadPoolExecutor() as executor:
            exe_tasks = [executor.submit(*task) for task in tasks]
            results = [future.result() for future in concurrent.futures.as_completed(exe_tasks)]
        return results

    all_results = []
    for i in tqdm(range(0, len(all_tasks), parralle_num)):
        all_results += multi_thread_excute_helper(all_tasks[i : i + parralle_num])
    return all_results
