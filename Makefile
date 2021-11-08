ifeq ($(DESTDIR), )
  PYINSTALLARGS =
else
  PYINSTALLARGS = --root=$(DESTDIR)
endif

.PHONY: test
test:
	./RectClient.py
clean:
	rm -rf build/
install:
	if which python2; then python2 setup.py install $(PYINSTALLARGS); fi
	if which python3; then python3 setup.py install $(PYINSTALLARGS); fi
uninstall:
	if which python2; then python2 setup.py install $(PYINSTALLARGS) --record /tmp/rect.txt >/dev/null; sed 's!^!$(DESTDIR)!' < /tmp/rect.txt | xargs rm -f >/dev/null; fi
	if which python3; then python3 setup.py install $(PYINSTALLARGS) --record /tmp/rect.txt >/dev/null; sed 's!^!$(DESTDIR)!' < /tmp/rect.txt | xargs rm -f >/dev/null; fi

