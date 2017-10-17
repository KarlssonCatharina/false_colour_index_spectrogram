import numpy as np
import matplotlib.pyplot as plt
import scipy.stats
import os
import glob

# Load index spectrograms from file
output_dir = './output_spectrograms'
aci_spec = np.load(os.path.join(output_dir,'aci_spec.npy'))
fentropy_spec = np.load(os.path.join(output_dir,'fentropy_spec.npy'))
mag_spec = np.load(os.path.join(output_dir,'mags.npy'))

# Plot histogram of ACI values
plt.subplot(311)
plt.hist(aci_spec.flatten())
plt.xlabel('ACI')
plt.ylabel('Frequency')

# Plot histogram of freq entropy values
plt.subplot(312)
plt.hist(fentropy_spec.flatten())
plt.xlabel('Frequency Entropy')
plt.ylabel('Frequency')

# Plot histogram of magnitude values
plt.subplot(313)
plt.hist(mag_spec.flatten())
plt.xlabel('Magnitude')
plt.ylabel('Frequency')

plt.show()
