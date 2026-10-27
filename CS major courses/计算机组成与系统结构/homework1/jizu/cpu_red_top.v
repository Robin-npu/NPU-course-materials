--- /mnt/data/9efcdcc3-d080-4121-be48-7bf4b8870ab8.py	2026-03-21 09:57:26.460064939 +0000
+++ /mnt/data/tb_cpu_red_top.py	2026-03-21 10:00:19.911670363 +0000
@@ -1,111 +1,174 @@
-import cocotb
-from cocotb.clock import Clock
-from cocotb.triggers import RisingEdge, Timer
-import random
-
-def ori(rt, rs, imm):  return (0b001101<<26) | (rs<<21) | (rt<<16) | (imm & 0xFFFF)
-def addu(rd, rs, rt): return (0<<26) | (rs<<21) | (rt<<16) | (rd<<11) | 0x21
-def bne(rs, rt, off): return (0b000101<<26) | (rs<<21) | (rt<<16) | (off & 0xFFFF)
-def lw(rt, base, off): return (0b100011<<26) | (base<<21) | (rt<<16) | (off & 0xFFFF)
-def sw(rt, base, off): return (0b101011<<26) | (base<<21) | (rt<<16) | (off & 0xFFFF)
-
-@cocotb.test()
-async def final_high_coverage_v2(dut):
-
-    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
-
-    # Reset
-    dut.rst_n.value = 0
-    await Timer(20, units="ns")
-    await RisingEdge(dut.clk)
-    dut.rst_n.value = 1
-
-    program = {}
-    pc = 0x80000000
-
-    def emit(inst):
-        nonlocal pc
-        program[pc] = inst
-        pc += 4
-
-    # ========= 1. 寄存器边界 =========
-    emit(ori(1, 0, 0x0000))
-    emit(ori(2, 0, 0xFFFF))
-    emit(ori(31, 0, 0x7FFF))
-    emit(ori(30, 0, 0x8000))
-
-    # 写 $0
-    emit(ori(0, 1, 1234))
-    emit(addu(0, 1, 2))
-
-    # ========= 2. 数据相关 =========
-    emit(ori(3, 0, 5))
-    emit(addu(4, 3, 3))
-    emit(addu(5, 4, 3))
-
-    # ========= 3. BNE 全覆盖 =========
-    emit(ori(6, 0, 10))
-    emit(ori(7, 0, 10))
-
-    # 不跳
-    emit(bne(6, 7, 1))
-    emit(ori(8, 0, 111))
-
-    # 正跳
-    emit(bne(6, 0, 2))
-    emit(ori(8, 0, 222))
-    emit(ori(8, 0, 333))
-
-    # 负跳（关键！）
-    emit(ori(9, 0, 1))
-    emit(ori(10, 0, 2))
-    emit(bne(9, 10, -2))  # 回跳
-
-    # ========= 4. 内存覆盖 =========
-    for i in range(5):
-        emit(ori(11, 0, i))
-        emit(sw(11, 0, i * 4))
-        emit(lw(12, 0, i * 4))
-
-    # 读未写地址
-    emit(lw(13, 0, 0x100))
-
-    # 写 $0
-    emit(lw(0, 0, 0))
-
-    # ========= 5. 非法指令 =========
-    emit(0xFFFFFFFF)
-    emit(0xFC000000)
-    emit(0x0000003F)
-
-    # ========= 6. 半随机指令 =========
-    for _ in range(200):
-        r = random.randint(0, 4)
-        if r == 0:
-            emit(ori(random.randint(0,31), random.randint(0,31), random.randint(0,0xFFFF)))
-        elif r == 1:
-            emit(addu(random.randint(0,31), random.randint(0,31), random.randint(0,31)))
-        elif r == 2:
-            emit(lw(random.randint(0,31), 0, random.randint(0,64)))
-        elif r == 3:
-            emit(sw(random.randint(0,31), 0, random.randint(0,64)))
-        else:
-            emit(bne(random.randint(0,31), random.randint(0,31), random.randint(-4,4)))
-
-    # ========= 仿真 =========
-    mem = {}
-
-    for _ in range(2000):
-        addr = int(dut.instr_addr.value)
-        instr = program.get(addr, random.getrandbits(32))
-        dut.instr.value = instr
-
-        if dut.dmem_we.value:
-            mem[int(dut.dmem_addr.value)] = int(dut.dmem_wdata.value)
-
-        if dut.dmem_re.value:
-            dut.dmem_rdata.value = mem.get(int(dut.dmem_addr.value), 0)
-
-        await RisingEdge(dut.clk)
-
-    dut._log.info("HIGH COVERAGE DONE")
\ No newline at end of file
+import cocotb
+from cocotb.clock import Clock
+from cocotb.triggers import RisingEdge, Timer
+
+
+def ori(rt, rs, imm):
+    return (0b001101 << 26) | (rs << 21) | (rt << 16) | (imm & 0xFFFF)
+
+
+def addu(rd, rs, rt):
+    return (0 << 26) | (rs << 21) | (rt << 16) | (rd << 11) | 0x21
+
+
+def bne(rs, rt, off):
+    return (0b000101 << 26) | (rs << 21) | (rt << 16) | (off & 0xFFFF)
+
+
+def lw(rt, base, off):
+    return (0b100011 << 26) | (base << 21) | (rt << 16) | (off & 0xFFFF)
+
+
+def sw(rt, base, off):
+    return (0b101011 << 26) | (base << 21) | (rt << 16) | (off & 0xFFFF)
+
+
+def rtype_raw(rs, rt, rd, shamt, funct):
+    return (0 << 26) | (rs << 21) | (rt << 16) | (rd << 11) | (shamt << 6) | (funct & 0x3F)
+
+
+@cocotb.test()
+async def final_high_coverage_v3(dut):
+    """
+    目标：把 RTL 里的关键分支全部定点踩到，而不是靠随机撞运气。
+    重点覆盖：
+    1) reset 分支
+    2) valid / invalid opcode
+    3) R-type 有效 funct / 默认 funct
+    4) BNE: 非 branch、branch 不跳、正向跳、负向回跳
+    5) ORI / ADDU / LW 写回的 true/false 分支（写 $0）
+    6) SW / LW / 未写地址 / 负偏移地址
+    """
+
+    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
+
+    # ---------- reset ----------
+    dut.instr.value = 0
+    dut.dmem_rdata.value = 0
+    dut.rst_n.value = 0
+    await Timer(20, units="ns")
+    await RisingEdge(dut.clk)
+    dut.rst_n.value = 1
+
+    # ---------- build deterministic program ----------
+    program = {}
+    pc = 0x80000000
+
+    def emit(inst):
+        nonlocal pc
+        program[pc] = inst
+        pc += 4
+
+    # 1) ORI / register boundaries / write $0 false branch
+    emit(ori(1, 0, 0x0000))   # r1  = 0x0000
+    emit(ori(2, 0, 0xFFFF))   # r2  = 0xFFFF
+    emit(ori(3, 0, 0x5555))   # r3  = 0x5555
+    emit(ori(4, 0, 0xAAAA))   # r4  = 0xAAAA
+    emit(ori(31, 0, 0x7FFF))  # high reg index
+    emit(ori(30, 0, 0x8000))  # sign boundary bit
+    emit(ori(5, 2, 0x00F0))   # nonzero rs, OR path
+    emit(ori(0, 1, 0x1234))   # write $0, should be ignored
+
+    # 2) ADDU valid / rd==0 false branch / data dependency
+    emit(addu(6, 3, 4))       # valid addu
+    emit(addu(7, 6, 3))       # use result immediately
+    emit(addu(0, 3, 4))       # rd==0, false branch
+
+    # 3) R-type invalid funct -> hit alu_out default in R-type
+    emit(rtype_raw(3, 4, 8, 0, 0x20))
+    emit(rtype_raw(0, 0, 9, 0, 0x00))
+
+    # 4) BNE not taken
+    emit(ori(10, 0, 10))
+    emit(ori(11, 0, 10))
+    emit(bne(10, 11, 1))      # not taken
+    emit(ori(12, 0, 0x0111))
+
+    # 5) BNE taken forward
+    emit(bne(10, 0, 2))       # taken, skip next 2 instructions
+    emit(ori(12, 0, 0x0222))
+    emit(ori(12, 0, 0x0333))
+    emit(ori(12, 0, 0x0444))  # lands here
+
+    # 6) BNE taken backward, but finite loop (避免之前那个死循环坑)
+    emit(ori(13, 0, 1))       # increment = 1
+    emit(ori(14, 0, 3))       # target = 3
+    emit(ori(15, 0, 0))       # counter = 0
+    emit(addu(15, 15, 13))    # counter += 1
+    emit(bne(15, 14, -2))     # back to addu until counter == 3
+    emit(ori(16, 0, 0x1234))  # proves loop exited
+
+    # 7) Memory coverage: base + positive offset + negative offset + unread address
+    emit(ori(17, 0, 0x0020))  # base address = 0x20
+    emit(ori(18, 0, 0xABCD))
+    emit(ori(19, 0, 0x1357))
+
+    emit(sw(18, 17, 0))       # mem[0x20] = 0xABCD
+    emit(lw(20, 17, 0))       # load written addr
+
+    emit(sw(19, 17, 4))       # mem[0x24] = 0x1357
+    emit(lw(21, 17, 4))
+
+    emit(sw(4, 17, -4))       # mem[0x1C] = r4, negative offset
+    emit(lw(22, 17, -4))
+
+    emit(lw(23, 17, 0x10))    # unread addr -> should get 0
+    emit(lw(0, 17, 0))        # write $0 false branch for LW
+
+    # 8) Invalid opcode path
+    emit(0xFFFFFFFF)
+    emit(0xFC000000)
+    emit(0xA0000000)          # opcode = 0b101000, invalid
+
+    # 9) More toggles / different registers, but no risky random backward branches
+    for r in range(24, 32):
+        emit(ori(r, 0, 1 << (r - 24)))
+
+    emit(addu(24, 24, 25))
+    emit(addu(26, 26, 27))
+    emit(addu(28, 28, 29))
+    emit(addu(30, 30, 31))
+    emit(sw(24, 17, 8))
+    emit(lw(25, 17, 8))
+    emit(bne(24, 25, 1))      # should be not taken after load
+    emit(bne(24, 0, 1))       # taken forward by 1
+    emit(ori(26, 0, 0xDEAD))  # skipped
+    emit(ori(27, 0, 0xBEEF))
+
+    # ---------- memory model ----------
+    mem = {}
+
+    def fetch_fallback(addr: int) -> int:
+        # 程序跑完以后不要喂随机指令。
+        # 随机看着热闹，coverage 工具不一定买账，还容易把 PC 带沟里。
+        # 这里交替喂两种“安全垃圾”：
+        # - 0x00000000: valid R-type + invalid funct
+        # - 0xFFFFFFFF: invalid opcode
+        return 0x00000000 if ((addr >> 2) & 1) == 0 else 0xFFFFFFFF
+
+    total_cycles = len(program) + 80
+
+    # ---------- simulation ----------
+    for _ in range(total_cycles):
+        addr = int(dut.instr_addr.value)
+        dut.instr.value = program.get(addr, fetch_fallback(addr))
+        await Timer(1, units="ps")  # 让组合逻辑先稳定一下
+
+        if int(dut.dmem_we.value):
+            mem[int(dut.dmem_addr.value) & 0xFFFFFFFF] = int(dut.dmem_wdata.value) & 0xFFFFFFFF
+
+        if int(dut.dmem_re.value):
+            dut.dmem_rdata.value = mem.get(int(dut.dmem_addr.value) & 0xFFFFFFFF, 0)
+        else:
+            dut.dmem_rdata.value = 0
+
+        await RisingEdge(dut.clk)
+
+    # ---------- a few lightweight sanity checks ----------
+    # 这些断言不影响 coverage，但能防止“覆盖率上去了，电路其实跑飞了”这种离谱情况。
+    assert mem.get(0x20, None) == 0xABCD, f"mem[0x20] mismatch: {mem.get(0x20)}"
+    assert mem.get(0x24, None) == 0x1357, f"mem[0x24] mismatch: {mem.get(0x24)}"
+    assert mem.get(0x1C, None) == 0xAAAA, f"mem[0x1C] mismatch: {mem.get(0x1C)}"
+
+    dut._log.info(f"Program length = {len(program)} instructions")
+    dut._log.info("HIGH COVERAGE V3 DONE")
