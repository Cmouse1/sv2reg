#!/usr/bin/env python3
"""
SV to Python Register Generator

从 SystemVerilog 模块例化代码生成 address_planner 风格的 Python 寄存器代码。

输入格式:
    module <name> ["module description"]
    //<group_name> ["group description"]
    .<port_name> [ ( <signal> ) ] [,] // <direction> [<width>] [sw=X] [hw=Y] [init=X] ["field description"]
    endmodule

    其中 () 内信号名和尾部逗号均可省略，以下写法等价:
      .rst_n ( pin_rst ) , // input "reset"
      .rst_n ,               // input "reset"
      .rst_n                 // input "reset"

    位宽支持两种写法:
      - [MSB:LSB]   如 [10:0]  →  11 bit
      - width=N     如 width=8 →  8 bit
      不写位宽时默认 1 bit。

    方向决定 access 类型（可通过 sw=/hw= 手动覆盖）:
      - input  →  sw=ReadWrite, hw=ReadOnly
      - output →  sw=ReadOnly,  hw=ReadWrite
      例: // input, sw=ReadOnly, hw=ReadOnly   (强制 RO)
          // input, hw=WriteOnly                (只覆盖 hw)

    init=X 可手动指定 init_value（默认按位宽全填 0），支持:
      - init=0x5A  （十六进制）
      - init=42     （十进制）
      - init=0b1010（二进制）

    行首 // 为组分割，组内信号位宽总和超过 32 时自动拆分:
      - 第一块保持原名
      - 溢出块加 _ex0, _ex1... 后缀

    "" 内的文字自动填入 description 字段。

用法:
    python sv2reg.py demo.sv                          # 默认输出 <module>_reg_rf_gen.py
    python sv2reg.py demo.sv -o output.py             # 指定输出文件
    python sv2reg.py demo.sv -r                       # 生成后自动执行

示例:
    module sys_pcie_eth_wrap
    //lane "lane registers"
    .lanea      // input "enable"
    .lanec      // input [10:0] "counter"
    .data       // output, width=8 "data bus"
    .ro_reg     // input, sw=ReadOnly, hw=ReadOnly "force read-only"
    .init_reg   // input, width=8, init=0x5A "with init value"
    endmodule
"""

import re
import sys
import argparse


def parse_sv(filepath: str):
    """
    解析 SV 文件，返回 (module_name, module_desc, groups)
    groups: [(group_name, group_desc, [(port_name, direction, width, desc, sw_ov, hw_ov, init_ov), ...]), ...]
    """
    with open(filepath, 'r') as f:
        text = f.read()

    module_name = None
    module_desc = ''
    groups = []
    current_group = None
    current_group_desc = ''
    current_ports = []

    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue

        # module declaration: module <name> ["description"]
        m = re.match(r'module\s+(\w+)(?:\s*"([^"]*)")?', line, re.IGNORECASE)
        if m:
            module_name = m.group(1)
            module_desc = m.group(2) or ''
            continue

        # group header: //group_name "description"  (行首注释)
        m = re.match(r'//(\w+)(?:\s*"([^"]*)")?', line)
        if m:
            if current_group is not None:
                groups.append((current_group, current_group_desc, current_ports))
            current_group = m.group(1)
            current_group_desc = m.group(2) or ''
            current_ports = []
            continue

        # port connection: .port_name [( signal )] , // direction[, width=N] [sw=X] [hw=Y] ["desc"]
        # 小括号内信号名和尾部逗号均可省略
        # sw=/hw= 可手动覆盖 access 类型（默认由 direction 决定）
        m = re.match(
            r'\.(\w+)(?:\s*\([^)]*\))?\s*,?\s*//\s*(\w+)'
            r'(?:[,\s]+width\s*[=:]\s*(\d+))?'
            r'(?:\s*\[(\d+):(\d+)\])?'
            r'(?:[,\s]+sw\s*[=:]\s*(\w+))?'
            r'(?:[,\s]+hw\s*[=:]\s*(\w+))?'
            r'(?:[,\s]*"([^"]*)")?',
            line, re.IGNORECASE
        )
        if m:
            port_name = m.group(1)
            direction = m.group(2).lower()
            # 优先级: [MSB:LSB] > width=N > 默认1
            if m.group(4) is not None:
                msb, lsb = int(m.group(4)), int(m.group(5))
                width = msb - lsb + 1
            elif m.group(3) is not None:
                width = int(m.group(3))
            else:
                width = 1
            sw_override = m.group(6) or ''
            hw_override = m.group(7) or ''
            description = m.group(8) or ''
            # init= 位置无关，单独提取
            init_m = re.search(r'init\s*[=:]\s*([^,\s"]+)', line)
            init_override = init_m.group(1) if init_m else ''
            current_ports.append((port_name, direction, width, description, sw_override, hw_override, init_override))
            continue

    # 收尾最后一个 group
    if current_group is not None:
        groups.append((current_group, current_group_desc, current_ports))

    return module_name, module_desc, groups


def make_init_value(width: int) -> str:
    """根据位宽生成 init_value，如 width=11 -> 0b00000000000"""
    return '0b' + '0' * width


def direction_to_access(direction: str, sw_override='', hw_override=''):
    """
    由 direction 决定默认值，sw=/hw= 手动覆盖。
    input  -> sw=ReadWrite, hw=ReadOnly
    output -> sw=ReadOnly,  hw=ReadWrite
    """
    if direction == 'input':
        sw, hw = 'ReadWrite', 'ReadOnly'
    else:
        sw, hw = 'ReadOnly', 'ReadWrite'
    if sw_override:
        sw = sw_override
    if hw_override:
        hw = hw_override
    return sw, hw


