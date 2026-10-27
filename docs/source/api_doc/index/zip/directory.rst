hfutils.index.zip.directory
========================================================

.. currentmodule:: hfutils.index.zip.directory

.. automodule:: hfutils.index.zip.directory


ZipEntry
-----------------------------------------------------

.. autoclass:: ZipEntry
    :members: encrypted,strong,raw_name,name,path,flags,method,stored_method,csize,size,crc,offset,disk,dos_time,dos_date,extra,aes,is_dir


ZipDirectory
-----------------------------------------------------

.. autoclass:: ZipDirectory
    :members: entries,files,encoding,comment,source,volumes,tail_start,notes


classify\_non\_zip
-----------------------------------------------------

.. autofunction:: classify_non_zip


not\_a\_zip
-----------------------------------------------------

.. autofunction:: not_a_zip


find\_eocd
-----------------------------------------------------

.. autofunction:: find_eocd


build\_directory
-----------------------------------------------------

.. autofunction:: build_directory


raw\_volume\_name
-----------------------------------------------------

.. autofunction:: raw_volume_name


open\_zip
-----------------------------------------------------

.. autofunction:: open_zip
