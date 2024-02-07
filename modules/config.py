import os
import json
import math
import numbers
import args_manager
import modules.flags
import modules.sdxl_styles

from modules.model_loader import load_file_from_url
from modules.util import get_files_from_folder
from modules.model_previewer import cleanup as cleanup_model_previews

config_path = os.path.abspath("./config.txt")
config_example_path = os.path.abspath("config_modification_tutorial.txt")
config_dict = {}
always_save_keys = []
visited_keys = []

try:
    with open(os.path.abspath(f'./presets/default.json'), "r", encoding="utf-8") as json_file:
        config_dict.update(json.load(json_file))
except Exception as e:
    print(f'Load default preset failed.')
    print(e)

try:
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as json_file:
            config_dict.update(json.load(json_file))
            always_save_keys = list(config_dict.keys())
except Exception as e:
    print(f'Failed to load config file "{config_path}" . The reason is: {str(e)}')
    print('Please make sure that:')
    print(f'1. The file "{config_path}" is a valid text file, and you have access to read it.')
    print('2. Use "\\\\" instead of "\\" when describing paths.')
    print('3. There is no "," before the last "}".')
    print('4. All key/value formats are correct.')

def try_load_deprecated_user_path_config():
    global config_dict

    if not os.path.exists('user_path_config.txt'):
        return

    try:
        deprecated_config_dict = json.load(open('user_path_config.txt', "r", encoding="utf-8"))

        def replace_config(old_key, new_key):
            if old_key in deprecated_config_dict:
                config_dict[new_key] = deprecated_config_dict[old_key]
                del deprecated_config_dict[old_key]

        replace_config('modelfile_path', 'path_checkpoints')
        replace_config('lorafile_path', 'path_loras')
        replace_config('embeddings_path', 'path_embeddings')
        replace_config('vae_approx_path', 'path_vae_approx')
        replace_config('upscale_models_path', 'path_upscale_models')
        replace_config('inpaint_models_path', 'path_inpaint')
        replace_config('controlnet_models_path', 'path_controlnet')
        replace_config('clip_vision_models_path', 'path_clip_vision')
        replace_config('fooocus_expansion_path', 'path_fooocus_expansion')
        replace_config('temp_outputs_path', 'path_outputs')

        if deprecated_config_dict.get("default_model", None) == 'juggernautXL_version6Rundiffusion.safetensors':
            os.replace('user_path_config.txt', 'user_path_config-deprecated.txt')
            print('Config updated successfully in silence. '
                  'A backup of previous config is written to "user_path_config-deprecated.txt".')
            return

        if input("Newer models and configs are available. "
                 "Download and update files? [Y/n]:") in ['n', 'N', 'No', 'no', 'NO']:
            config_dict.update(deprecated_config_dict)
            print('Loading using deprecated old models and deprecated old configs.')
            return
        else:
            os.replace('user_path_config.txt', 'user_path_config-deprecated.txt')
            print('Config updated successfully by user. '
                  'A backup of previous config is written to "user_path_config-deprecated.txt".')
            return
    except Exception as e:
        print('Processing deprecated config failed')
        print(e)
    return


try_load_deprecated_user_path_config()

preset = args_manager.args.preset

                
if isinstance(preset, str):
    preset_path = os.path.abspath(f'./presets/{preset}.json')
    try:
        if os.path.exists(preset_path):
            with open(preset_path, "r", encoding="utf-8-sig") as json_file:
                config_dict.update(json.load(json_file))
            print(f'Loaded preset: {preset_path}')
        else:
            raise FileNotFoundError
    except Exception as e:
        print(f'Load preset [{preset_path}] failed')
        print(e)


def get_dir_or_set_default(key, default_value):
    global config_dict, visited_keys, always_save_keys

    if key not in visited_keys:
        visited_keys.append(key)

    if key not in always_save_keys:
        always_save_keys.append(key)

    v = config_dict.get(key, None)
    if isinstance(v, str) and os.path.exists(v) and os.path.isdir(v):
        return v
    else:
        if v is not None:
            print(f'Failed to load config key: {json.dumps({key:v})} is invalid or does not exist; will use {json.dumps({key:default_value})} instead.')
        dp = os.path.abspath(os.path.join(os.path.dirname(__file__), default_value))
        os.makedirs(dp, exist_ok=True)
        config_dict[key] = dp
        return dp


