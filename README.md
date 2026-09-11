# AES-128-Core-Iterative：迭代式AES-128加解密核（流片）

## Golden model

`model/aes128.py` 是一个无第三方依赖的 FIPS 197 AES-128 功能参考模型，
支持加密、解密和密钥扩展。代码按 AES 轮变换顺序展开，方便初学者阅读。
该模型不描述 RTL 的时序和握手行为。

字节序约定：十六进制字符串左侧字节是 AES 的第一个字节；对应 RTL
`logic [127:0]` 时，它位于 `[127:120]`。

```bash
# FIPS 197 C.1 标准向量
python3 model/aes128.py
# ciphertext: 69c4e0d86a7b0430d8cdb78070b4c55a
# decrypted:  00112233445566778899aabbccddeeff
```

Python 代码中可使用 `encrypt_block` / `decrypt_block` 处理 16-byte 数据。

```bash
python3 -m unittest discover -s tests -v
```
