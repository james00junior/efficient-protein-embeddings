#!/usr/bin/env python
# coding: utf-8

# #ML Hands-on Challenge - Getting started
# 
# The goal of this notebook is to explore the data that we have provided from the ML hands-on challenge. You will learn more about the CATH labels, how to visualize the protein structure, and challenges you will have to handle (e.g. gaps in structure).
# 
# We are grouping at the CATH architecture level as this is the level that your models will be classifying the protein domains.
# 
# There are 10 CATH architectures that the protein domains can be classified into, and we will explore examples from each architecture.
# 

# In[17]:


import pandas as pd
import numpy as np
import sys
import glob
import os
import Bio.PDB.PDBParser
import py3Dmol
import warnings

warnings.filterwarnings("ignore", message="Used element '.' for Atom")

architecture_names = {(1, 10): "Mainly Alpha: Orthogonal Bundle",
                      (1, 20): "Mainly Alpha: Up-down Bundle",
                      (2, 30): "Mainly Beta: Roll",
                      (2, 40): "Mainly Beta: Beta Barrel",
                      (2, 60): "Mainly Beta: Sandwich",
                      (3, 10): "Alpha Beta: Roll",
                      (3, 20): "Alpha Beta: Alpha-Beta Barrel",
                      (3, 30): "Alpha Beta: 2-Layer Sandwich",
                      (3, 40): "Alpha Beta: 3-Layer(aba) Sandwich",
                      (3, 90): "Alpha Beta: Alpha-Beta Complex"}

# Open the training data sequences and structure
data = pd.read_csv('cath_w_seqs_share.csv', index_col=0)
data

# The CATH classification for a protein can be determined by concatenating the columns
example_cath_id = data['cath_id'][0]
example_class = data['class'][0]
example_arch = f"({example_class},{data['architecture'][0]})"
example_topo = f"({example_class},{data['architecture'][0]},{data['topology'][0]})"
example_superfam = f"({example_class},{data['architecture'][0]},{data['topology'][0]},{data['superfamily'][0]})"


print(f"""
Protein domain with cath id {example_cath_id} is in class {example_class}, \
architecture {example_arch}, topology {example_topo}, and superfamily {example_superfam}.
""")


# The sequences come from the PDB files
from Bio.PDB.Polypeptide import protein_letters_3to1

def get_sequence_from_pdb(pdb_filename):
    pdb_parser = Bio.PDB.PDBParser()
    structure = pdb_parser.get_structure(pdb_filename, pdb_filename)
    assert len(structure) == 1

    seq = []

    for model in structure:
        for chain in model:
            for residue in chain:
                if residue.get_id()[0] == " ":  # This checks if it's a standard residue
                    seq.append(protein_letters_3to1[residue.get_resname()])
                else:
                    print('nonstandard', residue.get_id())

    return ''.join(seq)

example_seq = get_sequence_from_pdb(f"pdb_share/{example_cath_id}")
print(f"The sequence for cath id {example_cath_id} is {example_seq}")

# Check that it matches the data file
data['sequences'][0] == example_seq

# Load sequence and structure for one example for each architecture
cath_examples = data.groupby(['class', 'architecture'])[['cath_id','sequences']].first()
cath_examples


def view_structure(pdb_filename, name, gaps=[], width=300, height=300):
  pdb_parser = Bio.PDB.PDBParser()
  structure = pdb_parser.get_structure(pdb_filename, pdb_filename)

  # Add the model and set the cartoon style
  viewer = py3Dmol.view(query=f'arch: {name}, pdb: {pdb_filename}', width=width, height=height)
  viewer.addModel(open(pdb_filename, 'r').read(), 'pdb')
  viewer.setStyle({'cartoon': {'color': 'spectrum'}})

  if gaps:
    # Add dashed lines for gaps
    for chain_id, start_res, end_res in gaps:
        try:
            start_residue = structure[0][chain_id][start_res-1]
            end_residue = structure[0][chain_id][end_res]

            # Get coordinates and convert to Python float
            start_coords = [float(coord) for coord in start_residue['CA'].get_coord()]
            end_coords = [float(coord) for coord in end_residue['CA'].get_coord()]

            # Add dashed cylinders for missing residues
            viewer.addCylinder({'start': {'x': start_coords[0], 'y': start_coords[1], 'z': start_coords[2]},
                                'end': {'x': end_coords[0], 'y': end_coords[1], 'z': end_coords[2]},
                                'radius': 0.1, 'color': 'red', 'dashed': True, 'fromCap': 1, 'toCap': 1})
        except KeyError:
          print(f"Residue {start_res} or {end_res} in chain {chain_id} not found.")

  viewer.zoomTo()
  return viewer




