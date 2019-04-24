
import os
import shutil
import tempfile

tempfolder = tempfile.gettempdir()

print(len(os.listdir(tempfolder)))
for item in os.listdir(tempfolder):
	ipath = os.path.join(tempfolder,item)
	if os.path.isdir(ipath):
		contents = os.listdir(ipath)
		if item.startswith('tmp'):
			try:
				if all([(fname.startswith('mpet') and fname.endswith('.dat')) for fname in contents]):
					print('Removing tempdir: {}'.format(item))
					shutil.rmtree(ipath)
				elif all([(fname=='preproc_imgtemp.dat' or fname=='imfile.dat') for fname in contents]):
					print('Removing tempdir: {}'.format(item))
					shutil.rmtree(ipath)
			except Exception as e:
				print('Falied to remove tempdir in clean_tempdir: {}'.format(item))
				print('Exception: {}'.format(e))