path_checkpoints = get_dir_or_set_default('path_checkpoints', '../models/checkpoints/')
path_loras = get_dir_or_set_default('path_loras', '../models/loras/')
path_embeddings = get_dir_or_set_default('path_embeddings', '../models/embeddings/')
path_vae_approx = get_dir_or_set_default('path_vae_approx', '../models/vae_approx/')
path_upscale_models = get_dir_or_set_default('path_upscale_models', '../models/upscale_models/')
path_inpaint = get_dir_or_set_default('path_inpaint', '../models/inpaint/')
path_controlnet = get_dir_or_set_default('path_controlnet', '../models/controlnet/')
path_clip_vision = get_dir_or_set_default('path_clip_vision', '../models/clip_vision/')
path_fooocus_expansion = get_dir_or_set_default('path_fooocus_expansion', '../models/prompt_expansion/fooocus_expansion')
path_outputs = get_dir_or_set_default('path_outputs', '../outputs/')


def get_config_item_or_set_default(key, default_value, validator, disable_empty_as_none=False, corrector=None):
    global config_dict, visited_keys

    debug_mode=False
    if debug_mode:
        print(f"Checking key: {key}")

    if key not in visited_keys:
        visited_keys.append(key)
    
    v = config_dict.get(key, None)
    if debug_mode:
        print(f"Value for key {key}: {v}")

    if not disable_empty_as_none:
        if v is None or v == '':
            v = default_value
            if debug_mode:
                print(f"Value for key {key} is None or empty, setting to default: {v}")

    if validator(v):
        if debug_mode:
            print(f"Value for key {key} passed validation.")
    elif corrector:
        corrected_v = corrector(v)
        if validator(corrected_v):
            if debug_mode:
                print(f"Value for key {key} passed validation after correction.")
            v = corrected_v
        else:
            print(f"Failed to load config key after correction. Using default: {default_value}")
            v = default_value
    else:
        print(f"Failed to load config key: {json.dumps({key: v})} is invalid. Using default: {default_value}")
        v = default_value

    config_dict[key] = v
    return v

def get_model_filenames(folder_path, name_filter=None):
    return get_files_from_folder(folder_path, ['.pth', '.ckpt', '.bin', '.safetensors', '.fooocus.patch'], name_filter)

def update_all_model_names():
    global model_filenames, lora_filenames
    model_filenames = get_model_filenames(path_checkpoints)
    lora_filenames = get_model_filenames(path_loras)
    return

model_filenames = []
lora_filenames = []
update_all_model_names()

def model_validator(value):
    if isinstance(value, str) and (value == "" or value in model_filenames):
        return True
    else :
        print(f"model_filenames: {model_filenames}")  # Debug print
        print(f"failed model_validator: {value}")  # Debug printà
        return False

def correct_case_sensitivity(value, valid_values):
    """Corrects case sensitivity of a value or list of values based on a list of valid values.
       If a valid value is contained in the input value, it replaces it with the full valid value."""
    def find_full_match(partial_value):
        if isinstance(partial_value, str):
            lower_partial_value = partial_value.lower()
            for valid_value in valid_values:
                if lower_partial_value == valid_value.lower():
                    return valid_value
                elif lower_partial_value in valid_value.lower():
                    return valid_value
        return partial_value

    print(f"Initial value: {value}")  # Debug print

    # If value is a string, apply find_full_match directly
    if isinstance(value, str):
        corrected_value = find_full_match(value)
        print(f"Corrected string value: {corrected_value}")  # Debug print
        return corrected_value
    
    # If value is a list
    elif isinstance(value, list):
        print(f"Processing list value: {value}")  # Debug print before if cases

        # Check if value is a list of lists (as in default_loras)
        if all(isinstance(item, list) and len(item) == 2 for item in value):
            corrected_list = []
            for sub_value in value:
                print(f"Processing sub_value: {sub_value}")  # Debug print
                if isinstance(sub_value, list):
                    corrected_element = find_full_match(sub_value[0])
                    print(f"Correcting {sub_value[0]} to {corrected_element}")  # Debug print
                    corrected_list.append([corrected_element, sub_value[1]])
                else:
                    corrected_list.append(sub_value)
            print(f"Corrected list of lists: {corrected_list}")  # Debug print
            return corrected_list

        # If value is a regular list
        else:
            corrected_list = [find_full_match(val) for val in value]
            print(f"Corrected regular list: {corrected_list}")  # Debug print
            return corrected_list

    return value



