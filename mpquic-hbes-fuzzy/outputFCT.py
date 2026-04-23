import os
import re

def getFCT(url_prefix):
    for root, _, files in os.walk(base_dir):
        for file_name in files:
            if file_name == "quic_client.log":
                file_path = os.path.join(root, file_name)
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        for line in f:
                            match = re.search(rf"{re.escape(url_prefix)}(\S+)", line)
                            if match:
                                value = match.group(1)
                                if value.endswith("ms"): # change s and ms to fix
                                    new_name = str(float(value[:-2]) / 1000)  # 去掉 "ms" 并 /1000
                                elif value.endswith("s"):
                                    # new_name = str(float(value[:-1]) * 1000)  # 去掉 "s" 并 *1000
                                    new_name = value[:-1]   #  去掉 "s"
                                else:
                                    new_name = value
                                print(new_name)
                except Exception as e:
                    print(f"Error reading {file_path}: {e}")
    print("------")

if __name__ == '__main__':
    # url_prefix_h = "random-high: "
    # url_prefix_m = "random-medium: "
    # url_prefix_l = "random-low: "
    url_prefix_0 = "random0: "
    url_prefix_1 = "random1: "
    url_prefix_all = "Completed all: "
    # url_prefix = "random"
    url_prefix = "random-single: "
    # url_prefix = "random-low-small: "
    # url_prefix = "random-high-big: "
    # url_prefix = "Completed all: "
    url_prefix_hs = "random-high-small: "
    url_prefix_lb = "random-low-big: "

    base_dir = "/home/server/Desktop/mpquic-hbes/ecf_results_3_stream/https_quic_20260204_095803_ecf_ban10rtt120_3stream"

    # getFCT(url_prefix)
    getFCT(url_prefix_all)
    # stream_list = [url_prefix_0, url_prefix_1]
    # for url in stream_list:
    #     getFCT(url)