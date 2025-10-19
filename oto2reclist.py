import tkinter as tk
from tkinter import filedialog, messagebox
import os

def generate_reclist(input_path, output_path):
    """
    根据 oto.ini 文件生成录音列表的核心函数。

    参数:
    input_path (str): 输入的 oto.ini 文件路径。
    output_path (str): 输出的录音列表 .txt 文件路径。

    返回:
    int: 成功生成的唯一文件名数量。

    异常:
    FileNotFoundError: 如果输入文件不存在。
    IOError: 如果文件读写过程中发生错误。
    """
    # 1. 检查输入文件是否存在
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"错误：输入文件 '{os.path.basename(input_path)}' 不存在。")

    unique_filenames = set()

    try:
        # 尝试使用 'utf-8' 或 'shift_jis' 编码读取文件
        try:
            with open(input_path, 'r', encoding='utf-8') as f_in:
                lines = f_in.readlines()
        except UnicodeDecodeError:
            with open(input_path, 'r', encoding='shift_jis', errors='ignore') as f_in:
                lines = f_in.readlines()

        for line in lines:
            # 2. 只要.ini的列名：通过'='分割，获取第一部分
            if '=' not in line:
                continue
            
            column_name = line.split('=', 1)[0].strip()
            
            # 3. 省略'.'以及其右边的部分
            if '.' in column_name:
                base_name = column_name.rsplit('.', 1)[0]
            else:
                base_name = column_name
            
            # 4. 减去重复的采样名
            unique_filenames.add(base_name)

    except Exception as e:
        raise IOError(f"读取文件 '{os.path.basename(input_path)}' 时发生错误: {e}")

    # 将集合转换为列表并排序
    sorted_filenames = sorted(list(unique_filenames))

    try:
        # 5. 将结果写入输出文件
        with open(output_path, 'w', encoding='utf-8') as f_out:
            for name in sorted_filenames:
                f_out.write(name + '\n')
    except Exception as e:
        raise IOError(f"写入文件 '{os.path.basename(output_path)}' 时发生错误: {e}")
    
    return len(sorted_filenames)

# --- GUI 相关函数 ---

def select_input_file():
    """打开文件对话框让用户选择 oto.ini 文件"""
    global input_filepath
    filepath = filedialog.askopenfilename(
        title="选择 oto.ini 文件",
        filetypes=[("INI 文件", "*.ini"), ("所有文件", "*.*")]
    )
    if filepath:
        input_filepath = filepath
        # 更新标签，显示已选择的文件路径
        input_label.config(text=f"已选输入文件:\n{filepath}", fg="blue")

def select_output_file():
    """打开文件对话框让用户选择保存位置和文件名"""
    global output_filepath
    filepath = filedialog.asksaveasfilename(
        title="选择保存位置和文件名",
        initialfile="reclist.txt",
        defaultextension=".txt",
        filetypes=[("文本文档", "*.txt"), ("所有文件", "*.*")]
    )
    if filepath:
        output_filepath = filepath
        # 更新标签，显示将要保存的路径
        output_label.config(text=f"将保存至:\n{filepath}", fg="green")

def start_processing():
    """执行生成录音表的主流程"""
    # 检查是否已选择输入文件
    if not input_filepath:
        messagebox.showerror("操作错误", "请先选择一个 oto.ini 输入文件。")
        return
    
    # 如果用户未指定输出路径，则主动弹出保存对话框
    if not output_filepath:
        select_output_file()
        # 如果用户在保存对话框中点击了取消，则中止操作
        if not output_filepath:
            return

    try:
        # 调用核心逻辑函数
        count = generate_reclist(input_filepath, output_filepath)
        # 弹出成功提示框
        messagebox.showinfo(
            "处理成功",
            f"录音列表已成功生成！\n\n共导出 {count} 个唯一的采样名。\n\n文件保存在:\n{output_filepath}"
        )
        status_label.config(text=f"成功生成文件: {os.path.basename(output_filepath)}", fg="dark green")
    except Exception as e:
        # 如果发生错误，弹出错误提示框
        messagebox.showerror("处理失败", str(e))
        status_label.config(text="处理失败，请检查文件或权限。", fg="red")


# --- 主程序和GUI布局 ---

if __name__ == '__main__':
    # 全局变量，用于存储用户选择的文件路径
    input_filepath = ""
    output_filepath = ""

    # 创建主窗口
    root = tk.Tk()
    root.title("oto.ini 录音表生成工具")
    root.geometry("450x380")  # 设置窗口初始大小
    root.resizable(False, False) # 禁止调整窗口大小

    # --- 创建界面组件 ---
    
    # 主框架
    main_frame = tk.Frame(root, padx=20, pady=15)
    main_frame.pack(expand=True, fill=tk.BOTH)

    # 1. 选择输入文件按钮
    btn_input = tk.Button(main_frame, text="1. 选择 oto.ini 文件", command=select_input_file, width=30)
    btn_input.pack(pady=(5, 5))

    # 显示输入文件路径的标签
    input_label = tk.Label(main_frame, text="尚未选择输入文件", wraplength=400, justify=tk.CENTER)
    input_label.pack(pady=(0, 15))

    # 2. 选择输出位置按钮
    btn_output = tk.Button(main_frame, text="2. 选择保存位置", command=select_output_file, width=30)
    btn_output.pack(pady=5)

    # 显示输出文件路径的标签
    output_label = tk.Label(main_frame, text="将默认保存为 reclist.txt", wraplength=400, justify=tk.CENTER)
    output_label.pack(pady=(0, 20))

    # 3. 执行处理的按钮
    btn_process = tk.Button(main_frame, text="3. 生成录音表", command=start_processing, font=("Helvetica", 12, "bold"), bg="#4CAF50", fg="white")
    btn_process.pack(pady=10, ipady=5, fill=tk.X)

    # 状态栏标签
    status_label = tk.Label(root, text="欢迎使用", bd=1, relief=tk.SUNKEN, anchor=tk.W, padx=10)
    status_label.pack(side=tk.BOTTOM, fill=tk.X)

    # 启动GUI事件循环
    root.mainloop()