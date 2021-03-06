#!/usr/bin/python

import curses
import traceback
import string
import os
import time
import json
import sys
sys.path.append('./src/')

import cpu
import flag
import flag_functions
import functions
import instruction
import register
import memory
import label


def create_subwindow(x, y, w, h, border_list, header):
    res = stdscr.subwin(12, 14, 0, 0)
    res = stdscr.subwin(h, w, y, x)
    b1, b2, b3, b4, b5, b6, b7, b8 = border_list
    res.border(b1, b2, b3, b4, b5, b6, b7, b8)
    #inbox_w = w - 2
    res.addstr(1, 1, header)
    res.hline(2, 1, chr(45), w - 2)
    return res


def create_suface():
    reg_window = create_subwindow(
        0, 0, 18, 12,
        [0, 0, 0, 0,
         0, curses.ACS_TTEE, curses.ACS_PLUS, curses.ACS_PLUS],
        'REGISTERS')
    flags_window = create_subwindow(
        0, 11, 18, 12,
        [0, 0, 0, 0,
         curses.ACS_PLUS, curses.ACS_PLUS, 0, curses.ACS_BTEE],
        'FLAGS'
    )
    sig_window = create_subwindow(
        17, 0, 20, 12,
        [0, 0, 0, 0,
         curses.ACS_TTEE, curses.ACS_TTEE, curses.ACS_PLUS, curses.ACS_RTEE],
        'SIGNATURES'
    )
    asm_window = create_subwindow(
        17, 11, 20, 12,
        [0, 0, 0, 0,
         curses.ACS_PLUS, curses.ACS_RTEE, curses.ACS_BTEE, curses.ACS_BTEE],
        'ASSEMBLER'
    )
    memo_window = create_subwindow(
        36, 0, 43, 23,
        [0, 0, 0, 0,
         curses.ACS_TTEE, 0, curses.ACS_BTEE, 0],
        'MEMO DUMP'
    )
    return (reg_window, flags_window, sig_window, asm_window, memo_window)


def update_registers(reg_window, registers):
    i = 3
    for reg in registers:
        reg_window.addstr(i, 1, reg + ' ' + str(registers[reg]))
        i += 1


def update_flags(flags_window, flags):
    i = 3
    for flag in flags:
        flags_window.addstr(i, 1, str(flags[flag]))
        i += 1


def update_memory(memo_window, memory):
    i = 3
    for line in memory.list():
        memo_window.addstr(i, 1, line)
        i += 1
        if i == 22:
            break


def update_signatures(sig_window, signatures, memory):
    total = 0
    i = 3
    for sig, threat in signatures:
        if sig in str(memory):
            sig_window.addstr(i, 1, 'V ' + sig)
            i += 1
            total += threat
        else:
            sig_window.addstr(i, 1, 'X ' + sig)
            i += 1
    sig_window.addstr(10, 1, 'TOTAL: ' + str(total) + '%')


def update_demo_program(asm_window):
    program = [
        'MOV EBX, 1792',
        'LABEL:',
        'MOV EAX, [EDX]',
        'MOV ECX, 74',
        'XOR EAX, ECX',
        'ADD EAX, EBX',
        'MOV EAX, [EAX]',
        'MOV ECX, 115',
        'XOR EAX, ECX',
        'MOV [EDX], AL',
        'INC EDX',
        'CMP EDX, EBX',
        'JNE LABEL',
        'RET',
    ]
    i = 3
    for line in program:
        asm_window.addstr(i, 1, line)
        i += 1
        if i == 11:
            break


def refresh_cpu_screen(cpu, screen, **kwargs):
    update_registers(kwargs['reg_window'], cpu.registers)
    update_flags(kwargs['flags_window'], cpu.flags)
    update_memory(kwargs['memo_window'], cpu.memory)
    update_demo_program(kwargs['asm_window'])
    update_signatures(kwargs['sig_window'], kwargs['signatures'], cpu.memory)
    screen.refresh()


if __name__ == '__main__':
    try:
        stdscr = curses.initscr()
        curses.noecho()
        curses.cbreak()
        screen = stdscr.subwin(23, 79, 0, 0)
        screen.box()
        screen.refresh()
        stdscr.keypad(1)

        (reg_window,
         flags_window,
         sig_window,
         asm_window,
         memo_window) = create_suface()

        cpu_registers = register.load_from_file(
            './examples/x86/registers.json'
        )
        cpu_instructions = instruction.load_from_file(
            './examples/x86/instructions.json'
        )
        cpu_flags = flag.load_from_file('./examples/x86/flags.json')
        cpu_memory = memory.MemoryPage(2048)
        loaded_memory = eval(open('./examples/memory.txt').read())
        cpu_memory.write_ord(0, loaded_memory)

        cpu = cpu.CPU(
            name='x86',
            instructions=cpu_instructions,
            flags=cpu_flags,
            registers=cpu_registers,
            ip_register='EIP',
            memory=cpu_memory
        )

        demo_signatures = [
            ('/tmp', 1),
            ('chmod', 3),
            ('sed', 5)
        ]

        # 1246382666 - 74, 74, 74, 74
        # 1936946035 - 115, 115, 115, 115
        program = [
            "cpu.registers['EBX'].set_int_value(1792)",
            """cpu.execute(
                'MOVR',
                cpu.registers['EAX'],
                cpu.memory.get_bin(cpu.registers['EDX'].get_int_value(), 1)
            )""",
            "cpu.registers['ECX'].set_int_value(74)",
            "cpu.execute('XOR', cpu.registers['EAX'], cpu.registers['ECX'])",
            "cpu.execute('ADD', cpu.registers['EAX'], cpu.registers['EBX'])",
            """cpu.execute(
                'MOVR',
                cpu.registers['EAX'],
                cpu.memory.get_bin(cpu.registers['EAX'].get_int_value(), 1)
            )""",
            "cpu.registers['ECX'].set_int_value(115)",
            "cpu.execute('XOR', cpu.registers['EAX'], cpu.registers['ECX'])",
            #"cpu.execute('SUB', cpu.registers['EDX'], cpu.registers['EBX'])",
            """cpu.execute(
                'MOVM',
                cpu.memory,
                cpu.registers['EDX'].get_int_value(),
                cpu.registers['EAX'].get_byte_list_value()[:1]
            )""",
            "cpu.execute('ADD', cpu.registers['EDX'], 1)",
            "cpu.execute('JMP', cpu.registers['EIP'], label.Label('', 0))",
        ]

        for i in range(100):
            for instruction in program:
                eval(instruction)
                refresh_cpu_screen(
                    cpu,
                    screen,
                    reg_window=reg_window,
                    flags_window=flags_window,
                    memo_window=memo_window,
                    asm_window=asm_window,
                    sig_window=sig_window,
                    signatures=demo_signatures
                )
                c = screen.getch()

        c = screen.getch()

        stdscr.keypad(0)
        curses.echo()
        curses.nocbreak()
        curses.endwin()
    except:
        stdscr.keypad(0)
        curses.echo()
        curses.nocbreak()
        curses.endwin()
        traceback.print_exc()
