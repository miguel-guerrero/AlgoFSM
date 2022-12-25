
test:
	make -C tests test
	make -C unit_tests test

gls:
	make -C tests gls

clean:
	make -C tests clean
	make -C unit_tests clean
	$(RM) -r __pycache__ .mypy_cache
	$(RM) -r algofsm/__pycache__ algofsm/.mypy_cache
