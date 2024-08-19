"""
This module provides functionality for identifying model files based on their extensions and naming patterns.

It includes a comprehensive list of model file extensions, patterns for sharded model files, and specific patterns
for Hugging Face model files. The main function, :func:`is_model_file`, determines whether a given filename corresponds
to a model file based on these predefined patterns and extensions.

This module can be useful in various scenarios, such as:

- Automated model file detection in directories
- Validation of uploaded files in machine learning platforms
- Preprocessing steps in model loading pipelines

Usage:
    .. code:: python

        from model_file_identifier import is_model_file

        filename = "model.pt"
        if is_model_file(filename):
            print(f"{filename} is a model file")
        else:
            print(f"{filename} is not a model file")
"""

import os
import re
from typing import Union

_MODEL_EXTS = {
    '.ckpt',  # Checkpoint file
    '.pt',  # PyTorch model file
    '.pth',  # PyTorch model file (alternative extension)
    '.safetensors',  # SafeTensors model file
    '.onnx',  # Open Neural Network Exchange model file
    '.model',  # Generic model file
    '.h5',  # Hierarchical Data Format version 5
    '.hdf5',  # Hierarchical Data Format version 5 (alternative extension)
    '.mlmodel',  # Core ML model file
    '.ftz',  # FastText model file
    '.pb',  # Protocol Buffer file (often used for TensorFlow models)
    '.tflite',  # TensorFlow Lite model file
    '.pkl',  # Pickle file (often used for scikit-learn models)
    '.joblib',  # Joblib file (often used for scikit-learn models)
    '.bin',  # Binary file (generic)
    '.meta',  # Meta file (often associated with TensorFlow checkpoints)
    '.params',  # Parameters file (often used in MXNet)
    '.pdparams',  # PaddlePaddle parameters file
    '.pdmodel',  # PaddlePaddle model file
    '.ot',  # OpenVINO model file
    '.nnet',  # Neural network file
    '.dnn',  # Deep neural network file
    '.mar',  # MXNet Archive
    '.tf',  # TensorFlow SavedModel file
    '.keras',  # Keras model file
    '.weights',  # Weights file (generic)
    '.pmml',  # Predictive Model Markup Language file
    '.gguf',  # GGUF (GPT-Generated Unified Format) file
    '.ggml',  # GGML (GPT-Generated Model Language) file
    '.q4_0',  # 4-bit quantized model (type 0)
    '.q4_1',  # 4-bit quantized model (type 1)
    '.q5_0',  # 5-bit quantized model (type 0)
    '.q5_1',  # 5-bit quantized model (type 1)
    '.q8_0',  # 8-bit quantized model
    '.qnt',  # Quantized model (generic)
    '.int8',  # 8-bit integer quantized model
    '.fp16',  # 16-bit floating point model
    '.bk',  # Backup file (often used for model checkpoints)
    '.engine',  # TensorRT engine file
    '.plan',  # TensorRT plan file
    '.trt',  # TensorRT model file
    '.torchscript',  # TorchScript model file
    '.pdiparams',  # PaddlePaddle inference parameters file
    '.pdopt',  # PaddlePaddle optimizer file
    '.nb',  # Neural network binary file
    '.mnn',  # MNN (Mobile Neural Network) model file
    '.ncnn',  # NCNN model file
    '.om',  # CANN (Compute Architecture for Neural Networks) offline model
    '.rknn',  # Rockchip Neural Network model file
    '.xmodel',  # Vitis AI model file
    '.kmodel',  # Kendryte model file
}

_MODEL_SHARD_PATTERNS = [
    r'.*-\d{5}-of-\d{5}',  # Pattern for sharded files like "model-00001-of-00005"
    r'.*\.bin\.\d+',  # Pattern for binary shards like "model.bin.1"
    r'.*\.part\.\d+',  # Pattern for part files like "model.part.0"
    r'.*_part_\d+',  # Alternative pattern for part files like "model_part_0"
    r'.*-shard\d+',  # Pattern for shard files like "model-shard1"
]

_HF_MODEL_PATTERNS = [
    r'pytorch_model.*\.bin',  # Hugging Face PyTorch model file
    r'tf_model.*\.h5',  # Hugging Face TensorFlow model file
    r'model.*\.ckpt',  # Hugging Face checkpoint file
    r'flax_model.*\.msgpack',  # Hugging Face Flax model file
    r'.*\.safetensors',  # SafeTensors file (often used in Hugging Face models)
]


def is_model_file(filename: Union[str, os.PathLike]) -> bool:
    """
    Determine if a given filename corresponds to a model file.

    This function checks if the provided filename matches any of the known model file extensions
    or patterns, including sharded model files and Hugging Face specific patterns.

    :param filename: The name of the file to check. Can be a full path or just the filename.
    :type filename: Union[str, os.PathLike]

    :return: True if the filename corresponds to a model file, False otherwise.
    :rtype: bool

    :raises TypeError: If the filename is not a string or os.PathLike object.

    Usage:
        >>> is_model_file("model.pt")
        True
        >>> is_model_file("data.csv")
        False
        >>> is_model_file("model-00001-of-00005")
        True
        >>> is_model_file("pytorch_model.bin")
        True

    .. note::
        This function is case-insensitive and works with both file names and full paths.
    """
    if not isinstance(filename, (str, os.PathLike)):
        raise TypeError(f'Unknown file name type - {filename!r}')
    filename = os.path.basename(os.path.normcase(str(filename)))

    if any(filename.lower().endswith(ext) for ext in _MODEL_EXTS):
        return True
    if any(re.match(pattern, filename.lower()) for pattern in _MODEL_SHARD_PATTERNS):
        return True
    if any(re.match(pattern, filename.lower()) for pattern in _HF_MODEL_PATTERNS):
        return True

    return False
