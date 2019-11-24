# Image Steganography

Image Steganography using the LSB method with a layer of Symmetric Encryption

#### Requirements:
Python 3.7

All modules in requirement.txt

### Usage:

###### Embedding:

`python cryptsteg -emb <path to carrier file> <path to embed file> <(optional)output path>`

###### Extracting:

`python cryptsteg -ext <path to carrier file> <embedded data format> <(optional)output path>`

### Note:

When an image a embedded a **key file** is generated which contains the **decryption key**.
This key is required for decrypting the data after extracting.
The key will be in the same directory as the output image

If an output path is **not** specified then the **current directory** of the script will be used as the **output directory**

When specifying the **embedded data format** while extracting, **do not specify '.'**

For Example:

**Correct** :  png

**Incorrect** :  **.** png
