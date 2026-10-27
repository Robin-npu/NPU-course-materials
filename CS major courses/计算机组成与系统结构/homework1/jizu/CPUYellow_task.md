<!--
    CPU_YELLOW 五级流水线 MIPS 处理器设计
    **课程名称：** 计算机组成与系统结
    **课程编号：** U10M11007.02
    **计算机学院**
    **西北工业大学**
-->

# Step 1 实验任务目标确认
完成兼容```doc/A03_“系统能力培养大赛”MIPS指令系统规范_v1.01.pdf```所规定的MIPS指令系统的处理器设计。该处理器具有典型的5级流水线结构，即应该具取指(IF)、译码(ID)、执行(EXE)、访存(MEM)、写回(WB)五个流水级。
# Step 2 自然语言描述 -> 设计Spec文件，人工检查确认
生成一份 Spec 文档，保存到doc/CPUYellow_spec.md，交给人工审阅。顶层模块使用模块名cpu_yellow_top，顶层文件保存在src/rtl/cpu_yellow_top.v。
| 端口名 | 方向 | 位宽 | 描述 |
| --- | --- | --- | --- |
| clk | input |	1 | 全局时钟，所有时序逻辑在上升沿更新。 |
|rst_n | input | 1 | 异步复位，低电平有效。复位时 PC 清零，所有控制信号置为无效。 |
| instr	| input	| 32 | 指令输入，来自外部指令存储器。 |
| instr_addr | output | 32 | 下一条指令的地址——当前指PC程序计数器，送指令存储器地址端口。 |
| dmem_addr	| output | 32 | 数据存储器地址，用于访存指令。 |
| dmem_wdata | output | 32 | 数据存储器写数据。 |
| dmem_rdata | input	| 32 | 数据存储器读数据。 |
| dmem_we | output | 1 | 数据存储器写使能，高有效。 |
| dmem_re | output | 1 | 数据存储器读使能，高有效。 |
以下是对Spec的基本要求，同时结合```doc/A03_“系统能力培养大赛”MIPS指令系统规范_v1.01.pdf```补全Spec文件。

## 时序要求

充分考虑五级流水线处理器的时序要求，每一条指令从指令取指开始到寄存器写回每个步骤在一个周期内完成。
```取指-->译码-->执行-->存储访问-->寄存器写回```需要在五个周期中分别完成，即每部操作一个周期。

- 指令存储器（IM）时序要求：
为了兼容FPGA Block RAM的时序特征，即地址 instr_addr 稳定后，存储器在下一时钟周期可以稳定输出数据，即instr需要在下一时钟周期内采样输出，instr_addr 与 instr 之间存在一个时钟周期的延迟。

- 数据存储器（DM）时序要求：
时序特征假设与指令存储其一致。
    读：组合逻辑，读使能 dmem_re 有效时，地址 dmem_addr 对应的数据一拍之后采样输出到 dmem_rdata。
    写：在时钟采样上升沿，若 dmem_we 有效，则将 dmem_wdata 写入地址 dmem_addr 对应的存储单元。

- 寄存器堆：写操作在时钟采样上升沿写入寄存器堆。
- PC 在时钟上升沿更新。

## 编程模型

### 数据格式

处理器可处理的数据格式定义如下：
- 比特（bit,b）
- 字节（Byte,8bits,B）
- 半字（Halfword,16bits, H）
- 字（Word,32bits,W）
### 寄存器
处理器包含的软件可见的寄存器种类如下：
- 32个32位通用寄存器，r0~r31。其中有两个被赋予了特殊含义：r0，0号通用寄存器，值永远为0；r31，31号通用寄存器，被JAL指令隐式的用作目标寄存器，存放返回地址。
- 程序计数器（PC）。这个寄存器软件无法直接访问。
### 大小尾端
处理器中的字节顺序和比特顺序均采用小尾端模式，即第0字节永远是最低有效字节，第0比特永远是最低有效比特。
### 存储访问类型
处理器至少支持不可缓存（uncached）这种存储访问类型。属于此类型的访问将直接读、写物理内存（或物理内存地址映射的寄存器），但不会访问或修改各级缓存中的内容。

## 操作模式

处理器永远处于核心态模式（KernelMode）。该操作模式下处理器可以执行所有指令，访问32位全地址空间。

## 指令定义

本系统包含 57 条指令，分为以下类别：

