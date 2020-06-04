# Uses the defined CC environment variable to find a suitable compiler
# for the kernel extension
#
# Note:
#   the setup.py build target does *NOT* update the _wf.so extension.
#   to do so, use the develop target (that it is why it appears first).

hgroot:=$(shell hg root)

develop: 
	pip install -e ./ --user

# The minus sign means ignore any errors (e.g. if there is nothing to uninstall)
install:
	-pip uninstall altis
	pip install ./

uninstall:
	-pip uninstall altis

clean:
	\rm -rf build _*.so
	find . -name __pycache__ | xargs \rm -rf
	find . -name *.pyc | xargs \rm -f
	find . -name *.so | xargs \rm -f
	python setup.py clean

clean_all:
	\rm -rf build _*.so
	find . -name *.egg-info | xargs \rm -rf
	find . -name *.eggs | xargs \rm -rf
	find . -name __pycache__ | xargs \rm -rf
	find . -name *.pyc | xargs \rm -f
	find . -name *.so | xargs \rm -f

tests:
#	nosetests -w tests 
	nosetests -v tests 

tags:
	ctags -R -f .tags

.PHONY: clean tests
