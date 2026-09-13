"""A small, readable AES-128 golden model."""

SBOX = bytes.fromhex("""
63 7c 77 7b f2 6b 6f c5 30 01 67 2b fe d7 ab 76
ca 82 c9 7d fa 59 47 f0 ad d4 a2 af 9c a4 72 c0
b7 fd 93 26 36 3f f7 cc 34 a5 e5 f1 71 d8 31 15
04 c7 23 c3 18 96 05 9a 07 12 80 e2 eb 27 b2 75
09 83 2c 1a 1b 6e 5a a0 52 3b d6 b3 29 e3 2f 84
53 d1 00 ed 20 fc b1 5b 6a cb be 39 4a 4c 58 cf
d0 ef aa fb 43 4d 33 85 45 f9 02 7f 50 3c 9f a8
51 a3 40 8f 92 9d 38 f5 bc b6 da 21 10 ff f3 d2
cd 0c 13 ec 5f 97 44 17 c4 a7 7e 3d 64 5d 19 73
60 81 4f dc 22 2a 90 88 46 ee b8 14 de 5e 0b db
e0 32 3a 0a 49 06 24 5c c2 d3 ac 62 91 95 e4 79
e7 c8 37 6d 8d d5 4e a9 6c 56 f4 ea 65 7a ae 08
ba 78 25 2e 1c a6 b4 c6 e8 dd 74 1f 4b bd 8b 8a
70 3e b5 66 48 03 f6 0e 61 35 57 b9 86 c1 1d 9e
e1 f8 98 11 69 d9 8e 94 9b 1e 87 e9 ce 55 28 df
8c a1 89 0d bf e6 42 68 41 99 2d 0f b0 54 bb 16
""")

INV_SBOX = bytearray(256)
for i in range(256):
    INV_SBOX[SBOX[i]] = i

RCON = (0x01, 0x02, 0x04, 0x08, 0x10, 0x20, 0x40, 0x80, 0x1B, 0x36)


def multiply(a, b):
    """AES finite-field multiplication."""
    result = 0
    for _ in range(8):
        if b & 1:
            result ^= a
        high_bit = a & 0x80
        a = (a << 1) & 0xFF
        if high_bit:
            a ^= 0x1B
        b >>= 1
    return result


def key_expansion(key):
    """Turn one 16-byte key into eleven round keys."""
    data = list(key)
    for round_number in range(10):
        word = data[-3:] + data[-4:-3]  # RotWord
        word = [SBOX[x] for x in word]  # SubWord
        word[0] ^= RCON[round_number]

        for byte in word:
            data.append(data[-16] ^ byte)
        for _ in range(12):
            data.append(data[-16] ^ data[-4])

    return [bytes(data[i : i + 16]) for i in range(0, 176, 16)]


def add_round_key(state, round_key):
    return bytes(state[i] ^ round_key[i] for i in range(16))


def sub_bytes(state, inverse=False):
    table = INV_SBOX if inverse else SBOX
    return bytes(table[x] for x in state)


def shift_rows(state, inverse=False):
    output = bytearray(16)
    for row in range(4):
        for column in range(4):
            shift = -row if inverse else row
            source_column = (column + shift) % 4
            output[4 * column + row] = state[4 * source_column + row]
    return bytes(output)


def mix_columns(state, inverse=False):
    if inverse:
        matrix = ((14, 11, 13, 9), (9, 14, 11, 13), (13, 9, 14, 11), (11, 13, 9, 14))
    else:
        matrix = ((2, 3, 1, 1), (1, 2, 3, 1), (1, 1, 2, 3), (3, 1, 1, 2))

    output = bytearray(16)
    for column in range(4):
        old_column = state[4 * column : 4 * column + 4]
        for row in range(4):
            for i in range(4):
                output[4 * column + row] ^= multiply(matrix[row][i], old_column[i])
    return bytes(output)


def encrypt(plaintext, key):
    """Encrypt one 16-byte block with a 16-byte key."""
    round_keys = key_expansion(key)
    state = add_round_key(plaintext, round_keys[0])

    for round_number in range(1, 10):
        state = sub_bytes(state)
        state = shift_rows(state)
        state = mix_columns(state)
        state = add_round_key(state, round_keys[round_number])

    state = sub_bytes(state)
    state = shift_rows(state)
    return add_round_key(state, round_keys[10])


def decrypt(ciphertext, key):
    """Decrypt one 16-byte block with a 16-byte key."""
    round_keys = key_expansion(key)
    state = add_round_key(ciphertext, round_keys[10])

    for round_number in range(9, 0, -1):
        state = shift_rows(state, inverse=True)
        state = sub_bytes(state, inverse=True)
        state = add_round_key(state, round_keys[round_number])
        state = mix_columns(state, inverse=True)

    state = shift_rows(state, inverse=True)
    state = sub_bytes(state, inverse=True)
    return add_round_key(state, round_keys[0])


if __name__ == "__main__":
    key = bytes.fromhex("000102030405060708090a0b0c0d0e0f")
    plaintext = bytes.fromhex("00112233445566778899aabbccddeeff")
    ciphertext = encrypt(plaintext, key)

    print("ciphertext:", ciphertext.hex())
    print("decrypted: ", decrypt(ciphertext, key).hex())