- **算术运算指令** (14条)
- **逻辑运算指令** (8条)
- **移位指令** (6条)
- **分支跳转指令** (12条)
- **数据移动指令** (4条)
- **自陷指令** (2条)
- **访存指令** (8条)
- **特权指令** (3条)

所有指令长度均为 32 比特，格式分为 I-Type, J-Type, R-Type。详细内容参考```doc/A03_“系统能力培养大赛”MIPS指令系统规范_v1.01.pdf```要求。

### 算术运算指令

| 指令 | 位段表示 (31..0) | 汇编格式 | 功能描述 | 操作定义 (伪代码) | 例外说明 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **ADD** | `000000 rs rt rd 00000 100000` | `ADD rd, rs, rt` | 有符号加法，溢出触发例外 | `tmp ← (GPR[rs]₃₁∥GPR[rs]) + (GPR[rt]₃₁∥GPR[rt])`<br>`if tmp₃₂ ≠ tmp₃₁ then SignalException(IntegerOverflow)`<br>`else GPR[rd] ← tmp₃₁..₀` | 整型溢出时触发 `IntegerOverflow` |
| **ADDI** | `001000 rs rt immediate` | `ADDI rt, rs, imm` | 加立即数（有符号扩展），溢出触发例外 | `tmp ← (GPR[rs]₃₁∥GPR[rs]) + SignExtend(imm)`<br>`if tmp₃₂ ≠ tmp₃₁ then SignalException(IntegerOverflow)`<br>`else GPR[rt] ← tmp₃₁..₀` | 整型溢出时触发 `IntegerOverflow` |
| **ADDU** | `000000 rs rt rd 00000 100001` | `ADDU rd, rs, rt` | 无符号加法，不产生溢出例外 | `GPR[rd] ← GPR[rs] + GPR[rt]` | 无 |
| **ADDIU** | `001001 rs rt immediate` | `ADDIU rt, rs, imm` | 加立即数（有符号扩展），不产生溢出例外 | `GPR[rt] ← GPR[rs] + SignExtend(imm)` | 无 |
| **SUB** | `000000 rs rt rd 00000 100010` | `SUB rd, rs, rt` | 有符号减法，溢出触发例外 | `tmp ← (GPR[rs]₃₁∥GPR[rs]) - (GPR[rt]₃₁∥GPR[rt])`<br>`if tmp₃₂ ≠ tmp₃₁ then SignalException(IntegerOverflow)`<br>`else GPR[rd] ← tmp₃₁..₀` | 整型溢出时触发 `IntegerOverflow` |
| **SUBU** | `000000 rs rt rd 00000 100011` | `SUBU rd, rs, rt` | 无符号减法，不产生溢出例外 | `GPR[rd] ← GPR[rs] - GPR[rt]` | 无 |
| **SLT** | `000000 rs rt rd 00000 101010` | `SLT rd, rs, rt` | 有符号小于置 1 | `if GPR[rs] < GPR[rt] then GPR[rd] ← 1 else GPR[rd] ← 0` | 无 |
| **SLTI** | `001010 rs rt immediate` | `SLTI rt, rs, imm` | 有符号小于立即数置 1 | `if GPR[rs] < SignExtend(imm) then GPR[rt] ← 1 else GPR[rt] ← 0` | 无 |
| **SLTU** | `000000 rs rt rd 00000 101011` | `SLTU rd, rs, rt` | 无符号小于置 1 | `if (0∥GPR[rs]) < (0∥GPR[rt]) then GPR[rd] ← 1 else GPR[rd] ← 0` | 无 |
| **SLTIU** | `001011 rs rt immediate` | `SLTIU rt, rs, imm` | 无符号小于立即数置 1 (立即数仍做有符号扩展) | `if (0∥GPR[rs]) < SignExtend(imm) then GPR[rt] ← 1 else GPR[rt] ← 0` | 无 |
| **DIV** | `000000 rs rt 0000000000 011010` | `DIV rs, rt` | 有符号除法 | `q ← GPR[rs] div GPR[rt]`<br>`LO ← q`<br>`r ← GPR[rs] mod GPR[rt]`<br>`HI ← r` | 除数为 0 时结果未定义 |
| **DIVU** | `000000 rs rt 0000000000 011011` | `DIVU rs, rt` | 无符号除法 | `q ← (0∥GPR[rs]) div (0∥GPR[rt])`<br>`LO ← q`<br>`r ← (0∥GPR[rs]) mod (0∥GPR[rt])`<br>`HI ← r` | 除数为 0 时结果未定义 |
| **MULT** | `000000 rs rt 0000000000 011000` | `MULT rs, rt` | 有符号乘法 | `prod ← GPR[rs] × GPR[rt]`<br>`LO ← prod₃₁..₀`<br>`HI ← prod₆₃..₃₂` | 无 |
| **MULTU** | `000000 rs rt 0000000000 011001` | `MULTU rs, rt` | 无符号乘法 | `prod ← (0∥GPR[rs]) × (0∥GPR[rt])`<br>`LO ← prod₃₁..₀`<br>`HI ← prod₆₃..₃₂` | 无 |

