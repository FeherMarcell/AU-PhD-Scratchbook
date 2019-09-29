
from hamming import hamming_encode, hamming_decode, hamming_fix_with_syndrome


def byte_to_bitlist(byte):
    # convert to a list of bits
    bitlist = [ int(i) for i in list('{0:0b}'.format(byte))]
    # pad the front with zeroes until it's length is 8
    while len(bitlist) < 8:
        bitlist.insert(0, 0)
    
    return bitlist
#

def bitlist_to_byte(bitlist):
    byte = 0
    # Reverse bitlist so we can iterate from LSB to MSB
    list_reversed = bitlist[::-1]
    for (idx, bit) in enumerate(list_reversed):
        if bit:
            # For each nonzero bit, add the current power of 2 to the result
            byte = byte + pow(2, idx)
    
    return byte
#


def gdd_hamming_compress(data):
    """
    Compress the passed list of binary numbers using GDD 
    """ 

    bases = []
    deviations = [] 

    # Hamming(7,4) operates on 7 bits at once, 
    # process the data in bytes and use the first 7 bits
    # of each byte. Carry over the last bit into the deviation.
    for byte in data:
        # Convert the next byte to binary form, a list of 0 and 1 (hamming coder expects this format)
        bitlist = byte_to_bitlist(byte)
        #print("%d -> %s" % (byte, bitlist))
        # Run a Hamming decoder on the next 7-bit section of the input data
        (base, deviation) = hamming_decode(bitlist[:7])
        #print("Base and deviation of byte %s: %s, %s" % (bitlist[:7], base, deviation) )

        # Check if the base is already known. 
        # This is the actual compression
        try:
            # Base already in bases at base_idx
            base_idx = bases.index(base)
            # Store only the index ("pointer") to the existing base
            bases.append(base_idx)
        except ValueError:
            # New base, not found in bases. 
            # Store the whole base 
            bases.append(base)

        # Carry over the last bit of the byte into the deviation
        deviation.append(bitlist[7])
        # Store the full deviation  
        deviations.append(deviation)
    # Finished processing every byte

    return (bases, deviations)
#

def gdd_hamming_decompress(bases, deviations):
    
    reconstructed_bytes = []
    for (idx, base) in enumerate(bases):
        # If the current base is a "pointer" to a full base, load it
        full_base = base if isinstance(base, list) else bases[base]
        # This deviation belongs to the current base 
        dev = deviations[idx]
        
        # Cut off the last bit, which is the carry-over last bit of the original input byte
        carryover_bit = dev[3]
        dev = dev[0:3]

        # GDD decode = Hamming encode
        bitlist = hamming_encode(full_base)
         
        # Apply the syndrome to recover the original bitlist 
        # (same process as the second half of Hamming decode)
        bitlist = hamming_fix_with_syndrome(bitlist, dev)

        # Append the carry-over bit
        bitlist.append(carryover_bit)
        #print("Reconstructed bitlist: %s" % bitlist)

        # Convert back from bitlist to byte
        current_byte = bitlist_to_byte(bitlist)
        #print("Byte: %d" % reconstructed_byte)
        reconstructed_bytes.append(current_byte)
    
    # Done reconstructing the whole data
    return bytes(reconstructed_bytes)


def readfile(filepath):
    with open(filepath, "rb") as f:
        return f.read()
#


file_contents = readfile("test_files/sample.pdf")
if not file_contents:
    raise ValueError("File too large! Please select a file that fits into the memory!")

print("File read: %d bytes" % (len(file_contents)))
#print("File contents: \n%s" % file_contents)
(bases, devs) = gdd_hamming_compress(file_contents)
print("Compression ready")

"""
# Compute the compression ratio (compressed size / orig size)
compressed_size_bits = len(deviations) * 4
for b in bases:
    if isinstance(b, list):
        # Full base
        compressed_size_bits = compressed_size_bits + len(b)
    else:
        # Pointer to an existing base
        compressed_size_bits += 0
orig_size_bits = len(data) * 8

print("Compression: %d -> %d bits, %lf percent size reduction" % (orig_size_bits, compressed_size_bits, (100-(100*compressed_size_bits/orig_size_bits))))
"""

reconstructed = gdd_hamming_decompress(bases, devs)

#print("Decompression ready")
#print("Decompressed data: \n%s" % reconstructed)

if reconstructed == file_contents:
    print("Decompression correct!")
else:
    print("ERROR!")

print("Finished.")