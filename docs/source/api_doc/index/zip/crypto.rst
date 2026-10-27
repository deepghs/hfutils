hfutils.index.zip.crypto
========================================================

.. currentmodule:: hfutils.index.zip.crypto

.. automodule:: hfutils.index.zip.crypto


AES\_KEY\_BITS
-----------------------------------------------------

.. autodata:: AES_KEY_BITS


ZipCryptoKeys
-----------------------------------------------------

.. autoclass:: ZipCryptoKeys
    :members: __init__,update,decrypt


ZipCryptoDecryptor
-----------------------------------------------------

.. autoclass:: ZipCryptoDecryptor
    :members: __init__,feed,finish,header_matches


AesDecryptor
-----------------------------------------------------

.. autoclass:: AesDecryptor
    :members: __init__,feed,finish


zipcrypto\_check\_byte
-----------------------------------------------------

.. autofunction:: zipcrypto_check_byte


parse\_aes\_extra
-----------------------------------------------------

.. autofunction:: parse_aes_extra


aes\_derive
-----------------------------------------------------

.. autofunction:: aes_derive


aes\_verifier\_matches
-----------------------------------------------------

.. autofunction:: aes_verifier_matches
