
set .env variables for 
    BLENDER_PATH=C:\Program Files\Blender Foundation\Blender {VERSION}
    ADDON_ZIP={where build artifact zip is located}
    SCENE_PATH={directory containing blend files to be tested}
    SCENE_NAME={name of scene}
    GROUND_TRUTH={rendered image to compare to for MSE and SSIM}
    VIEWPORT_FLAG={0 for no viewport rendering, 1 for viewport}

Run with ./run_render.cmd with Administrator Priviledges as it modifies Program Files in the Blender/scripts/modules subdir