def model_corrector(value):
    return correct_case_sensitivity(value, model_filenames)

default_base_model_name = get_config_item_or_set_default(
    key='default_model',
    default_value='model.safetensors',
    validator=model_validator,
    corrector=model_corrector
)
previous_default_models = get_config_item_or_set_default(
    key='previous_default_models',
    default_value=[],
    validator=lambda x: isinstance(x, list) and all(isinstance(k, str) for k in x)
)
default_refiner_model_name = get_config_item_or_set_default(
    key='default_refiner',
    default_value='None',
    validator=model_validator,
    corrector=model_corrector
)
default_refiner_switch = get_config_item_or_set_default(
    key='default_refiner_switch',
    default_value=0.8,
    validator=lambda x: isinstance(x, numbers.Number) and 0 <= x <= 1
)
default_loras_min_weight = get_config_item_or_set_default(
    key='default_loras_min_weight',
    default_value=-2,
    validator=lambda x: isinstance(x, numbers.Number) and -10 <= x <= 10
)
default_loras_max_weight = get_config_item_or_set_default(
    key='default_loras_max_weight',
    default_value=2,
    validator=lambda x: isinstance(x, numbers.Number) and -10 <= x <= 10
)

def loras_validator(x):
    if not isinstance(x, list):
        print(f"Validation failed: 'x' is not a list. Value of x: {x}")  # Debug print
        return False

    for y in x:
        if not (len(y) == 2 and isinstance(y[0], str) and isinstance(y[1], (numbers.Number, float))):
            print(f"Validation failed: Element structure is incorrect. Element: {y}")  # Debug print
            return False
        if y[0] != "None" and y[0] not in lora_filenames:
            print(f"Validation failed: Lora filename not found in lora_filenames. Lora filename: {y[0]}")  # Debug print
            print(f"Available lora_filenames: {lora_filenames}")  # Debug print
            return False

    return True

def loras_corrector(value):
    return correct_case_sensitivity(value, lora_filenames)

default_loras = get_config_item_or_set_default(
    key='default_loras',
    default_value=[
        [
            "sd_xl_offset_example-lora_1.0.safetensors",
            0.1
        ],
        [
            "None",
            1.0
        ],
        [
            "None",
            1.0
        ],
        [
            "None",
            1.0
        ],
        [
            "None",
            1.0
        ]
    ],
    validator=lambda x: isinstance(x, list) and all(len(y) == 2 and isinstance(y[0], str) and isinstance(y[1], numbers.Number) for y in x)
)
default_cfg_scale = get_config_item_or_set_default(
    key='default_cfg_scale',
    default_value=7.0,
    validator=lambda x: isinstance(x, numbers.Number)
)
default_sample_sharpness = get_config_item_or_set_default(
    key='default_sample_sharpness',
    default_value=2.0,
    validator=lambda x: isinstance(x, numbers.Number)
)
default_sampler = get_config_item_or_set_default(
    key='default_sampler',
    default_value='dpmpp_2m_sde_gpu',
    validator=lambda x: x in modules.flags.sampler_list
)
default_scheduler = get_config_item_or_set_default(
    key='default_scheduler',
    default_value='karras',
    validator=lambda x: x in modules.flags.scheduler_list
)

def sdxl_styles_validator(x):
    if not isinstance(x, list):
        print("Validation failed: The variable 'x' is not a list.")
        print(f"Type of x: {type(x)}")
        return False

    for y in x:
        if y not in modules.sdxl_styles.legal_style_names:
            print("Validation failed: An element in 'x' is not in legal_style_names.")
            print(f"Failed element: {y}")
            return False

    return True

