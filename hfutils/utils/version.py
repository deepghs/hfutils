from hbutils.testing import vpip

HF_IS_VERSION_1_X_X = (vpip('huggingface_hub') >= '1.0.0')
HF_IS_VERSION_0_X_X = (vpip('huggingface_hub') < '1.0.0')
