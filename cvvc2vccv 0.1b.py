import tkinter as tk
from tkinter import filedialog, messagebox
import configparser
import os
import subprocess

# 读取规则文件，忽略重复的选项
def load_rules(filename):
    config = configparser.ConfigParser()
    config.optionxform = str  # 保持大小写
    config.read(filename, encoding='utf-8')
    cv_rules = {}
    v_rules = {}
    c_rules = {}
    tial_rules = {}
    if 'CVRULE' in config:
        for key in config['CVRULE']:
            cv_rules[key] = config['CVRULE'][key].split(',')
    if 'VRULE' in config:
        for key in config['VRULE']:
            v_rules[key] = config['VRULE'][key].split(',')
    if 'CRULE' in config:
        for key in config['CRULE']:
            c_rules[key] = config['CRULE'][key].split(',')
    if 'TIALRULE' in config:
        for key in config['TIALRULE']:
            tial_rules[key] = config['TIALRULE'][key].split(',')
    return cv_rules, v_rules, c_rules, tial_rules

# 应用CVRULE和VRULE替换逻辑
def apply_cv_vc_rules(cv_rules, v_rules, c_rules, pinyin, name, timing):
    results = []
    if ' ' in pinyin and not pinyin.startswith('-'):
        left, right = pinyin.split(' ', 1)
        left = v_rules.get(left, [left])[0]
        right = c_rules.get(right, [right])[0] if right in c_rules else cv_rules.get(right, [right])[0]
        new_pinyin = f"{left} {right}"
        results.append(f"{name}={new_pinyin},{','.join(timing)}")
    else:
        if pinyin.startswith('- '):
            right = pinyin[2:]
            new_pinyin = f"- {cv_rules.get(right, [right])[0]}"
            results.append(f"{name}={new_pinyin},{','.join(timing)}")
        else:
            rule_items = cv_rules.get(pinyin, [pinyin])
            for item in rule_items:
                results.append(f"{name}={item},{','.join(timing)}")
    return results

# 应用规则到oto.ini
def apply_rules(oto_file, cv_rules, v_rules, c_rules, tial_rules, apply_tial_rule, max_entries):
    result = []
    seen_entries = {}  # 用于跟踪重复的条目及其编号
    debug_info = []  # 用于保存调试信息

    # 读取并按采样名部分（音素名）排序oto.ini条目 (按“yang”部分排序)
    with open(oto_file, 'r', encoding='utf-8', errors='ignore') as file:
        lines = file.readlines()
    lines.sort(key=lambda x: x.split('=')[1].split(',')[0].strip().lower())

    # 添加初始状态到调试信息
    debug_info.append("Initial sorted lines:")
    debug_info.extend(lines)

    unchanged_result = []  # 用于保存未更改的条目
    modified_result = []  # 用于保存更名和新增条目

    for line in lines:
        parts = line.strip().split('=')
        if len(parts) != 2:
            continue
        name, data = parts
        pinyin, *timing = data.split(',')

        if not pinyin:
            continue

        # 应用CVRULE、VRULE和CRULE替换
        replacements = apply_cv_vc_rules(cv_rules, v_rules, c_rules, pinyin, name, timing)
        
        # 如果没有符合任何替换规则的，保留原条目
        if len(replacements) == 1 and replacements[0] == line:
            unchanged_result.append(line)
        else:
            modified_result.extend(replacements)

    # 添加应用CVRULE、VRULE和CRULE后的结果到调试信息
    debug_info.append("\nAfter CVRULE, VRULE and CRULE:")
    debug_info.extend(modified_result)

    # 第二次应用TIALRULE
    final_result = []
    for line in modified_result:
        name, data = line.split('=')
        pinyin, *timing = data.split(',')

        # 处理有“-”符号的条目，应用TIALRULE
        if apply_tial_rule and pinyin.startswith('-'):
            parts = pinyin.split('- ', 1)
            if len(parts) == 2:
                right = parts[1]
                for key, values in tial_rules.items():
                    if right in values:
                        pinyin = f"- {key}"
                        break

        final_result.append(f"{name}={pinyin},{','.join(timing)}")

    # 添加应用TIALRULE后的结果到调试信息
    debug_info.append("\nAfter TIALRULE:")
    debug_info.extend(final_result)

    # 合并未更名条目与更名条目
    final_result = unchanged_result + final_result

    # 如果max_entries为0（无限制），则所有条目需要加上序号
    if max_entries == 0:
        renamed_result = []
        seen_entries = {}
        for line in final_result:
            name, data = line.split('=')
            pinyin, *timing = data.split(',')

            entry_key = pinyin.split(',')[0]
            if entry_key in seen_entries:
                seen_entries[entry_key] += 1
                pinyin = f"{pinyin}_{seen_entries[entry_key]}"
            else:
                seen_entries[entry_key] = 1

            renamed_result.append(f"{name}={pinyin},{','.join(timing)}")
    else:
        renamed_result = []
        seen_entries = {}
        for line in final_result:
            name, data = line.split('=')
            pinyin, *timing = data.split(',')

            entry_key = pinyin.split(',')[0]
            if entry_key in seen_entries:
                if seen_entries[entry_key] < max_entries:
                    seen_entries[entry_key] += 1
                    pinyin = f"{pinyin}_{seen_entries[entry_key]}"
                else:
                    continue
            else:
                seen_entries[entry_key] = 1

            renamed_result.append(f"{name}={pinyin},{','.join(timing)}")

    # 对采样名部分进行最终排序 (按采样名的“_cang_sang_yang.wav”部分排序)
    renamed_result.sort(key=lambda x: x.split('=')[0].strip().lower())

    # 获取用户文档目录路径
    user_documents = os.path.join(os.path.expanduser("~"), "Documents")
    debug_file_path = os.path.join(user_documents, "debug_info.txt")

    # 输出调试信息到文件
    with open(debug_file_path, "w", encoding='utf-8') as debug_file:
        for info in debug_info:
            debug_file.write(info + "\n")

    return renamed_result

