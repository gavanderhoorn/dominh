
CC=ktrans.exe
SUPPORT_VER?=V7.70-1
CFLAGS=/ver $(SUPPORT_VER)

SRCS=dmh_selprg.kl dmh_autom.kl dmh_simkey.kl

OBJS=$(SRCS:.kl=.pc)

.PHONY: clean

all: $(OBJS)

clean:
	@del /q /f $(OBJS) 2>nul

help:
	@echo "Build the Dominh helper programs with ktrans."
	@echo ""
	@echo "Requires 'ktrans.exe' to be on the path."
	@echo "Define 'SUPPORT_VER' to compile for system versions other than the"
	@echo "default 'V7.70-1'. To build for an 9.10 system:"
	@echo ""
	@echo "    make SUPPORT_VER=V9.10-1"
	@echo ""

%.pc: %.kl
	@$(CC) $^ $(CFLAGS)
