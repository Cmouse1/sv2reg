#!/usr/bin/env python3
"""
sv2reg_align.py — Auto-align sv2reg-format SV port declarations

Aligns:
  - .port_name    left-aligned to uniform width
  - ( signal )    left-paren aligned
  - ,             comma aligned
  - // comment    comment aligned

Usage:
  python3 sv2reg_align.py demo.sv           # print to stdout
  python3 sv2reg_align.py demo.sv --inplace # modify in-place
"""
import argparse
import re
import sys


def align_lines(lines: list[str]) -> list[str]:
    """Take list of lines, return aligned list."""

    # ---- Pass 1: parse port lines, compute column widths ----
    entries = []       # [(line_idx, port_name, signal_block, comma, comment), ...]
    max_name = 0
    max_signal = 0

    for i, line in enumerate(lines):
        if not re.match(r'^\s*\.\w', line):
            continue

        line = line.rstrip('\n')
        trimmed = line.lstrip()

        # Split at //
        c_idx = trimmed.find('//')
        if c_idx >= 0:
            port_part = trimmed[:c_idx]
            comment = trimmed[c_idx:]
        else:
            port_part = trimmed
            comment = ''

        port_part = port_part.rstrip()

        # Extract .port_name
        pm = re.match(r'(\.\w+)', port_part)
        if not pm:
            continue
        port_name = pm.group(1)

        # Tail after port_name
        tail = port_part[len(port_name):].lstrip()

        # Extract (signal_block)
        signal_block = ''
        if tail and tail[0] == '(':
            close_idx = tail.find(')')
            if close_idx >= 0:
                signal_block = tail[:close_idx + 1]
                tail = tail[close_idx + 1:].lstrip()

        # Extract comma
        comma = ',' if tail and tail[0] == ',' else ''

        nlen = len(port_name)
        slen = len(signal_block)
        if nlen > max_name:
            max_name = nlen
        if slen > max_signal:
            max_signal = slen

        entries.append((i, port_name, signal_block, comma, comment))

    if not entries:
        return lines  # nothing to align

    # ---- Pass 2: rebuild aligned lines ----
    for ln, port_name, signal_block, comma, comment in entries:
        # Column layout: <space><port_name><pad>  <signal_or_pad>  <comma>  // <comment>

        # Col 1: port_name
        new = ' ' + port_name
        name_pad = max_name - len(port_name)
        if name_pad > 0:
            new += ' ' * name_pad

        # Gap 2 spaces
        new += '  '

        # Col 2: signal_block or blank padding
        if signal_block:
            new += signal_block
            sig_pad = max_signal - len(signal_block)
            if sig_pad > 0:
                new += ' ' * sig_pad
        elif max_signal > 0:
            new += ' ' * max_signal

        # Gap + comma
        new += '  '
        if comma:
            new += comma
        else:
            new += ' '

        # Gap + comment
        if comment:
            new += '  ' + comment

        lines[ln] = new + '\n'

    return lines


def main():
    parser = argparse.ArgumentParser(description='Align sv2reg-format SV port declarations')
    parser.add_argument('file', help='SV file to align')
    parser.add_argument('--inplace', '-i', action='store_true',
                        help='Modify file in-place (default: print to stdout)')
    args = parser.parse_args()

    with open(args.file) as f:
        lines = f.readlines()

    aligned = align_lines(lines)

    if args.inplace:
        with open(args.file, 'w') as f:
            f.writelines(aligned)
        print(f'Aligned {args.file}')
    else:
        sys.stdout.writelines(aligned)


if __name__ == '__main__':
    main()
