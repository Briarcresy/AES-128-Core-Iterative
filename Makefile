ROOT := $(CURDIR)
STA_DIR := $(ROOT)/yosys-sta
DESIGN := Aes128Iterative
SDC_FILE := $(ROOT)/constraints/Aes128Iterative.sdc
RESULT_DIR := $(ROOT)/backend/sta-results
CLK_FREQ_MHZ ?= 20
PPA_RESULT_DIR := $(RESULT_DIR)/$(DESIGN)-$(CLK_FREQ_MHZ)MHz
SBOX_MEM := $(ROOT)/mem/sbox.mem
ROM_CODE := $(ROOT)/pdk/IP/ROM/ics55_ecos_rom_256x8_m8_b1/verilog/ics55_ecos_rom_256x8_m8_b1.romcode
ROM_LIB := $(ROOT)/pdk/IP/ROM/ics55_ecos_rom_256x8_m8_b1/lib/ics55_ecos_rom_256x8_m8_b1_tt1p2v25cctyp.lib
ROM_SIM_MODEL := pdk/IP/ROM/ics55_ecos_rom_256x8_m8_b1/verilog/ics55_ecos_rom_256x8_m8_b1_core.v
PPA_TOOL_LOG := $(PPA_RESULT_DIR)/ppa-tool.log

RTL_FILES := $(addprefix $(ROOT)/,$(shell cat $(ROOT)/files.f))

.PHONY: test test-rom test-mix test-core test-wrapper lint romcode prepare-sta sta ppa

romcode: $(ROM_CODE)

$(ROM_CODE): $(SBOX_MEM) scripts/generate_romcode.py
	@python3 scripts/generate_romcode.py >/dev/null

test-rom: romcode
	iverilog -g2005 -I. -s tb_sbox_rom -o /tmp/aes_sbox_rom.vvp tests/tb_sbox_rom.v rtl/core/sbox_rom.v $(ROM_SIM_MODEL)
	vvp /tmp/aes_sbox_rom.vvp

test-mix:
	iverilog -g2005 -I. -s tb_mix_column -o /tmp/aes_mix_column.vvp tests/tb_mix_column.v rtl/core/mix_column.v
	vvp /tmp/aes_mix_column.vvp

test-core: romcode
	iverilog -g2005 -I. -s tb_aes128_iterative -o /tmp/aes_core.vvp tests/tb_aes128_iterative.v $$(grep '^rtl/core/' files.f) $(ROM_SIM_MODEL)
	vvp /tmp/aes_core.vvp

test-wrapper: romcode
	iverilog -g2012 -I. -s tb_aes128_wrapper -o /tmp/aes_wrapper.vvp tests/tb_aes128_wrapper.sv $$(grep '^rtl/' files.f) $(ROM_SIM_MODEL)
	vvp /tmp/aes_wrapper.vvp

test: test-rom test-mix test-core test-wrapper

lint:
	verilator --lint-only -Wall -Wno-fatal --top-module $(DESIGN) -I. $(RTL_FILES)

prepare-sta:
	@python3 scripts/configure_yosys_sta.py >/dev/null

sta: romcode prepare-sta
	@mkdir -p $(PPA_RESULT_DIR)
	@if ! $(MAKE) --no-print-directory -C $(STA_DIR) sta \
		DESIGN=$(DESIGN) \
		SDC_FILE=$(SDC_FILE) \
		CLK_FREQ_MHZ=$(CLK_FREQ_MHZ) \
		CLK_PORT_NAME=clock \
		EXTRA_LIB_FILES=$(ROM_LIB) \
		O=$(RESULT_DIR) \
		RTL_FILES="$(RTL_FILES)" >$(PPA_TOOL_LOG) 2>&1; then \
		printf 'STA tool failed. Last 80 log lines:\n' >&2; \
		tail -n 80 $(PPA_TOOL_LOG) >&2; \
		exit 1; \
	fi
	@$(ROOT)/scripts/ppa_summary.sh $(PPA_RESULT_DIR) $(DESIGN) $(CLK_FREQ_MHZ)

ppa: sta