def sdxl_styles_corrector(value):
    return correct_case_sensitivity(value, modules.sdxl_styles.legal_style_names)

default_styles = get_config_item_or_set_default(
    key='default_styles',
    default_value=[
        "Fooocus V2",
        "Fooocus Enhance",
        "Fooocus Sharp"
    ],
    validator=sdxl_styles_validator,
    corrector=sdxl_styles_corrector
)
default_prompt_negative = get_config_item_or_set_default(
    key='default_prompt_negative',
    default_value='',
    validator=lambda x: isinstance(x, str),
    disable_empty_as_none=True
)
default_prompt = get_config_item_or_set_default(
    key='default_prompt',
    default_value='',
    validator=lambda x: isinstance(x, str),
    disable_empty_as_none=True
)
default_performance = get_config_item_or_set_default(
    key='default_performance',
    default_value='Speed',
    validator=lambda x: x in modules.flags.performance_selections
)
default_advanced_checkbox = get_config_item_or_set_default(
    key='default_advanced_checkbox',
    default_value=False,
    validator=lambda x: isinstance(x, bool)
)
default_max_image_number = get_config_item_or_set_default(
    key='default_max_image_number',
    default_value=32,
    validator=lambda x: isinstance(x, int) and x >= 1
)
default_image_number = get_config_item_or_set_default(
    key='default_image_number',
    default_value=2,
    validator=lambda x: isinstance(x, int) and 1 <= x <= default_max_image_number
)
checkpoint_downloads = get_config_item_or_set_default(
    key='checkpoint_downloads',
    default_value={},
    validator=lambda x: isinstance(x, dict) and all(isinstance(k, str) and isinstance(v, str) for k, v in x.items())
)
lora_downloads = get_config_item_or_set_default(
    key='lora_downloads',
    default_value={},
    validator=lambda x: isinstance(x, dict) and all(isinstance(k, str) and isinstance(v, str) for k, v in x.items())
)
embeddings_downloads = get_config_item_or_set_default(
    key='embeddings_downloads',
    default_value={},
    validator=lambda x: isinstance(x, dict) and all(isinstance(k, str) and isinstance(v, str) for k, v in x.items())
)
available_aspect_ratios = get_config_item_or_set_default(
    key='available_aspect_ratios',
    default_value=[
        '64*64', '128*128', '256*256', '512*512', '1024*1024',
        '704*1408', '704*1344', '768*1344', '768*1280', '832*1216', '832*1152',
        '896*1152', '896*1088', '960*1088', '960*1024', '1024*960',
        '1088*960', '1088*896', '1152*896', '1152*832', '1216*832', '1280*768',
        '1344*768', '1344*704', '1408*704', '1472*704', '1536*640', '1600*640',
        '1664*576', '1728*576', '1920*1080', '800*600', '600*800',
        '1200*900', '900*1200', '1600*1200', '1200*1600', 
        '1191*842', '842*1191', '1280*720', '2560*1440'
    ],
    validator=lambda x: isinstance(x, list) and all('*' in v for v in x) and len(x) > 1
)
default_aspect_ratio = get_config_item_or_set_default(
    key='default_aspect_ratio',
    default_value='1152*896' if '1152*896' in available_aspect_ratios else available_aspect_ratios[0],
    validator=lambda x: x in available_aspect_ratios
)
default_inpaint_engine_version = get_config_item_or_set_default(
    key='default_inpaint_engine_version',
    default_value='v2.6',
    validator=lambda x: x in modules.flags.inpaint_engine_versions
)
default_cfg_tsnr = get_config_item_or_set_default(
    key='default_cfg_tsnr',
    default_value=7.0,
    validator=lambda x: isinstance(x, numbers.Number)
)
default_overwrite_step = get_config_item_or_set_default(
    key='default_overwrite_step',
    default_value=-1,
    validator=lambda x: isinstance(x, int)
)
default_overwrite_switch = get_config_item_or_set_default(
    key='default_overwrite_switch',
    default_value=-1,
    validator=lambda x: isinstance(x, int)
)
use_cleanup_model_previews = get_config_item_or_set_default(
    key='use_cleanup_model_previews',
    default_value=False,
    validator=lambda x: x == False or x == True
)
use_add_model_previews = get_config_item_or_set_default(
    key='use_add_model_previews',
    default_value=True,
    validator=lambda x: x == False or x == True
)
use_gpu_model_loader = get_config_item_or_set_default(
    key='use_gpu_model_loader',
    default_value=True,
    validator=lambda x: x == False or x == True
)
use_model_cache = get_config_item_or_set_default(
    key='use_model_cache',
    default_value=True,
    validator=lambda x: x == False or x == True
)
example_inpaint_prompts = get_config_item_or_set_default(
    key='example_inpaint_prompts',
    default_value=[
        'highly detailed face', 'detailed girl face', 'detailed man face', 'detailed hand', 'beautiful eyes'
    ],
    validator=lambda x: isinstance(x, list) and all(isinstance(v, str) for v in x)
)

