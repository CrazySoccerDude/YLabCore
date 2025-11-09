"""LCR_ADMX2001 串口通信原始测试脚本。

用于批量发送命令（尤其是 ``help`` 类指令）并收集响应，
便于整理仪器交互文档。
"""

from __future__ import annotations

import re
import serial
import time
from typing import Iterable


ANSI_PATTERN = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")


def strip_ansi(lines: Iterable[str]) -> list[str]:
    """移除串口输出中的 ANSI 控制字符。"""

    cleaned: list[str] = []
    for line in lines:
        # 仪器会返回 \x1b7、\x1b8 等控制字符，需要一并清理。
        no_escape = line.replace("\x1b7", "").replace("\x1b8", "")
        cleaned.append(ANSI_PATTERN.sub("", no_escape))
    return cleaned


def read_response(ser: serial.Serial, *, timeout: float = 3.0, post_prompt_wait: float = 0.4) -> list[str]:
    """读取串口响应。

    - 遇到提示符 ``ADMX2001>`` 后不会立即退出，而是再等待
      ``post_prompt_wait`` 秒，以捕获 help 输出等多行文本。
    - 如果提示符出现两次，也视为输出完成。
    - 遇到 ``PASSWORD>`` 也停止读取，因为这是密码输入提示。
    """

    lines: list[str] = []
    start = time.time()
    prompt_seen = 0
    last_line_time = time.time()

    while time.time() - start < timeout:
        raw = ser.readline()
        if not raw:
            if prompt_seen and (time.time() - last_line_time) > post_prompt_wait:
                break
            continue

        decoded = raw.decode(errors="ignore").rstrip("\r\n")
        if decoded:
            lines.append(decoded)
            last_line_time = time.time()
            if "ADMX2001>" in decoded:
                prompt_seen += 1
                if prompt_seen >= 2:
                    break
            elif "PASSWORD>" in decoded:
                # 遇到密码提示，立即停止读取
                break

    return strip_ansi(lines)


def send_command(ser: serial.Serial, cmd: str, *, wait: float = 0.5) -> list[str]:
    """发送单条命令并返回响应。"""

    full_cmd = f"{cmd}\r\n"
    print(f"[SEND] {repr(full_cmd)}")
    ser.write(full_cmd.encode())
    time.sleep(wait)
    response = read_response(ser)
    if not response:
        print("[WARN] 未收到响应")
        return []
    return response


def send_command_with_ending(ser: serial.Serial, cmd: str, ending: str, *, wait: float = 0.5) -> list[str]:
    """发送单条命令并返回响应，使用指定的行结束符。"""

    full_cmd = f"{cmd}{ending}"
    print(f"[SEND] {repr(full_cmd)}")
    ser.write(full_cmd.encode())
    time.sleep(wait)
    response = read_response(ser)
    if not response:
        print("[WARN] 未收到响应")
        return []
    return response