### 逻辑运算指令

| 指令 | 位段表示 (31..0) | 汇编格式 | 功能描述 | 操作定义 (伪代码) | 例外说明 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **AND** | `000000 rs rt rd 00000 100100` | `AND rd, rs, rt` | 位与 | `GPR[rd] ← GPR[rs] & GPR[rt]` | 无 |
| **ANDI** | `001100 rs rt immediate` | `ANDI rt, rs, imm` | 立即数位与 (0扩展) | `GPR[rt] ← GPR[rs] & ZeroExtend(imm)` | 无 |
| **LUI** | `001111 00000 rt immediate` | `LUI rt, imm` | 加载立即数到高16位 | `GPR[rt] ← (imm ∥ 0¹⁶)` | 无 |
| **NOR** | `000000 rs rt rd 00000 100111` | `NOR rd, rs, rt` | 位或非 | `GPR[rd] ← ~(GPR[rs] \| GPR[rt])` | 无 |
| **OR** | `000000 rs rt rd 00000 100101` | `OR rd, rs, rt` | 位或 | `GPR[rd] ← GPR[rs] \| GPR[rt]` | 无 |
| **ORI** | `001101 rs rt immediate` | `ORI rt, rs, imm` | 立即数位或 (0扩展) | `GPR[rt] ← GPR[rs] \| ZeroExtend(imm)` | 无 |
| **XOR** | `000000 rs rt rd 00000 100110` | `XOR rd, rs, rt` | 位异或 | `GPR[rd] ← GPR[rs] ^ GPR[rt]` | 无 |
| **XORI** | `001110 rs rt immediate` | `XORI rt, rs, imm` | 立即数位异或 (0扩展) | `GPR[rt] ← GPR[rs] ^ ZeroExtend(imm)` | 无 |

### 移位指令

| 指令 | 位段表示 (31..0) | 汇编格式 | 功能描述 | 操作定义 (伪代码) | 例外说明 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **SLLV** | `000000 rs rt rd 00000 000100` | `SLLV rd, rt, rs` | 变量逻辑左移 | `s ← GPR[rs]₄..₀`<br>`GPR[rd] ← GPR[rt](₃₁₋ₛ)..₀ ∥ 0ˢ` | 无 |
| **SLL** | `000000 00000 rt rd sa 000000` | `SLL rd, rt, sa` | 立即数逻辑左移 | `s ← sa`<br>`GPR[rd] ← GPR[rt](₃₁₋ₛ)..₀ ∥ 0ˢ` | 无 |
| **SRAV** | `000000 rs rt rd 00000 000111` | `SRAV rd, rt, rs` | 变量算术右移 | `s ← GPR[rs]₄..₀`<br>`GPR[rd] ← (GPR[rt]₃₁)ˢ ∥ GPR[rt]₃₁..ₛ` | 无 |
| **SRA** | `000000 00000 rt rd sa 000011` | `SRA rd, rt, sa` | 立即数算术右移 | `s ← sa`<br>`GPR[rd] ← (GPR[rt]₃₁)ˢ ∥ GPR[rt]₃₁..ₛ` | 无 |
| **SRLV** | `000000 rs rt rd 00000 000110` | `SRLV rd, rt, rs` | 变量逻辑右移 | `s ← GPR[rs]₄..₀`<br>`GPR[rd] ← 0ˢ ∥ GPR[rt]₃₁..ₛ` | 无 |
| **SRL** | `000000 00000 rt rd sa 000010` | `SRL rd, rt, sa` | 立即数逻辑右移 | `s ← sa`<br>`GPR[rd] ← 0ˢ ∥ GPR[rt]₃₁..ₛ` | 无 |

