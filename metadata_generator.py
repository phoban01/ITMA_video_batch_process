import os,binascii,collections,json
import glob
import subprocess
import time
import datetime
import re

# two processes. 
# 1. generate a default json document which can be edited to insert performers names
# and basic metadata

# 2. a processor that can fill in other details using ffprobe for duration,
# other basic metadata. uses main performers field to get names. generates refnos
# and folders. also needs to generate accession number

def ffmpeg_version():
	return subprocess.check_output(["ffmpeg","-version"]).split('\n')[0].strip()

def format_duration(string):
	time_obj = datetime.datetime.strptime(string,"%H:%M:%S")	
	if time_obj.hour == 0:
		return time_obj.strftime('%M min., %S sec.')
	elif time_obj.hour > 0 and time_obj.hour < 2:
		return time_obj.strftime('%H hr., %M min., %S sec.').lstrip('0')
	else:
		return time_obj.strftime('%H hrs., %M min., %S sec.').lstrip('0')

def get_creation_date(path):
	t = os.path.getctime(path)
	date = datetime.datetime.fromtimestamp(t)
	date = date.strftime("%d %B %Y")
	return str(date)

def generate_record(refno,file_type):
	data = collections.OrderedDict({"REFNO":refno,'AccessionNumber': "%s-%s" % (refno,binascii.b2a_hex(os.urandom(3)))})
	data['Title'] = ''
	data['MainPerformers'] = ''
	data['Name'] = ''	
	data['Collector'] = ''
	if file_type == 'MP4':
		data['ArchiveLocation'] = 'Server'
	elif file_type == 'MXF':
		data['ArchiveLocation'] = 'Server : {server location}'
	if file_type == 'MP4':
		data['Image_MAC'] = '{server location}'
	data['Subject'] = ''
	data['Language'] = ['English']
	data['Country'] = 'Ireland'
	data['Decade'] = '{decade}'
	data['RecordingLocation'] = ''
	data['RecordingDate'] = '{recording date}'
	data['RunningTime'] = '{duration}'
	data['MaterialType'] = '{filetype} file'
	data['SoutronRelationships'] = '{sibling refno}'
	data['PhysicalDescription'] = '1 computer file ({filetype}, {duration}) : digital, stereo'
	data['Notes'] = """Video recorded using Canon XF100 (Canon XD Codec) @ 1080p. 
	Audio from stereo pair of small diaphragm condenser microphones recorded to Sound Devicess 722 @ 48kHz, 24 bit. 
	1080p {filetype} file created on {creation date} using {ffmpeg version}."""
	if file_type == 'MXF':
		data['Notes'] += '\nUsers may not have access to master copy.'
	data = json.dumps(data,indent=2)
	return data

def parse_metadata(string):
	data = ["ITEMS:","CREATED ON:","CONTENTS DURATIONS:","THE FOLLOWING NAMES WERE FOUND:"]
	ix = []
	for i in data:
		ix.append(string.find(i))
	splits = []
	for i,j in enumerate(ix):
		if i != len(ix)-1:
			splits.append(string[ix[i]:ix[i+1]])
	parsed = {"durations":[],"dates":[]}
	for i,j in enumerate(data):
		if i == 1:
			for item in splits[i].strip(j).strip().split('\n'):
				clean_date = re.match(r'(ITEM \d+:)\s(\d+\s\w+\s\d+)\s',item.strip()).groups()[-1]
				parsed['dates'].append(clean_date)
		elif i == 2:
			for item in splits[i].strip(j).strip().split('\n'):
				clean_duration = re.match(r'(ITEM\s\d+)\s(Duration:)(\d+:\d+:\d+)',item.strip()).groups()[-1]
				parsed['durations'].append(format_duration(clean_duration))
	return parsed

ROOT = "/Volumes/ITMAVideoDrobo/*"

total_number_of_videos = 0

for event in glob.glob(ROOT):
	metadata_path = os.path.join(event,"folder_metadata.txt")
	if os.path.exists(metadata_path):	
		with open(metadata_path,"r") as f:
			event_md = f.read()
		metadata = parse_metadata(event_md)
		for subfolder in glob.glob(event + "/*"):
			if os.path.isdir(subfolder):
				for i,video_file in enumerate(glob.glob(subfolder + '/*[.MXF .MP4]')):
					duration = metadata['durations'][i]
					recording_date = metadata['dates'][i]
					decade = "%ds"% (int(recording_date.split()[-1]) - int(list(recording_date.split()[-1])[-1]))
					file_type = video_file.split('.')[-1].upper()
					creation_date = get_creation_date(video_file)
					metadata_json = generate_record('{REFNO}-ITMA-%s'%file_type,file_type)
					metadata_json = metadata_json.replace('{duration}',duration)
					metadata_json = metadata_json.replace('{filetype}',file_type)
					metadata_json = metadata_json.replace('{recording date}',recording_date)
					metadata_json = metadata_json.replace('{creation date}',creation_date)
					metadata_json = metadata_json.replace('{ffmpeg version}',ffmpeg_version())
					metadata_json = metadata_json.replace('{decade}',decade)
					json_file = open(video_file + '.json','w')
					json_file.write(metadata_json)
					json_file.close()
					total_number_of_videos += 1

print total_number_of_videos
