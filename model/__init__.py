"""AES-128 golden model."""

from .aes128 import decrypt_block, encrypt_block, expand_key

__all__ = ["encrypt_block", "decrypt_block", "expand_key"]