import py3Dmol
from IPython.display import display, HTML

pdb_dir = 'pdb_share'
num_columns = [2, 3, 5]  # Number of columns in the grid
# titles = ['Structure 1', 'Structure 2', 'Structure 3', 'Structure 4']

# Creating HTML table for the grid
html = '<table><tr>'
print_col = 0
for i, (arch, row) in enumerate(cath_examples.iterrows()):
    cath_id = row[0]
    pdb_filename = os.path.join(pdb_dir, cath_id)

    if (i-sum(num_columns[:print_col])) % num_columns[print_col] == 0 and i > 0:
        print_col += 1
        html += '</tr><tr>'
    viewer_html = view_structure(pdb_filename, arch)._make_html()
    html += f'<td><div style="text-align: center;"><strong>{arch} {architecture_names[arch]}</strong></div>{viewer_html}</td>'
html += '</tr></table>'

# Display the grid
display(HTML(html))


# Indices of the cath domain associated with the cath_id in the full protein
# that can be found using the pdb id in the PDB online.

example_cath_ids = ['3zq4C03', '3i9v600']
data[data['cath_id'].isin(example_cath_ids)]



# If you compare the indices that in the cath_indices range and not in the PDB file
# residue indices, for these examples you will get this

example_gaps = {'3zq4C03': [('C', 493, 501)],
                '3i9v600': [('6', 58, 74)]}


# We can visualize the gaps are red lines
import py3Dmol
from IPython.display import display, HTML

# Creating HTML table for the grid
html = '<table><tr>'
for cath_id, gap in example_gaps.items():
  viewer_html = view_structure(f'pdb_share/{cath_id}', cath_id, gaps=gap)._make_html()
  html += f'<td><div style="text-align: center;"><strong>{cath_id}</strong></div>{viewer_html}</td>'
html += '</tr></table>'

# Display the grid
display(HTML(html))




# In[19]:


data['sequences']


# In[21]:


# Check for NaN values in the 'sequences' column
nan_indices = data['sequences'].index[data['sequences'].apply(pd.isna)]

# Remove non-standard residues and handle NaN values
def preprocess_sequence(seq):
    if pd.isna(seq):
        return ''
    return ''.join([aa for aa in seq if aa in protein_letters_3to1.values()])

# Apply the preprocessing function to the 'sequences' column
data['sequences'] = data['sequences'].apply(preprocess_sequence)


# In[23]:


nan_indices


# In[24]:


# Convert sequences to numerical format using one-hot encoding
from sklearn.preprocessing import OneHotEncoder

# Create a mapping from amino acid to index
aa_to_index = {aa: i for i, aa in enumerate(protein_letters_3to1.values())}

# Convert sequences to numerical format
def sequence_to_onehot(sequence):
    return np.array([[1 if aa == aa_to_index[acid] else 0 for acid in protein_letters_3to1.values()] for aa in sequence])

data['sequences_onehot'] = data['sequences'].apply(sequence_to_onehot)


# In[27]:


import matplotlib.pyplot as plt

# 2. Data Exploration and Visualization

# Explore class distribution
class_distribution = data['class'].value_counts()
print("Class Distribution:\n", class_distribution)

# Plot a bar graph of the class distribution
plt.figure(figsize=(10, 6))
class_distribution.plot(kind='bar', color='skyblue')
plt.title('Class Distribution')
plt.xlabel('CATH Class')
plt.ylabel('Count')
plt.show()

# Visualize protein structures for a few examples
pdb_dir = 'pdb_share'
for i, (arch, row) in enumerate(cath_examples.iterrows()):
    cath_id = row[0]
    pdb_filename = os.path.join(pdb_dir, cath_id)
    viewer = view_structure(pdb_filename, arch)
    viewer.show()