### 分支跳转指令

| 指令 | 位段表示 (31..0) | 汇编格式 | 功能描述 | 操作定义 (伪代码) | 例外说明 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **BEQ** | `000100 rs rt offset` | `BEQ rs, rt, offset` | 相等转移 | `if GPR[rs] = GPR[rt] then PC ← PC + SignExtend(offset∥0²)` | 无 |
| **BNE** | `000101 rs rt offset` | `BNE rs, rt, offset` | 不等转移 | `if GPR[rs] ≠ GPR[rt] then PC ← PC + SignExtend(offset∥0²)` | 无 |
| **BGEZ** | `000001 rs 00001 offset` | `BGEZ rs, offset` | 大于等于0转移 | `if GPR[rs] ≥ 0 then PC ← PC + SignExtend(offset∥0²)` | 无 |
| **BGTZ** | `000111 rs 00000 offset` | `BGTZ rs, offset` | 大于0转移 | `if GPR[rs] > 0 then PC ← PC + SignExtend(offset∥0²)` | 无 |
| **BLEZ** | `000110 rs 00000 offset` | `BLEZ rs, offset` | 小于等于0转移 | `if GPR[rs] ≤ 0 then PC ← PC + SignExtend(offset∥0²)` | 无 |
| **BLTZ** | `000001 rs 10000 offset` | `BLTZ rs, offset` | 小于0转移 | `if GPR[rs] < 0 then PC ← PC + SignExtend(offset∥0²)` | 无 |
| **BGEZAL**| `000001 rs 10001 offset` | `BGEZAL rs, offset` | 大于等于0调用并保存返回地址 | `GPR[31] ← PC + 8`<br>`if GPR[rs] ≥ 0 then PC ← PC + SignExtend(offset∥0²)` | 无 |
| **BLTZAL**| `000001 rs 10000 offset` | `BLTZAL rs, offset` | 小于0调用并保存返回地址 | `GPR[31] ← PC + 8`<br>`if GPR[rs] < 0 then PC ← PC + SignExtend(offset∥0²)` | 无 |
| **J** | `000010 instr_index` | `J target` | 无条件直接跳转 | `PC ← PC₃₁..₂₈ ∥ instr_index ∥ 0²` | 无 |
| **JAL** | `000011 instr_index` | `JAL target` | 无条件跳转并保存返回地址 | `GPR[31] ← PC + 8`<br>`PC ← PC₃₁..₂₈ ∥ instr_index ∥ 0²` | 无 |
| **JR** | `000000 rs 0000000000 00000 001000` | `JR rs` | 寄存器跳转 | `PC ← GPR[rs]` | 无 |
| **JALR** | `000000 rs 00000 rd 00000 001001` | `JALR rd, rs` | 寄存器跳转并保存返回地址 | `temp ← GPR[rs]`<br>`GPR[rd] ← PC + 8`<br>`PC ← temp` | 无 |

### 数据移动指令

| 指令 | 位段表示 (31..0) | 汇编格式 | 功能描述 | 操作定义 (伪代码) | 例外说明 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **MFHI** | `000000 0000000000 rd 00000 010000` | `MFHI rd` | HI -> GPR | `GPR[rd] ← HI` | 无 |
| **MFLO** | `000000 0000000000 rd 00000 010010` | `MFLO rd` | LO -> GPR | `GPR[rd] ← LO` | 无 |
| **MTHI** | `000000 rs 000000000000000 010001` | `MTHI rs` | GPR -> HI | `HI ← GPR[rs]` | 无 |
| **MTLO** | `000000 rs 000000000000000 010011` | `MTLO rs` | GPR -> LO | `LO ← GPR[rs]` | 无 |

### 自陷指令

| 指令 | 位段表示 (31..0) | 汇编格式 | 功能描述 | 操作定义 (伪代码) | 例外说明 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **BREAK** | `000000 code 001101` | `BREAK` | 触发断点例外 | `SignalException(Breakpoint)` | 触发 `Breakpoint` 例外 |
| **SYSCALL**| `000000 code 001100` | `SYSCALL` | 触发系统调用例外 | `SignalException(SystemCall)` | 触发 `SystemCall` 例外 |

### 访存指令

