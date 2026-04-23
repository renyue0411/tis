import os

def rename_folders():
    current_dir = "./results_2_diff_streams_2"  # 获取目录
    for folder in os.listdir(current_dir):
        folder_path = os.path.join(current_dir, folder)
        if os.path.isdir(folder_path) and "mptcp-" in folder:
            new_name = folder.split("mptcp-")[-1]  # 获取 "mptcp-" 之后的部分
            new_path = os.path.join(current_dir, new_name)
            os.rename(folder_path, new_path)
            print(f'Renamed: "{folder}" → "{new_name}"')

if __name__ == "__main__":
    rename_folders()