# In[35]:


# 3. Model Development - Recurrent Neural Network (RNN)

from sklearn.model_selection import train_test_split
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Embedding
from tensorflow.keras.preprocessing.sequence import pad_sequences

# Calculate the maximum sequence length
max_sequence_length = max(len(seq) for seq in data['sequences_onehot'])


# Assuming a fixed sequence length, adjust as needed
fixed_sequence_length = max_sequence_length 

# Pad sequences using Keras pad_sequences
padded_sequences = pad_sequences(data['sequences_onehot'].tolist(), maxlen=max_sequence_length, padding='post')

# Pad sequences to the maximum length
#padded_sequences = np.array([np.pad(seq, ((0, max_sequence_length - len(seq)), (0, 0)), 'constant') for seq in data['sequences_onehot']])


# In[36]:


max_sequence_length


# In[38]:


padded_sequences[0]


# In[40]:


from sklearn.preprocessing import LabelEncoder
from tensorflow.keras.utils import to_categorical

# Split the data into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(padded_sequences, data['class'], test_size=0.2, random_state=42)

# Encode the class labels
label_encoder = LabelEncoder()
y_train_encoded = label_encoder.fit_transform(y_train)
y_test_encoded = label_encoder.transform(y_test)

# Convert class labels to one-hot encoding
y_train_onehot = to_categorical(y_train_encoded)
y_test_onehot = to_categorical(y_test_encoded)

# Build the RNN model for multi-class classification
model = Sequential()
model.add(LSTM(64, input_shape=(max_sequence_length, len(protein_letters_3to1)), activation='relu'))
model.add(Dense(3, activation='softmax'))  # Assuming 3 classes; adjust based on your actual number of classes

# Compile the model
model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])

# Train the model
model.fit(X_train, y_train_onehot, epochs=10, batch_size=32, validation_split=0.2)

# Evaluate the model on the test set
accuracy = model.evaluate(X_test, y_test_onehot)[1]
print(f"Test Accuracy: {accuracy}")


# In[41]:


from tensorflow.keras.layers import LSTM, Dense, BatchNormalization, Dropout, Conv1D, MaxPooling1D, Flatten
from tensorflow.keras.utils import to_categorical


# In[42]:


from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, BatchNormalization, Dropout, Conv1D, MaxPooling1D, Flatten
from tensorflow.keras.utils import to_categorical

# Assuming 'padded_sequences' is a 3D array with shape (num_samples, max_sequence_length, num_features)

# Split the data into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(padded_sequences, data['class'], test_size=0.2, random_state=42)

# Encode the class labels
label_encoder = LabelEncoder()
y_train_encoded = label_encoder.fit_transform(y_train)
y_test_encoded = label_encoder.transform(y_test)

# Convert class labels to one-hot encoding
y_train_onehot = to_categorical(y_train_encoded)
y_test_onehot = to_categorical(y_test_encoded)

# Build the RNN model for multi-class classification with CNN layers
model = Sequential()

# Add three 1D Convolutional layers with Batch Normalization and Dropout
model.add(Conv1D(32, kernel_size=3, activation='relu', input_shape=(max_sequence_length, len(protein_letters_3to1))))
model.add(BatchNormalization())
model.add(Dropout(0.5))

model.add(Conv1D(64, kernel_size=3, activation='relu'))
model.add(BatchNormalization())
model.add(Dropout(0.5))

model.add(Conv1D(128, kernel_size=3, activation='relu'))
model.add(BatchNormalization())
model.add(Dropout(0.5))

# Add LSTM layer
model.add(LSTM(64, activation='relu'))

# Flatten before Dense layers
model.add(Flatten())

# Fully connected Dense layer
model.add(Dense(128, activation='relu'))
model.add(BatchNormalization())
model.add(Dropout(0.5))

# Output layer
model.add(Dense(3, activation='softmax'))  # Assuming 3 classes; adjust based on your actual number of classes

# Compile the model
model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])

# Train the model
model.fit(X_train, y_train_onehot, epochs=10, batch_size=32, validation_split=0.2)

# Evaluate the model on the test set
accuracy = model.evaluate(X_test, y_test_onehot)[1]
print(f"Test Accuracy: {accuracy}")


# In[ ]:




