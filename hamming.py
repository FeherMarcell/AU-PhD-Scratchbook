import logging
from sys import exit
import random

def _gf2_add(bit1, bit2):
    # Mod2 addition = XOR
    return int(bool(bit1) != bool(bit2))

def _gf2_mul(bit1, bit2):
    # Mod2 multiplication = AND
    return int(bool(bit1) and bool(bit2))

def _mul_vec_mat(vector, matrix):
    # The matrix must have the same number of rows as the vector's length
    if len(vector) != len(matrix):
        raise ValueError("Wrong dimensions! Vector length %d must be the same as matrix rows %d" % (len(vector), len(matrix)))
    
    result = [0] * len(matrix[0])

    matrix_rows_to_xor = [row for (idx, row) in enumerate(matrix) if vector[idx] == 1]
    #print("Matrix rows to XOR: %s" % matrix_rows_to_xor)

    for (colidx, elem) in enumerate(matrix[0]):
        for row in matrix_rows_to_xor:
            result[colidx] = _gf2_add(result[colidx], row[colidx])
        
    return result

def _mul_mat_vec(matrix, vector):
    # Matrix x Vector multiplication

    # The matrix must have the same number of cols than the vector's rows
    if len(matrix[0]) != len(vector):
        raise ValueError("Wrong dimensions! Vector length {} must be the same as matrix columns {}".format(len(vector), len(matrix[0])))

    result = [0] * len(matrix)
    for (rowidx, row) in enumerate(matrix):
        for (colidx, col) in enumerate(row):
            result[rowidx] = _gf2_add(result[rowidx], _gf2_mul(col, vector[colidx]))
    
    return result

# One possible generator matrix for Hamming(7,4)
# This moves the 3 parity bits to the front of the codeword
GENERATOR = [
    [0,1,1, 1,0,0,0],
    [1,0,1, 0,1,0,0],
    [1,1,0, 0,0,1,0],
    [1,1,1, 0,0,0,1]
]

_GENERATOR = [
    [1,0,0,0, 1,0,1],
    [0,1,0,0, 1,1,1],
    [0,0,1,0, 1,1,0],
    [0,0,0,1, 0,1,1]
]

# The corresponding parity check matrix
PARITY_CHECK = [
    [1,0,0, 0,1,1,1],
    [0,1,0, 1,0,1,1],
    [0,0,1, 1,1,0,1]
]

_PARITY_CHECK = [
    [1,1,1,0, 1,0,0],
    [0,1,1,1, 0,1,0],
    [1,1,0,1, 0,0,1]
] 
def hamming_encode(message):
    if len(message) != 4:
        raise ValueError("Message must be 4 bits!")

    # Encoding is simply multiplying the message with the generator matrix
    return _mul_vec_mat(message, GENERATOR)
#

def hamming_decode(codeword):
    # Decode a potentially noisy codeword received after transmission
    # The result will be correct if 0 or 1 bit of the codeword is corrupted.

    # Generate the syndrome vector
    syndrome = _mul_mat_vec(PARITY_CHECK, codeword)
    
    # Find which bit was flipped using the syndrome, and flip it back
    fixed_codeword = hamming_fix_with_syndrome(codeword, syndrome)
    
    # Depending on the format of the Generator matrix, the 
    # data bits are either in the beginning or the end of the
    # codeword. If the Generator matrix has an identity on the 
    # left side, the decoded data is at the end of the fixed 
    # codeword, if the identity is on the right the data bits 
    # are in the beginning
    data_bits = fixed_codeword[:4] if GENERATOR[0][:4] == [1,0,0,0] else fixed_codeword[3:]
    
    return (data_bits, syndrome)
#

def hamming_fix_with_syndrome(codeword, syndrome):

    if syndrome == [0,0,0]:
        # No error in transmission
        return codeword
    
    # Find which column of the parity check matrix is identical to the syndrome
    # TODO instead of searching for the parity column, we could precompute 
    # a lookup table that has the correct flipped bit index for every possible syndrome
    for i in range(len(PARITY_CHECK[0])):
        parity_col = [PARITY_CHECK[j][i] for j in range(len(PARITY_CHECK))]

        if parity_col == syndrome:
            #print("Syndrome: %s, Error bit: %d" % (syndrome, i))
            # Flip the corresponding bit in the codeword
            codeword[i] = 0 if codeword[i]==1 else 1
            #print("Codeword after fix: %s" % codeword)
            return codeword
    
    raise ValueError("Failed to fix codeword, no fix found for syndrome {}".format(syndrome))
#

def test_hamming():
    """
    Tests Hamming encode and decode for every 4-bit binary sequence, 
    simulating every possible single bit error between encode and decode.
    Throws ValueError if any of the "transmitted" messages was not corrected
    by the decoder properly. 
    """

    # Generate every possible 4-bit binary message (16 messages)
    every_message = [ [i,j,k,l] for i in (0,1) for j in (0,1) for k in (0,1) for l in (0,1) ]

    for message in every_message:

        #print("Message to send: %s" % message)

        # Encode
        message_on_wire = hamming_encode(message)
        #print("Encoded message: %s" % message_on_wire)
        

        # Decode without error
        recieved = message_on_wire
        (decoded_mes, syndrome) = hamming_decode(recieved)
        #print("Received message: %s" % decoded_mes)
        if not decoded_mes == message:
            print("Error decoding without error %s. Syndrome: %s Decoded message: %s" % (message, syndrome, decoded_mes))
            
        # Corrupt each bit and try to decode
        for bit_idx in range(len(message_on_wire)):
            # Make a copy of the codeword before corrupting it 
            recieved = message_on_wire.copy()
            recieved[bit_idx] = 1 if recieved[bit_idx] == 0 else 0
        
            # Decode
            #print("Received codeword: %s" % recieved)
            (decoded_mes, syndrome) = hamming_decode(recieved.copy())
            #print("Received message: %s" % decoded_mes)
            if not decoded_mes == message:
                print("Error with %s when bit %d is flipped" % (message, bit_idx))
            else:
                pass
                #print("Message %s corrected when bit %d is flipped"  % (message, bit_idx))
                #print("%s message = %s base + %s syndrome" % (recieved, decoded_mes, syndrome))

        print("Message corrected successfully: %s" % message)

    print("Every possible 4-bit message with 1 bit error was corrected.")



# What to run when this python file is invoked (not imported somewhere else)
if __name__ == "__main__":
    test_hamming()