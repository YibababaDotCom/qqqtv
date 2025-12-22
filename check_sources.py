import requests
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

# 配置
INPUT_FILE = 'channels.txt'
OUTPUT_FILE = 'output.txt'
MAX_WORKERS = 30  # 6000条数据建议 30 线程，兼顾速度与稳定性
TIMEOUT = 5

def check_live_source(name, url, index):
    """检测函数，返回索引以便后续恢复顺序"""
    try:
        # 尝试 HEAD 请求
        response = requests.head(url, timeout=TIMEOUT, allow_redirects=True)
        if response.status_code == 200:
            return index, name, url, True
    except:
        pass
    
    try:
        # 备选 GET 请求
        response = requests.get(url, timeout=TIMEOUT, stream=True)
        return index, name, url, response.status_code == 200
    except:
        return index, name, url, False

def main():
    if not os.path.exists(INPUT_FILE):
        return

    tasks = []
    seen_urls = set()
    
    # 1. 读取文件并去重，同时记录原始索引
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        for idx, line in enumerate(f):
            line = line.strip()
            if line and ',' in line:
                name, url = line.split(',', 1)
                if url not in seen_urls:
                    seen_urls.add(url)
                    tasks.append((name, url, idx))

    print(f"总计 {len(tasks)} 个唯一源，开始并发检测...")

    results = []
    # 2. 多线程检测
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_task = {executor.submit(check_live_source, n, u, i): i for n, u, i in tasks}
        
        count = 0
        for future in as_completed(future_to_task):
            res = future.result() # (index, name, url, is_valid)
            if res[3]: # 如果有效
                results.append(res)
            
            count += 1
            if count % 100 == 0:
                print(f"已完成: {count}/{len(tasks)}")

    # 3. 按照原始文件的索引排序，保证顺序不变
    results.sort(key=lambda x: x[0])

    # 4. 写入文件
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        for _, name, url, _ in results:
            f.writelines(f"{name},{url}\n")

    print(f"检测完毕，有效源已写入 {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