example_inpaint_prompts = [[x] for x in example_inpaint_prompts]

config_dict["default_loras"] = default_loras = default_loras[:default_loras_max_number] + [['None', 1.0] for _ in range(default_loras_max_number - len(default_loras))]

possible_preset_keys = [
    "default_model",
    "default_refiner",
    "default_refiner_switch",
    "default_loras_min_weight",
    "default_loras_max_weight",
    "default_loras",
    "default_loras_max_number",
    "default_cfg_scale",
    "default_sample_sharpness",
    "default_sampler",
    "default_scheduler",
    "default_performance",
    "default_prompt",
    "default_prompt_negative",
    "default_styles",
    "default_aspect_ratio",
    "use_cleanup_model_previews",
    "use_add_model_previews",
    "use_gpu_model_loader",
    "use_model_cache",
    "checkpoint_downloads",
    "embeddings_downloads",
    "lora_downloads",
]


REWRITE_PRESET = False

if REWRITE_PRESET and isinstance(args_manager.args.preset, str):
    save_path = 'presets/' + args_manager.args.preset + '.json'
    with open(save_path, "w", encoding="utf-8") as json_file:
        json.dump({k: config_dict[k] for k in possible_preset_keys}, json_file, indent=4)
    print(f'Preset saved to {save_path}. Exiting ...')
    exit(0)


def add_ratio(x):
    a, b = x.replace('*', ' ').split(' ')[:2]
    a, b = int(a), int(b)
    g = math.gcd(a, b)
    return f'{a}×{b} <span style="color: grey;"> \U00002223 {a // g}:{b // g}</span>'


default_aspect_ratio = add_ratio(default_aspect_ratio)
available_aspect_ratios = [add_ratio(x) for x in available_aspect_ratios]


# Only write config in the first launch.
if not os.path.exists(config_path):
    with open(config_path, "w", encoding="utf-8") as json_file:
        json.dump({k: config_dict[k] for k in always_save_keys}, json_file, indent=4)


# Always write tutorials.
with open(config_example_path, "w", encoding="utf-8") as json_file:
    cpa = config_path.replace("\\", "\\\\")
    json_file.write(f'You can modify your "{cpa}" using the below keys, formats, and examples.\n'
                    f'Do not modify this file. Modifications in this file will not take effect.\n'
                    f'This file is a tutorial and example. Please edit "{cpa}" to really change any settings.\n'
                    + 'Remember to split the paths with "\\\\" rather than "\\", '
                      'and there is no "," before the last "}". \n\n\n')
    json.dump({k: config_dict[k] for k in visited_keys}, json_file, indent=4)


os.makedirs(path_outputs, exist_ok=True)


