import requests
import os

def check_live_source(url):
    """检查直播源是否有效"""
    try:
        # 使用 HEAD 请求减少流量消耗，设置 5 秒超时
        response = requests.head(url, timeout=5, allow_redirects=True)
        return response.status_code == 200
    except:
        try:
            # 部分服务器不支持 HEAD，尝试 GET 请求读取少量字节
            response = requests.get(url, timeout=5, stream=True)
            return response.status_code == 200
        except:
            return False

def main():
    input_file = 'channels.txt'
    output_file = 'output.txt'
    
    if not os.path.exists(input_file):
        print(f"错误: {input_file} 不存在")
        return

    unique_sources = {} # 使用字典去重：{url: name}
    
    # 1. 读取并去重
    with open(input_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and ',' in line:
                name, url = line.split(',', 1)
                if url not in unique_sources:
                    unique_sources[url] = name

    print(f"去重完成，剩余 {len(unique_sources)} 条待检测...")

    # 2. 检查有效性并写入文件
    valid_count = 0
    with open(output_file, 'w', encoding='utf-8') as f:
        for url, name in unique_sources.items():
            print(f"正在检测: {name} ({url})")
            if check_live_source(url):
                f.write(f"{name},{url}\n")
                valid_count += 1
                print(">> [有效]")
            else:
                print(">> [失效]")

    print(f"任务完成！有效源共计: {valid_count}")

if __name__ == "__main__":
    main()
