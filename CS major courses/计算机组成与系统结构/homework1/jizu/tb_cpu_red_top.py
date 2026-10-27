import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer
import random

def ori(rt, rs, imm):  return (0b001101<<26) | (rs<<21) | (rt<<16) | (imm & 0xFFFF)
def addu(rd, rs, rt): return (0<<26) | (rs<<21) | (rt<<16) | (rd<<11) | 0x21
def bne(rs, rt, off): return (0b000101<<26) | (rs<<21) | (rt<<16) | (off & 0xFFFF)
def lw(rt, base, off): return (0b100011<<26) | (base<<21) | (rt<<16) | (off & 0xFFFF)
def sw(rt, base, off): return (0b101011<<26) | (base<<21) | (rt<<16) | (off & 0xFFFF)

@cocotb.test()
async def final_high_coverage_v2(dut):

    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())

    # Reset
    dut.rst_n.value = 0
    await Timer(20, units="ns")
    await RisingEdge(dut.clk)
    dut.rst_n.value = 1

    program = {}
    pc = 0x80000000

    def emit(inst):
        nonlocal pc
        program[pc] = inst
        pc += 4

    # ========= 1. 寄存器边界 =========
    emit(ori(1, 0, 0x0000))
    emit(ori(2, 0, 0xFFFF))
    emit(ori(31, 0, 0x7FFF))
    emit(ori(30, 0, 0x8000))

    # 写 $0
    emit(ori(0, 1, 1234))
    emit(addu(0, 1, 2))

    # ========= 2. 数据相关 =========
    emit(ori(3, 0, 5))
    emit(addu(4, 3, 3))
    emit(addu(5, 4, 3))

    # ========= 3. BNE 全覆盖 =========
    emit(ori(6, 0, 10))
    emit(ori(7, 0, 10))

    # 不跳
    emit(bne(6, 7, 1))
    emit(ori(8, 0, 111))

    # 正跳
    emit(bne(6, 0, 2))
    emit(ori(8, 0, 222))
    emit(ori(8, 0, 333))

    # 负跳（关键！）
    emit(ori(9, 0, 1))
    emit(ori(10, 0, 2))
    emit(bne(9, 10, -2))  # 回跳

    # ========= 4. 内存覆盖 =========
    for i in range(5):
        emit(ori(11, 0, i))
        emit(sw(11, 0, i * 4))
        emit(lw(12, 0, i * 4))

    # 读未写地址
    emit(lw(13, 0, 0x100))

    # 写 $0
    emit(lw(0, 0, 0))

    # ========= 5. 非法指令 =========
    emit(0xFFFFFFFF)
    emit(0xFC000000)
    emit(0x0000003F)

    # ========= 6. 半随机指令 =========
    for _ in range(200):
        r = random.randint(0, 4)
        if r == 0:
            emit(ori(random.randint(0,31), random.randint(0,31), random.randint(0,0xFFFF)))
        elif r == 1:
            emit(addu(random.randint(0,31), random.randint(0,31), random.randint(0,31)))
        elif r == 2:
            emit(lw(random.randint(0,31), 0, random.randint(0,64)))
        elif r == 3:
            emit(sw(random.randint(0,31), 0, random.randint(0,64)))
        else:
            emit(bne(random.randint(0,31), random.randint(0,31), random.randint(-4,4)))

    # ========= 仿真 =========
    mem = {}

    for _ in range(2000):
        addr = int(dut.instr_addr.value)
        instr = program.get(addr, random.getrandbits(32))
        dut.instr.value = instr

        if dut.dmem_we.value:
            mem[int(dut.dmem_addr.value)] = int(dut.dmem_wdata.value)

        if dut.dmem_re.value:
            dut.dmem_rdata.value = mem.get(int(dut.dmem_addr.value), 0)

        await RisingEdge(dut.clk)

    dut._log.info("HIGH COVERAGE DONE")