def main() -> None:
    port = "COM4"
    baudrate = 115200
    timeout = 2.0
    ser = serial.Serial(
        port=port,
        baudrate=baudrate,
        bytesize=serial.EIGHTBITS,
        parity=serial.PARITY_NONE,
        stopbits=serial.STOPBITS_ONE,
        timeout=timeout,
        xonxoff=False,
        rtscts=False,
        dsrdtr=False,
    )
    print(f"[INFO] 打开串口 {port}，波特率 {baudrate}")

    # 选择测试模式：'help' 或 'commands' 或 'specific' 或 'line_ending_test'
    test_mode = "line_ending_test"  # 改为 'help' 可运行 help 测试，'commands' 运行实际命令，'line_ending_test' 测试行结束符

    if test_mode == "help":
        commands = [
            "help",
            "help z",
            "help temperature",
            "help initiate",
            "help abort",
            "help frequency",
            "help magnitude",
            "help offset",
            "help setgain",
            "help trig_mode",
            "help average",
            "help display",
            "help mdelay",
            "help tdelay",
            "help count",
            "help tcount",
            "help sweep_type",
            "help sweep_scale",
            "help compensation",
            "help rdcomp",
            "help storecomp",
            "help calibrate",
            "help rdcal",
            "help resetcal",
            "help storecal",
            "help get_attr",
            "help error_check",
            "help history",
            "help reset",
            "help selftest",
            "help gpio_ctrl",
        ]
    elif test_mode == "commands":
        # 实际命令测试
        commands = [
            "*idn?",  # 获取仪器ID
            "temperature",  # 获取温度
            "frequency 1000",  # 设置频率1kHz
            "magnitude 1.0",  # 设置幅度1.0V
            "offset 0.0",  # 设置偏移0V
            "setgain auto",  # 自动增益
            "average 10",  # 设置平均次数
            "count 5",  # 设置采样计数
            "display 6",  # 设置显示模式为阻抗(R,X)
            "trig_mode internal",  # 内部触发
            "z",  # 执行测量
            "get_attr",  # 获取属性
            "error_check on",  # 启用错误检查
            "reset",  # 重置模块
        ]
    else:
        # 特定命令测试 - 完整的calibration过程
        commands = [
            "calibrate",  # 查看当前状态
            "calibrate open",  # 执行开路校准
            #"calibrate short",  # 执行短路校准
            #"calibrate",  # 再次查看状态
            "calibrate commit",  # 提交校准系数
        ]

    if test_mode == "line_ending_test":
        # 测试不同行结束符对标准命令的影响
        test_commands = ["frequency 1000", "magnitude 1.0", "temperature"]
        endings = ["\r\n", "\r", "\n"]
        
        print("[INFO] 测试不同行结束符对标准命令的影响")
        print("=" * 80)
        
        for cmd in test_commands:
            print(f"\n[测试命令] {cmd}")
            print("-" * 40)
            
            for ending in endings:
                print(f"\n[行结束符] {repr(ending)}")
                # 使用 cls 清屏，避免缓存数据干扰。
                send_command(ser, "cls", wait=0.2)
                
                response = send_command_with_ending(ser, cmd, ending, wait=1.0)
                print("[RECV]")
                if response:
                    for line in response:
                        print(f"  {line}")
                else:
                    print("  [无响应]")
                print("-" * 30)
        
        return  # 测试完成后退出

    try:
        ser.flushInput()
        ser.flushOutput()

        for i, cmd in enumerate(commands):
            # 使用 cls 清屏，避免缓存数据干扰。
            send_command(ser, "cls", wait=0.2)
            
            if cmd == "calibrate commit":
                # 特殊处理commit命令，因为需要密码
                full_cmd = f"{cmd}\r"
                print(f"[SEND] {repr(full_cmd)}")
                ser.write(full_cmd.encode())
                
                # 等待PASSWORD>提示
                response = read_response(ser, timeout=2.0)
                print("[RECV]")
                if response:
                    for line in response:
                        print(f"  {line}")
                
                # 等待PASSWORD>提示
                response = read_response(ser, timeout=2.0)
                print("[RECV]")
                if response:
                    for line in response:
                        print(f"  {line}")
                
                # PASSWORD>出现后，立即发送密码，不要任何延迟
                print("[SEND PASSWORD] 'Analog123'")
                ser.write(b"Analog123\n")  # 立即发送
                
                # 立即读取响应
                password_response = read_response(ser, timeout=1.0)
                if password_response:
                    for line in password_response:
                        print(f"  {line}")
                        if "success" in line.lower() or "committed" in line.lower():
                            print("[SUCCESS] Calibration committed!")
                            return
                print("-" * 60)
            else:
                response = send_command(ser, cmd, wait=1.0)
                print("[RECV]")
                if response:
                    for line in response:
                        print(f"  {line}")
                else:
                    print("  [无响应]")
                print("-" * 60)

    finally:
        ser.close()
        print("[INFO] 串口已关闭")


if __name__ == "__main__":
    main()