REG_BITS = 32  # 每个寄存器的位宽


def split_ports(ports: list) -> list:
    """
    将一组 ports 按 REG_BITS 分割成多个块。
    返回 [[(name, direction, width, desc, sw_ov, hw_ov, init_val), ...], ...]
    """
    chunks = []
    current_chunk = []
    current_bits = 0

    for name, direction, width, desc, sw_ov, hw_ov, init_val in ports:
        if width > REG_BITS:
            if current_chunk:
                chunks.append(current_chunk)
                current_chunk = []
                current_bits = 0
            chunks.append([(name, direction, width, desc, sw_ov, hw_ov, init_val)])
        elif current_bits + width > REG_BITS:
            chunks.append(current_chunk)
            current_chunk = [(name, direction, width, desc, sw_ov, hw_ov, init_val)]
            current_bits = width
        else:
            current_chunk.append((name, direction, width, desc, sw_ov, hw_ov, init_val))
            current_bits += width

    if current_chunk:
        chunks.append(current_chunk)

    return chunks


def generate_code(module_name: str, module_desc: str, groups: list) -> str:
    """生成 Python 寄存器代码"""
    lines = []
    lines.append('import sys')
    lines.append("sys.path.append('.')")
    lines.append('from address_planner import *')
    lines.append('')

    regspace_name = module_name
    lines.append(
        f"regBank = RegSpace("
        f"name='{regspace_name}',size=16*KB,"
        f'description="{module_desc}",bus_width=16,software_interface=\'apb\')'
    )
    lines.append('')

    offset = 0
    reg_idx = 0

    for group_name, group_desc, ports in groups:
        # 对组内重名 port 去重
        seen = {}
        clean_ports = []
        for name, direction, width, desc, sw_ov, hw_ov, init_val in ports:
            if name in seen:
                seen[name] += 1
                clean_ports.append((f"{name}_{seen[name]}", direction, width, desc, sw_ov, hw_ov, init_val))
            else:
                seen[name] = 0
                clean_ports.append((name, direction, width, desc, sw_ov, hw_ov, init_val))

        # 按 32bit 分割
        chunks = split_ports(clean_ports)

        # 分隔注释（只针对第一个 chunk 输出组名）
        side = '#' * 5
        lines.append(f"{side} {group_name} {side}")

        for ci, chunk in enumerate(chunks):
            # 寄存器名：多块时第一块不加后缀，溢出块加 _ex0, _ex1...
            if len(chunks) > 1:
                reg_name = group_name if ci == 0 else f"{group_name}_ex{ci - 1}"
            else:
                reg_name = group_name

            reg_var = f"reg_{reg_idx}"
            lines.append(
                f"{reg_var} = Register("
                f"name='{reg_name}',bit={REG_BITS},"
                f'description="{group_desc}",'
                f"reg_type=Normal, parity=True)"
            )

            field_offset = 0
            for port_name, direction, width, desc, sw_ov, hw_ov, init_val in chunk:
                sw_acc, hw_acc = direction_to_access(direction, sw_ov, hw_ov)
                if init_val:
                    init_value_str = init_val
                else:
                    init_value_str = make_init_value(width)
                lines.append(
                    f"{reg_var}.add(Field("
                    f"name='{port_name}',bit={width},"
                    f"sw_access={sw_acc},hw_access={hw_acc},"
                    f"init_value={init_value_str},description='{desc}'),offset = {field_offset})"
                )
                field_offset += width

            offset_str = f"0x{offset:02X}"
            lines.append(f"regBank.add({reg_var}, offset={offset_str})")
            lines.append('')

            offset += 4
            reg_idx += 1

    # main guard
    lines.append('if __name__ == "__main__":')
    lines.append("    regBank.generate('build')")

    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(
        description='SV to Python Register Generator',
        epilog=(
            '输入格式: module <name> ["desc"]\n'
            '         //<group_name> ["desc"]\n'
            '         .<port> [ (sig) ] [,] // <direction> [<width>] [sw=X] [hw=Y] [init=X] ["desc"]\n'
            '         (信号名和逗号均可省略)\n'
            '位宽: [MSB:LSB] 或 width=N，默认 1bit\n'
            '方向: input->RW/RO, output->RO/RW, 可用 sw=/hw= 手动覆盖\n'
            'init: 手动指定 init_value（默认按位宽填 0）\n'
            '描述: ""内文字填入 description 字段\n'
            '默认输出: <module>_reg_rf_gen.py'
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument('input', help='输入的 SV 文件路径')
    parser.add_argument(
        '-o', '--output',
        help='输出的 Python 文件路径（默认 <module>_reg_rf_gen.py）'
    )
    parser.add_argument(
        '-r', '--run',
        action='store_true',
        help='生成后自动执行输出的 Python 文件'
    )
    args = parser.parse_args()

    # 解析
    module_name, module_desc, groups = parse_sv(args.input)
    if not module_name:
        print('错误: 未找到 module 声明', file=sys.stderr)
        sys.exit(1)

    # 生成
    code = generate_code(module_name, module_desc, groups)

    # 输出
    out_path = args.output or f"{module_name}_reg_rf_gen.py"
    with open(out_path, 'w') as f:
        f.write(code)
    print(f"✓ 已生成: {out_path}")

    # 自动执行
    if args.run:
        print(f"▶ 执行: {out_path}")
        import subprocess
        ret = subprocess.run(['python3', out_path])
        if ret.returncode != 0:
            sys.exit(ret.returncode)


if __name__ == '__main__':
    main()