| 指令 | 位段表示 (31..0) | 汇编格式 | 功能描述 | 操作定义 (伪代码) | 例外说明 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **LB** | `100000 base rt offset` | `LB rt, offset(base)` | 取字节（有符号扩展） | `vAddr ← GPR[base] + SignExtend(offset)`<br>`membyte ← LoadMemory(vAddr, BYTE)`<br>`GPR[rt] ← SignExtend(membyte)` | 无 |
| **LBU** | `100100 base rt offset` | `LBU rt, offset(base)` | 取字节（无符号扩展） | `vAddr ← GPR[base] + SignExtend(offset)`<br>`membyte ← LoadMemory(vAddr, BYTE)`<br>`GPR[rt] ← ZeroExtend(membyte)` | 无 |
| **LH** | `100001 base rt offset` | `LH rt, offset(base)` | 取半字（有符号扩展） | `vAddr ← GPR[base] + SignExtend(offset)`<br>`if vAddr₀ ≠ 0 then SignalException(AddressError)`<br>`memhalf ← LoadMemory(vAddr, HALFWORD)`<br>`GPR[rt] ← SignExtend(memhalf)` | 地址最低 1 位不为 0，触发 `AddressError` |
| **LHU** | `100101 base rt offset` | `LHU rt, offset(base)` | 取半字（无符号扩展） | `vAddr ← GPR[base] + SignExtend(offset)`<br>`if vAddr₀ ≠ 0 then SignalException(AddressError)`<br>`memhalf ← LoadMemory(vAddr, HALFWORD)`<br>`GPR[rt] ← ZeroExtend(memhalf)` | 地址最低 1 位不为 0，触发 `AddressError` |
| **LW** | `100011 base rt offset` | `LW rt, offset(base)` | 取字 | `vAddr ← GPR[base] + SignExtend(offset)`<br>`if vAddr₁..₀ ≠ 0 then SignalException(AddressError)`<br>`memword ← LoadMemory(vAddr, WORD)`<br>`GPR[rt] ← memword` | 地址最低 2 位不为 0，触发 `AddressError` |
| **SB** | `101000 base rt offset` | `SB rt, offset(base)` | 存字节 | `vAddr ← GPR[base] + SignExtend(offset)`<br>`StoreMemory(vAddr, BYTE, GPR[rt]₇..₀)` | 无 |
| **SH** | `101001 base rt offset` | `SH rt, offset(base)` | 存半字 | `vAddr ← GPR[base] + SignExtend(offset)`<br>`if vAddr₀ ≠ 0 then SignalException(AddressError)`<br>`StoreMemory(vAddr, HALFWORD, GPR[rt]₁₅..₀)` | 地址最低 1 位不为 0，触发 `AddressError` |
| **SW** | `101011 base rt offset` | `SW rt, offset(base)` | 存字 | `vAddr ← GPR[base] + SignExtend(offset)`<br>`if vAddr₁..₀ ≠ 0 then SignalException(AddressError)`<br>`StoreMemory(vAddr, WORD, GPR[rt]₃₁..₀)` | 地址最低 2 位不为 0，触发 `AddressError` |

### 特权指令

| 指令 | 位段表示 (31..0) | 汇编格式 | 功能描述 | 操作定义 (伪代码) | 例外说明 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **ERET** | `010000 1 000...000 011000` | `ERET` | 例外处理返回 | `PC ← EPC`<br>`Status.EXL ← 0` | 仅在 `Status.EXL=1` 时有效 |
| **MFC0** | `010000 00000 rt rd 00000000 sel` | `MFC0 rt, rd, sel` | 读 CP0 寄存器 | `GPR[rt] ← CP0[rd, sel]` | 访问非法 CP0 寄存器时触发 `ReservedInstruction` |
| **MTC0** | `010000 00100 rt rd 00000000 sel` | `MTC0 rt, rd, sel` | 写 CP0 寄存器 | `CP0[rd, sel] ← GPR[rt]` | 访问非法 CP0 寄存器或只读位时触发 `ReservedInstruction` |

## 存储管理

本指令系统对操作模式和存储访问类型进行了严格的限定，所以存储管理部分仅对虚实地址映射方式进行定义。
处理器可访问32位虚地址空间。整个4GB大小的虚地址空间被划分成5个段。处理器采用固定地址映射（FMT）机制，在进行虚实地址映射时，不同段的虚地址以线性方式固定地映射到一段连续的物理地址上。32位虚地址空间划分为 5 个段：

