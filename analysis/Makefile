# Change this directory to point to session data. Make sure 
# there is no space between := and directory path.
DATADIR:=$(HOME)/Desktop/Work/Behaviour/MouseS221/MouseS221_SessionType1_Session1/
DATADIR:=../../MouseS266/
CURRDIR:=$(shell pwd)
RESULT_DIR:=$(CURRDIR)/_results

all :  performance_index 
	python performance_curve.py $(RESULT_DIR)


performance_index : init
	./run_on_all_session.sh $(DATADIR) $(RESULT_DIR)


init :
	mkdir -p $(RESULT_DIR)
