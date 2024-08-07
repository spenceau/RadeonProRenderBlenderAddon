import importlib
# clear cache
importlib.invalidate_caches()

import os
import subprocess
import shutil
import sys
from dotenv import load_dotenv
import zipfile
import platform

# wrapper function to call bpy


def ensure_plugin_structure(plugin_folder):
    required_dirs = ['addons', 'modules', 'startup']
    for dir in required_dirs:
        path = os.path.join(plugin_folder, dir)
        if not os.path.exists(path):
            os.makedirs(path)


# unzips addon into the target directory
# RPRNAS seems to have double zips
def extract_addon_to_module(target_dir):
    # Extract the ZIP file to the target directory
    with zipfile.ZipFile(addon, 'r') as zip_ref:
        zip_ref.extractall(target_dir)

    print(f"Addon extracted to {target_dir}")

    # check for double zips as in the case of rprnas
    for root, dirs, files in os.walk(target_dir):
        for file in files:
            if file.endswith('.zip'):
                zip_path = os.path.join(root, file)
                with zipfile.ZipFile(zip_path, 'r') as inner_zip_ref:
                    inner_zip_ref.extractall(target_dir)
                print(f"Extracted inner ZIP: {zip_path}")
                os.remove(zip_path) # delete zip


def remove_rprblender(target_dir, plugin_dir):
    try:
        addon = os.path.join(target_dir, "rprblender")
        shutil.rmtree(addon, ignore_errors=True)
        shutil.rmtree(plugin_dir, ignore_errors=True)
        print(f"rprblender removed successfully from {target_dir}.")
    except Exception as e:
        print(f"Error removing rprblender: {e}")


def print_sys_path():
    print("SYS.PATH FOR cmd_render.py")
    for i, path in enumerate(sys.path):
        print(f"{i}: {path}")


if __name__ == "__main__":

    load_dotenv()

    #sys.path.append("./rprblender")
    script = sys.argv[1]
    blender_path = os.getenv('BLENDER_PATH')
    #print(f"BLENDER PATH: {blender_path}")
    blender_version = blender_version = " ".join(os.path.basename(blender_path).split()[-2:])
    #print(f"BLENDER VERSION: {blender_version}")
    if platform.system() == 'Windows':
        blender_exe = os.path.join(blender_path, "blender.exe")
        python = 'python'
    else:
        # assumes platform is Ubuntu/Linux
        blender_exe = os.path.join(blender_path, "blender")
        python = 'python3.11'

    addon = os.getenv('ADDON_ZIP')
    blender_files = os.getenv('SCENE_PATH')
    scene = os.getenv('SCENE_NAME')
    build = os.path.basename(addon)

    output_dir = os.path.join(os.getenv('RENDER_OUTPUT_DIR'), os.path.basename(addon), blender_version)
    plugin_folder = os.getenv('PLUGIN')

    ground_truth = os.getenv('GROUND_TRUTH')
    viewport_flag = os.getenv('VIEWPORT_FLAG')

    print(f"Scene name: {scene}")

    # creates dir with 3 necessary subdir to extract build zip into
    ensure_plugin_structure(plugin_folder)
    target_dir = os.path.join(os.getcwd(), plugin_folder, "modules")

    # extract zip file to blender's modules subdir in scripts
    extract_addon_to_module(target_dir)

    # run add_script.py to add the directory to Blender's scripts and then "restart" Blender

    cwd =  os.getcwd()
    subprocess.run([
        blender_exe,
        '--background',
        '--python', os.path.join(cwd, "add_script.py"),
        plugin_folder
    ])

    # Always run final_render.py
    final_render_command = [
        blender_exe,
        '--background',
        '--python', script,
        blender_files,
        scene,
        output_dir,
    ]
    subprocess.run(final_render_command)

    # need to run remove_script.py since a failed render seems to kick out of final_render.py
    cwd =  os.getcwd()
    subprocess.run([
        blender_exe,
        '--background',
        '--python', os.path.join(cwd, "remove_script.py"),
        plugin_folder,
        output_dir,
        scene
    ])

    # Always run compare_render.py after final_render.py
    compare_render_command = [
        python, 'compare_render.py',     
        '--ground-truth-dir', ground_truth,
        '--output-dir', output_dir,
        '--scene-name', scene
    ]
    subprocess.run(compare_render_command)

    # Conditionally run viewport render
    # TODO: this hasn't been changed to reflect pulling from zip; probably unnecessary as this isn't going to be used per Sho
    viewport_render_command = [
        blender_path,
        '--python', 'viewport_render.py',
        '--',
        '--scene-path', blender_files,
        '--scene-name', scene,
        '--addon-zip', addon
    ]
    if viewport_flag == 1:
        subprocess.check_call(viewport_render_command)

    remove_rprblender(target_dir, plugin_folder)
