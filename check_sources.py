import requests
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

# 配置
INPUT_FILE = 'channels.txt'
OUTPUT_FILE = 'output.txt'
MAX_WORKERS = 20  # 同时开启的线程数，建议 20-30 之间
TIMEOUT = 5       # 每个链接的超时时间

def check_live_source(item):
    """
    检查单个直播源
    item: (name, url)
    返回: (name, url, is_valid)
    """
    name, url = item
    try:
        # 尝试 HEAD 请求
        response = requests.head(url, timeout=TIMEOUT, allow_redirects=True)
        if response.status_code == 200:
            return name, url, True
    except:
        pass
    
    try:
        # 备选 GET 请求（只读头部）
        response = requests.get(url, timeout=TIMEOUT, stream=True)
        return name, url, response.status_code == 200
    except:
        return name, url, False

def main():
    if not os.path.exists(INPUT_FILE):
        print("错误: channels.txt 不存在")
        return

    # 1. 预处理：去重
    unique_tasks = {}
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and ',' in line:
                name, url = line.split(',', 1)
                if url not in unique_tasks:
                    unique_tasks[url] = name

    print(f"去重完成，剩余 {len(unique_tasks)} 个源，开始多线程检测...")

    # 2. 多线程执行
    valid_sources = []
    task_list = [(name, url) for url, name in unique_tasks.items()]
    
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # 提交所有任务
        future_to_url = {executor.submit(check_live_source, task): task for task in task_list}
        
        done_count = 0
        for future in as_completed(future_to_url):
            name, url, is_valid = future.result()
            done_count += 1
            if is_valid:
                valid_sources.append(f"{name},{url}")
            
            # 每检测 100 条打印一次进度
            if done_count % 100 == 0:
                print(f"进度: {done_count}/{len(task_list)}...")

    # 3. 写入结果
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write('\n'.join(valid_sources))

    print(f"检测结束！有效源: {len(valid_sources)}，结果已保存至 {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