- **kuseg (2GB)**: `0x0000_0000 - 0x7FFF_FFFF` (用户态，可缓存/不可缓存)
- **kseg0 (512MB)**: `0x8000_0000 - 0x9FFF_FFFF` (核心态，直接映射，可缓存)
- **kseg1 (512MB)**: `0xA000_0000 - 0xBFFF_FFFF` (核心态，直接映射，不可缓存)
- **kseg2 (512MB)**: `0xC000_0000 - 0xDFFF_FFFF` (核心态，保留)
- **kseg3 (512MB)**: `0xE000_0000 - 0xFFFF_FFFF` (核心态，保留)

### 存储器与地址映射

考虑到```MIPS```体系结构兼容性，同时兼顾避免流水线处理器存储访问出现的结构冒险，在没有使用Cache设计的情况下简化设计。本次实验假设处理指令存储器与数据存储器在物理上为独立模块，但仍然统一编址，容量各为 64 KB。其中，指令存储器地址空间```0xBFC0_0000 ~ 0xBFC0_FFFF```，数据存储器地址空间```0xBFC1_0000 ~ 0xBFC1_FFFF```。后续实验在此基础上将会进一步调整细化。
    Testbench中指令存储器（Instruction Memory）和数据存储器（Data Memory）具有单独模块。

#### 1. 虚拟地址空间布局 (KSeg1)

本设计采用 MIPS32 经典的 **固定地址映射 (Fixed Memory Map)** 策略。在当前开发阶段（验证与仿真），所有代码与数据均映射至 **KSeg1 (Uncached)** 区域，以简化硬件译码逻辑并避免 Cache 一致性问题。

| 虚拟地址范围 (Hex) | 段名称 | 大小 | 缓存属性 | 用途说明 |
| :--- | :--- | :--- | :--- | :--- |
| `0xBFC0_0000 - 0xBFC0_FFFF` | **Code Segment** | 64 KB | Uncached | **主代码段 (IMEM)**。包含复位向量、异常入口及用户程序。 |
| `0xBFC1_0000 - 0xBFC1_FFFF` | **Data Segment** | 64 KB | Uncached | **主数据段 (DMEM)**。存放全局变量、堆栈及静态数据。 |
| `0xBFC0_0380` | **Exception Vector** | - | Uncached | **通用例外入口地址**。硬件规定跳转至此执行例外处理。 |
| `0xBFC0_0000` | **Reset Vector** | - | Uncached | **复位入口地址**。上电后 PC 初始值。 |

#### 2. 物理地址映射关系

在 KSeg1 区域，虚拟地址到物理地址的转换遵循简单的减法逻辑：
$$ \text{Physical Address} = \text{Virtual Address} - 0xA000\_0000 $$

*   **IMEM 译码**: 当 `PC[31:16] == 16'hBFC0` 时，选中 IMEM。局部地址索引为 `PC[15:2]` (14-bit)。
*   **DMEM 译码**: 当 `Addr[31:16] == 16'hBFC1` 时，选中 DMEM。局部地址索引为 `Addr[15:2]` (14-bit)。

### 存储器访问延迟特性

考虑到未来原型将在FPGA上实现，所有存储器访问都存在**1拍的采样延时**。即存储器读取时，需要在发出读使能信号后的下一个时钟上升沿才能稳定获得数据。

#### 1. 时序影响分析

*   **取指阶段 (IF)**: `instr_addr` 在周期 T 给出，`instr` 在周期 T+1 返回。这要求流水线在 IF 级必须处理这种固有的延迟。
*   **访存阶段 (MEM)**: `dmem_addr` 和 `dmem_re` 在周期 T 给出，`dmem_rdata` 在周期 T+1 返回。
*   **Load-Use 冒险**: 由于 `lw` 指令在 MEM 阶段结束时（T+1）才能拿到数据，而紧随其后的指令在 EX 阶段（T+1）就需要该数据，因此**必须插入一个 Stall（气泡）**来暂停流水线一拍。

#### 2. 硬件实现建议

*   **Hazard Detection Unit**: 必须在 ID 阶段检测 `EX/MEM` 阶段的 Load 指令是否与 `ID/EX` 阶段的源寄存器冲突。若冲突，则暂停 `PC` 和 `IF/ID` 寄存器更新，并在 `EX` 阶段插入 `NOP`。
*   **Forwarding Unit**: 对于非 Load 指令产生的 ALU 结果，可以通过旁路直接从 `EX/MEM` 或 `MEM/WB` 阶段前递到 `EX` 阶段输入端，从而消除大部分数据冒险。

