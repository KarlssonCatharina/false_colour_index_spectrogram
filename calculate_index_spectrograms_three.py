

#ensure you have the correct version of matplotlib installed, version 2.1.0 does not work. For mac specify in terminal with: "pip3 install matplotlib==2.0.2"

import os, glob

import numpy as np
from scipy.stats import entropy

import librosa



# some constants
statnames = ['fentropy', 'aci', 'specpow']  # these are the stats that we use for the RGB channels
choplensecs = 60

############################################################
# some acoustic indices

def fentropy(spectro):
	"Calculate entropy of each frequency bin separately"
	return np.array([entropy(row) for row in spectro])

def aci(spectro):
	"Calculate ACI of spectrogram for each freq bin separately"
	return np.array([np.sum(np.abs(row[1:] - row[:-1]))/np.sum(row) for row in spectro])

def magsum(spectro):
	  "Calculate sum-of-magnitudes for each freq bin separately"
	  return np.sum(spectro,axis=1)

def specpow(spectro):
	"Calculate power for each freq bin separately"
	return np.mean(spectro * spectro, axis=1)


############################################################
# functions to calc the stats

def calculate_index_spectrogram_singlecolumn(spectro):
	"""Calculates a single 'column', i.e. it assumes the supplied spectrogram represents a single temporal window to be summarised into a single column pixel."""
	stats = [
		aci(spectro),
		specpow(spectro),
	]
	#print("   shapes: %s" % [np.shape(entry) for entry in stats])
	return stats

def calculate_index_spectrograms(infpath):
	"""Supply either a list of wav file paths, or a folder to be globbed, or a single file path (to be chopped into 60s chunks).
	This is a generator function which will create an ITERATOR, returning one new column of index-pixel data on every loop of the iter."""

	dochop = False
	if type(infpath) in [str]:
		if not os.path.exists(infpath):
			raise ValueError("Path not found: %s" % infpath)
	else:
		for aninfpath in infpath:
			if not os.path.exists(aninfpath):
				raise ValueError("Path not found: %s" % aninfpath)

	#############################################
	# Handle user argument - either a foldername, or a list of files, or a single file which we will auto-chop
	if type(infpath) in [str]:
		if os.path.isdir(infpath):
			# if a single folder, we auto-expand it to a sorted list of the files found immediately within that folder
			infpath = sorted(glob.iglob(os.path.join(infpath, "*.wav")))
		else:
			# a single non-directory item submitted? then convert to a singleton list, and YES we'll chop it
			infpath = [infpath]
			dochop = True
	else:
		# a list has been supplied. could be from the CLI arguments, even if it's a single item.
		if len(infpath)==1:
			dochop = True

	#############################################
	# at this point we expect infpath to be a list of wav filepaths. (if the user submitted a list of something-elses, this assumption could break. caveat emptor)
	for aninfpath in infpath:
		#print(aninfpath)
		audiodata, audiosr = librosa.core.load(aninfpath, sr=None, mono=True)
		#print("Full audio duration is %s samples (%i seconds)" % (np.shape(audiodata), len(audiodata)/audiosr))
		if dochop:
			choplenspls = int(librosa.core.time_to_samples(choplensecs, audiosr)[0])
		else:
			choplenspls = len(audiodata)

		for whichchunk, offset in enumerate(range(0, len(audiodata), choplenspls)):
			#print("    chunk %i is [%i:%i]" % (whichchunk, offset, offset+choplenspls))
			audiochunk = audiodata[offset:offset+choplenspls]
			spectro = abs(librosa.core.stft(audiochunk))
			somedata = calculate_index_spectrogram_singlecolumn(spectro)
			yield somedata


def calculate_and_write_index_spectrograms(infpath, output_dir):
	"""simply iterates over the 1ry func and writes out files in our standard format (each channel a separate file, and each file a npz array)"""

	# Make output directory if it doesn't exists
	if not os.path.exists(output_dir):
		os.makedirs(output_dir)

	arrays = [[] for statname in statnames]
	for results in calculate_index_spectrograms(infpath):
		for (anarray, aresult) in zip(arrays, results):
			anarray.append(aresult)

	for (anarray, astatname) in zip(arrays, statnames):
		anarray = np.array(anarray)
		print (np.shape(anarray))
		np.savez(os.path.join(output_dir, 'indexdata_%s.npz' % astatname), specdata=anarray)

########################
def plot_fci_spectrogram(data_dir, doscaling=True, Fs=44100):
	"Composes a false-colour spectrogram plot from precalculated data. Returns the Matplotlib figure object, so you can show() it or plot it out to a file."
	import matplotlib.pyplot as plt

	false_colour_image = np.array([np.load(os.path.join(data_dir, 'indexdata_%s.npz' % statname))['specdata'] for statname in statnames])
	false_colour_image = np.transpose(false_colour_image, axes=(2,1,0))
	#print np.shape(false_colour_image)

	if doscaling:
		perc_cutoff = 10
		print (np.shape(false_colour_image))
		print (np.shape(np.percentile(false_colour_image, perc_cutoff, axis=(0,1), keepdims=True)))
		false_colour_image = (false_colour_image - np.percentile(false_colour_image, perc_cutoff, axis=(0,1), keepdims=True)) \
		                                         / np.percentile(false_colour_image, 100-perc_cutoff, axis=(0,1), keepdims=True)

	maxtime = np.shape(false_colour_image)[1] * (float(choplensecs)/60.)  # NB assumes chunking was performed using chunks of size "choplensecs", which is not always true
	#print maxtime
	timeunits = 'minutes'
	if maxtime > 60:
		maxtime /= 60.
		timeunits = "hours"
	plt.imshow(false_colour_image, aspect='auto', origin='lower', interpolation='none', extent=(0, maxtime, 0, Fs/2))
	plt.xlabel('Time (%s)' % timeunits)
	plt.ylabel('Frequency (Hz)')
	return plt.gcf()

########################
if __name__=='__main__':
	import argparse

	#default_in  = '/home/dans/birdsong/bl_dawnchorus_atmospheres/as_mono/022A-WA09020XXXXX-0916M0.flac'
	#default_in  = 'input_audio'
	default_in  = '/Users/catharinakarlsson/Desktop/Python/Audio_files/KIV_20170604_000001.wav'
	default_out = '/Users/catharinakarlsson/Desktop/Python/Output_spectrograms'

	parser = argparse.ArgumentParser()
	parser.add_argument("inpaths", nargs='*', default=default_in, help="Input path: can be a path to a single file (which will be chunked), or a folder full of wavs, or the input can be a list of wav files which you explicitly specify")
	parser.add_argument("-o", default=default_out, type=str, help="Output path: a folder (which should exist already) in which data files will be written.")
	parser.add_argument("-c", default=1, type=int, choices=[0,1], help="Whether to calculate the stats afresh. Use -c=0 to reuse previously calculated stats.")
	args = parser.parse_args()
	print (args)

	if args.c:
		calculate_and_write_index_spectrograms(infpath=args.inpaths, output_dir=args.o)

	# now plot
	ourplot = plot_fci_spectrogram(args.o)
	ourplot.show()
	input("Press a key to close")
