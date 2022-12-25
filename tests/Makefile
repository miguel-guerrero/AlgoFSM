.ONESHELL:

PASS=motor matmul1 matmul2 matmul3 test_seq1 test_seq2 tpg1 tpg2 tpg3 for1 for2 for3 for4 
DISABLED=ahb-lite-m spi-s

test:
	for i in $(PASS); do echo "=== $$i ===" ; make -C $$i test || exit 1; done
	@echo "All tests runned passed"

gls:
	for i in $(PASS); do echo "=== $$i ===" ; make -C $$i gls || exit 1; done
	@echo "All tests runned passed"

clean:
	for i in $(PASS); do echo "=== $$i ===" ; make -C $$i clean || exit 1; done
	for i in $(DISABLED); do echo "=== $$i ===" ; make -C $$i clean || exit 1; done
