import os,subprocess,sys,time,logging,re
from datetime import datetime
from time import gmtime,strftime

def is_too_old(path):
	global cut_off_date
	input_date_obj =  datetime.strptime(cut_off_date,'%d/%m/%Y')
	datestr = [int(x) for x in cut_off_date.split('/')]
	t = os.path.getmtime(path)
	FMT = '%d/%m/%Y'
	time_string = time.strftime(FMT,time.gmtime(t))
	time_string = datetime.strptime(time_string,'%d/%m/%Y')
	delta = (time_string - input_date_obj).days < 0
	return delta

cut_off_date = "25/12/2014"

path = "/Volumes/ITMADATA/VIDEO/ITMA video field recordings/in process/ITMA field recordings of Scoil Samhraidh Gaoth Dobhair 2014-2015/uilleann pipes recital/card 2/CONTENTS/CLIPS001/AA0332/AA033201.MXF"

print is_too_old(path)