def downloading_inpaint_models(v):
    assert v in modules.flags.inpaint_engine_versions

    load_file_from_url(
        url='https://huggingface.co/lllyasviel/fooocus_inpaint/resolve/main/fooocus_inpaint_head.pth',
        model_dir=path_inpaint,
        file_name='fooocus_inpaint_head.pth'
    )
    head_file = os.path.join(path_inpaint, 'fooocus_inpaint_head.pth')
    patch_file = None

    if v == 'v1':
        load_file_from_url(
            url='https://huggingface.co/lllyasviel/fooocus_inpaint/resolve/main/inpaint.fooocus.patch',
            model_dir=path_inpaint,
            file_name='inpaint.fooocus.patch'
        )
        patch_file = os.path.join(path_inpaint, 'inpaint.fooocus.patch')

    if v == 'v2.5':
        load_file_from_url(
            url='https://huggingface.co/lllyasviel/fooocus_inpaint/resolve/main/inpaint_v25.fooocus.patch',
            model_dir=path_inpaint,
            file_name='inpaint_v25.fooocus.patch'
        )
        patch_file = os.path.join(path_inpaint, 'inpaint_v25.fooocus.patch')

    if v == 'v2.6':
        load_file_from_url(
            url='https://huggingface.co/lllyasviel/fooocus_inpaint/resolve/main/inpaint_v26.fooocus.patch',
            model_dir=path_inpaint,
            file_name='inpaint_v26.fooocus.patch'
        )
        patch_file = os.path.join(path_inpaint, 'inpaint_v26.fooocus.patch')

    return head_file, patch_file


def downloading_sdxl_lcm_lora():
    load_file_from_url(
        url='https://huggingface.co/lllyasviel/misc/resolve/main/sdxl_lcm_lora.safetensors',
        model_dir=path_loras,
        file_name='sdxl_lcm_lora.safetensors'
    )
    return 'sdxl_lcm_lora.safetensors'


def downloading_controlnet_canny():
    load_file_from_url(
        url='https://huggingface.co/lllyasviel/misc/resolve/main/control-lora-canny-rank128.safetensors',
        model_dir=path_controlnet,
        file_name='control-lora-canny-rank128.safetensors'
    )
    return os.path.join(path_controlnet, 'control-lora-canny-rank128.safetensors')


def downloading_controlnet_cpds():
    load_file_from_url(
        url='https://huggingface.co/lllyasviel/misc/resolve/main/fooocus_xl_cpds_128.safetensors',
        model_dir=path_controlnet,
        file_name='fooocus_xl_cpds_128.safetensors'
    )
    return os.path.join(path_controlnet, 'fooocus_xl_cpds_128.safetensors')


def downloading_ip_adapters(v):
    assert v in ['ip', 'face']

    results = []

    load_file_from_url(
        url='https://huggingface.co/lllyasviel/misc/resolve/main/clip_vision_vit_h.safetensors',
        model_dir=path_clip_vision,
        file_name='clip_vision_vit_h.safetensors'
    )
    results += [os.path.join(path_clip_vision, 'clip_vision_vit_h.safetensors')]

    load_file_from_url(
        url='https://huggingface.co/lllyasviel/misc/resolve/main/fooocus_ip_negative.safetensors',
        model_dir=path_controlnet,
        file_name='fooocus_ip_negative.safetensors'
    )
    results += [os.path.join(path_controlnet, 'fooocus_ip_negative.safetensors')]

    if v == 'ip':
        load_file_from_url(
            url='https://huggingface.co/lllyasviel/misc/resolve/main/ip-adapter-plus_sdxl_vit-h.bin',
            model_dir=path_controlnet,
            file_name='ip-adapter-plus_sdxl_vit-h.bin'
        )
        results += [os.path.join(path_controlnet, 'ip-adapter-plus_sdxl_vit-h.bin')]

    if v == 'face':
        load_file_from_url(
            url='https://huggingface.co/lllyasviel/misc/resolve/main/ip-adapter-plus-face_sdxl_vit-h.bin',
            model_dir=path_controlnet,
            file_name='ip-adapter-plus-face_sdxl_vit-h.bin'
        )
        results += [os.path.join(path_controlnet, 'ip-adapter-plus-face_sdxl_vit-h.bin')]

    return results


def downloading_upscale_model():
    load_file_from_url(
        url='https://huggingface.co/lllyasviel/misc/resolve/main/fooocus_upscaler_s409985e5.bin',
        model_dir=path_upscale_models,
        file_name='fooocus_upscaler_s409985e5.bin'
    )
    return os.path.join(path_upscale_models, 'fooocus_upscaler_s409985e5.bin')


if use_cleanup_model_previews:
    cleanup_model_previews()
