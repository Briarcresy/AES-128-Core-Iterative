import unittest

from model.aes128 import decrypt_block, encrypt_block, expand_key


class AES128Test(unittest.TestCase):
    key = bytes.fromhex("000102030405060708090a0b0c0d0e0f")
    plaintext = bytes.fromhex("00112233445566778899aabbccddeeff")
    ciphertext = bytes.fromhex("69c4e0d86a7b0430d8cdb78070b4c55a")

    def test_encrypt(self):
        self.assertEqual(encrypt_block(self.plaintext, self.key), self.ciphertext)

    def test_decrypt(self):
        self.assertEqual(decrypt_block(self.ciphertext, self.key), self.plaintext)

    def test_last_round_key(self):
        expected = bytes.fromhex("13111d7fe3944a17f307a78b4d2b30c5")
        self.assertEqual(expand_key(self.key)[10], expected)


if __name__ == "__main__":
    unittest.main()