# 保存新的oto.ini
def save_new_oto(filename, content):
    with open(filename, 'w', encoding='utf-8') as file:
        for line in content:
            file.write(line + '\n')

def select_oto_file():
    global oto_file
    oto_file = filedialog.askopenfilename(title="选择oto.ini文件", filetypes=[("INI文件", "*.ini")])
    if oto_file:
        label_oto.config(text=f"已加载文件：{oto_file}")

def select_rule_file():
    global rule_file
    rule_file = filedialog.askopenfilename(title="选择InPutRule.ini文件", filetypes=[("INI文件", "*.ini")])
    if rule_file:
        label_rule.config(text=f"已加载文件：{rule_file}")

def open_export_location():
    user_documents = os.path.join(os.path.expanduser("~"), "Documents")
    subprocess.Popen(f'explorer "{user_documents}"')

def process_files():
    if not oto_file or not rule_file:
        messagebox.showerror("错误", "请先选择oto.ini和InPutRule.ini文件")
        return
    try:
        max_entries = repeats_entry.get()
        if not max_entries:
            max_entries = 0
        else:
            max_entries = int(max_entries)
    except ValueError:
        max_entries = 0  # 无效输入视为无限制

    apply_tial_rule = tial_rule_var.get()

    cv_rules, v_rules, c_rules, tial_rules = load_rules(rule_file)
    new_oto_content = apply_rules(oto_file, cv_rules, v_rules, c_rules, tial_rules, apply_tial_rule, max_entries)
    
    user_documents = os.path.join(os.path.expanduser("~"), "Documents")
    save_path = os.path.join(user_documents, 'new_oto.ini')
    
    save_new_oto(save_path, new_oto_content)
    label_process.config(text=f"处理完成，新文件保存在：{save_path}")

root = tk.Tk()
root.title("cvvc2vccv批量处理器")
root.geometry("400x400")

oto_file = ""
rule_file = ""

label_rule = tk.Label(root, text="选择InPutRule.ini文件", pady=10)
label_rule.pack()

btn_rule = tk.Button(root, text="选择InPutRule.ini文件", command=select_rule_file)
btn_rule.pack()

label_oto = tk.Label(root, text="选择oto.ini文件", pady=10)
label_oto.pack()

btn_oto = tk.Button(root, text="选择oto.ini文件", command=select_oto_file)
btn_oto.pack()

label_repeats = tk.Label(root, text="最大条目数：（0为无限制）", pady=10)
label_repeats.pack()

repeats_entry = tk.Entry(root)
repeats_entry.pack()

# 添加选择框来询问用户是否要应用TIAL规则
tial_rule_var = tk.BooleanVar()
tial_rule_var.set(False)  # 默认不应用TIAL规则
tial_rule_check = tk.Checkbutton(root, text="应用TIAL规则", variable=tial_rule_var)
tial_rule_check.pack()

label_process = tk.Label(root, text="", pady=10)
label_process.pack()

btn_process = tk.Button(root, text="处理文件", command=process_files)
btn_process.pack()

btn_open_location = tk.Button(root, text="打开导出位置", command=open_export_location)
btn_open_location.pack()

root.mainloop()