## 指令寻址

    上电后，处理器第一条指令地址为 ```0xBFC0_0000```，采用字节地址寻址方案，即每条指令具有```32 bits```即```4 Byte```；取指时地址更新应为4字节，即```PC + 4 Byte```。

## 冒险问题(这部分设计需要在Spec文件种详细说明)：

### 数据冒险

数据冒险全部能够检测出来，支持完全的数据冒险前递和旁路，当lw指令和下一条指令存在数据冒险，即lw写回的寄存器是下一条指令的输入寄存器，这是应该考虑增加一个stall，防止冒险发生。同时这里应该考虑存储器访问需要一拍，应该考虑提前发送存储器访问地址。

### 结构冒险

使用了指令存储和数据存储分开的策略，定序单发射流水线目前结构冒险不存在；

### 控制冒险

支持MIPS延迟槽指令特性。MIPS体系结构规范要求分支跳转指令是具有延迟槽的, 即如下如下```bne```分支跳转指令后的指令必须先被执行，再执行分支跳转目标。因此，在所有分支指令之后都会插入```nop```作为延迟操。在编译时```nop```会被汇编器设置为```0x0000_0000```。

```asm
    bne   a0, zero, loop1
    nop
```

在此基础上，消除控制冒险可以采用总是跳转（Always Taken）的思路。在取指令和译码的过程中进行最简单的分支预测方法，无论条件如何，都预测分支总是被执行。保证在译码级可以取得下一条指令。如果出现了预测错误，即出现了不跳转（Not Taken）的情况，则进行指令流水线的冲刷，将预测错误的所有指令流出流水线，保证对寄存器和存储器不产生影响。退回执行不跳转的指令。
这里用一个特殊的例子（上电后第一条指令即为分支指令）说明在延迟槽特性下总是跳转分支预测的基本过程。

- IF段设置一个PC寄存器,上电复位```0xbfbfffff```，代表当前IF段取出的指令的PC。 上电时正因为没有发出访存请求，```bfc00000```的指令还未读出，所以是```0xbfbfffff```。
- 使用PC寄存器+4的数值和ID段计算出的```Dest```(分支跳转目的)进信号行二选一， 进行选择的信号是ID段的```isTake```(表示当前ID段的分支跳转指令是否需要跳转)信号。 ID段复上电复位时，因为ID段没有任何指令，所以通过ID段的段间寄存器为isTake复位为1'b0。 将二选一结果记为nextPC, 此时线网nextPC是bfc00000
- 上电第一周期```clk0```，将取指总线上的addr和PC寄存器的的写入值赋值为线网信号nextPC,即```bfc00000```，但PC需要等下一个上跳沿采样保存。 上电第二周期```clk1```，PC寄存器值被改写，值是```bfc00000```,存储器读出的数据为```bfc00000```处的指令。 该指令进入IF段。 此时的nextPC为bfc00004
- 如果bfc00000是跳转指令，跳转地址为bfc00100。 则上电第二周期```clk1```的nextPC = bfc00004对应的就是延迟槽指令。 上电第三周期```clk2```存储器读出延迟槽指令，PC变为bfc00004，即延迟槽指令在IF段， bfc00000的分支指令已经离开IF段进入ID段了。 由于段内是组合逻辑，因此isTake变为1，Dest变为跳转目的，同时nextPC变为Dest。 下一周期即可读出跳转目的，实现无延迟无气泡流水线。
|variable|clk0|clk1|clk2|clk3|  
|reg [31:0] PC|0xbfbfffff|0xbfc00000|0xbfc00004|0xbfc00100|
|reg isTake|1’b0|1’b0|1’b1|1’b0|
|reg [31:0] Dest|any|any|bfc00100|any|
|wire [31:0] nextPC|bfc00000|bfc00004|bfc00100|bfc00104|

## 复位行为
当 rst_n 为低电平时，处理器异步复位：
pc 复位为 0xBFC0_0000，处理器取值第一条指令从指令存储器地址 0xBFC0_0000 开始。注意pc 寄存器在设计时取得第一条指令的地址都应该能够指向指令存储器的第一条指令位置。
寄存器复位。寄存器堆内容初始化为 0，但 $0 寄存器始终为 0。

