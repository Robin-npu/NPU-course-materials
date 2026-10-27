TOPLEVEL_LANG = verilog
VERILOG_SOURCES = cpu_red_top.v
TOPLEVEL = cpu_red_top
MODULE = tb_cpu_red_top

SIM = verilator

EXTRA_ARGS += --trace --coverage

include $(shell cocotb-config --makefiles)/Makefile.sim