复位采用异步复位同步释放机制，即外部复位信号需采用复位桥进行2次或更多次采样采样保证同步释放。复位释放后，每个时钟上升沿，处理器自动更新 PC 并开始取指、执行，实现不间断的指令流。

## 中断与例外

所有例外（含中断）的例外入口地址统一为0xBFC0_0380
详细设计参考```doc/A03_“系统能力培养大赛”MIPS指令系统规范_v1.01.pdf```第五节“5 中断与例外”。

## 系统控制寄存器

结合中断和例外的设计，实现部分```CP0```寄存器，具体要求参考```doc/A03_“系统能力培养大赛”MIPS指令系统规范_v1.01.pdf```第六节“6 系统控制寄存器”。

# Step 3 设计Spec -> 模块划分


在进行这一步之前，应该先人工确认spec文档的情况。

根据```doc/CPUYellow_spec.md```，将处理器划分为多个可行的模块，形成详细设计文档。文档中应包含顶层的模块结构图，每个模块的接口定义。每个模块形成详细的自然语言设计描述，对内部的状态机或者复杂组合逻辑进行描述。对模块的输入输出信号时序进行说明。

# Step4 模块详细设计 -> 按照模块设计RTL


在进行这一步之前，应该先人工确认包含模块设计的详细设计文档的情况。

根据设计生成的Spec文件以及详细设计文档，设计RTL，处理器顶层模块名称必须固定为 **cpu_yellow_top**，其端口定义、位宽及方向须严格遵循本文档接口规范，不得修改或增减信号。顶层文件保存在```src/rtl/cpu_yellow_top.v```，其他模块文件保存在```src/rtl/```文件夹下。

# step 4 RTL 语法lint检查

使用规则lint进行检查。

# step 5 设计Spec + RTL -> TB for UT

根据```doc/CPUYellow_spec.md```以及生成的RTL文件，创建systemverilog仿真验证平台，设计testbench文件。testbench文件即tb文件，tb文件顶层应该为```cpu_yellow_top_tb```，保存在```src/tb/cpu_yellow_top_tb.sv```，其他tb文件保存在```src/tb/```文件夹下。测试程序应该能够逐条指令完成仿真。
    
# step 6 调用 UVS UVD 做仿真验证

如果有UDA2.0设计环境支持，使用UVS UVD进行仿真验证。
根据仿真验证结果，判断处理器是否符合设计。如果符合设计，继续进行后续步骤。否则，返回设计阶段，重新设计。需要统计验证覆盖率情况。

# step 7 使用verilator进行仿真测试

如果已经使用了UVS UVD进行仿真验证，跳过这个步骤。如果没有UDA2.0设计环境支持，使用verilator进行仿真测试。
verilator应收集覆盖率：```verilator --coverage```
建议开启波形查看，观察关键信号：PC、instr、ALU结果、写使能、存储器读写等。

# step 8 生成报告
完成仿真验证报告，包括仿真验证结果、覆盖率报告、波形查看等文件。人工提交设计总结报告。
所有报告文档均为**markdown格式**，即文件格式为 **.md**
    

<!-- ### 7.2 文件结构及说明
```
学号_姓名/
    ├── src/
    │   ├── rtl/
    |   |    └── cpu_yellow_top.v
    │   └── tb/
    |        └── 根据需要创建文件，使用tb_cpu_yellow_top_tb命名顶层module及文件
    ├── doc/
    |        ├── CPUYellow_spec.md
    |        ├── CPUYellow_veri_rpt.md
    |        └── CPUYellow_report.md(人工完成的个人设计总结报告)
    ├── appendix/
    └── README.md



**rtl**：该文件夹下存放CPU_YELLOW的源代码，其中cpu_yellow_top.v为top module，名称不可更改。

**tb**：该文件夹下存放testbench文件及其他测试文件。可以根据需要选择文件类型。

**doc**：该文件夹下存放三个报告文件，分别是CPUYellow_spec.md、CPUYellow_veri_rpt.md、CPUYellow_report.md。其中CPUYellow_report.md为人工完成的个人设计总结报告。

**appendix**：该文件夹下存放附件，包括仿真验证过程中产生的中间文件、结果输出文件、提示词及模型交互历史等，例如覆盖率报告、波形文件等。

**README.md**：用于描述任何文件夹情况、编译运行步骤或特殊说明，可自行确定内容。 -->
