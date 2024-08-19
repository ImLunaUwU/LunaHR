# LunaHR - Heart rate to VRChat through OSC 

<img src="app_icon.png" width="200" height="200" />

If you like my project, please star it as it shows you're interested! <3

At this moment, its unsure if an H9 or other Polar devices would work with the PolarH10 script.

H10 and devices used with Pulsoid are the only confirmed to work at the current moment.
If you have another Polar monitor, please test my script with your device and let me know if it works! <3

[Consider supporting me on Ko-Fi :3](https://ko-fi.com/imlunauwu)

#### Please direct issues to me, I'd love to fix any.
^ Message me on Discord @ imlunauwu.

## Installs:

Everything should now be straightforward.

Get the Unity prefab here: [Quest compatible (33 bytes)](https://github.com/ImLunaUwU/LunaHR/blob/main/LunaHR%20(33%20bytes%2C%20works%20with%20quest).unitypackage), [PC only (9 bytes)](https://github.com/ImLunaUwU/LunaHR/blob/main/LunaHR%20(9%20bytes%2C%20not%20quest%20compatible).unitypackage)

Get the executable versions of the HR software from here: [Polar (H10)](https://github.com/ImLunaUwU/LunaHR/blob/main/dist/PolarH10OSC.exe), [Pulsoid (Now with OAuth)](https://github.com/ImLunaUwU/LunaHR/blob/main/dist/PulsoidHROSC%20OAuth.exe)

I'm gonna be honest and say your anti-virus probably wont like them, due to the fact that they're unsigned and the backend is Python.
If you do not trust the EXEs, feel free to use the raw Python scripts. They're essentially the same, but one (the exe) is neater and comes with the dependencies packaged.

I have no clue how to get this unflagged, since it is what it is. A Python script. I'd remake this in electron and all, but idk how to use that :c

The executable versions wont require you installing a bunch of things, as all dependencies are packaged within. For this reason, it also runs slightly better... Probably...

![Image of the executables](zginbfyf.bmp)
## Setup:

### Avatar
The needed prefabs is in the unitypackages (see links above). Avatar setup is as simple as any other VRCFury asset, and should be drag and drop onto your avatar.

Before importing the unitypackage, please make sure you already have Poiyomi Toon (or Poi Pro) installed.
Alternatively, if you do not want to use Poi, you'd lack the BPM effect unless you set it up yourself.
This is slightly time consuming, but overall worth it if you're chronically online like me.

*HR Prefab should be dragged onto the avatar root itself.*

When adding to the avatar, the display defaults to be on your left wrist/left lower arm bone. This can be changed by unpacking the prefab and changing armature link settings.

VRCFury should take care of all setup from this point. If not, please contact me because then I'd need to fix some things.

*In the most recent update HR Prefab can be left on before uploading, as it now uses VRCFury toggles.*

Feel free to customize materials to your liking.

### Polar H10
Everything is now configurable in the new GUI app.

### Pulsoid - PAID PLAN REQUIRED
Login is simple and in a GUI. This requires Pulsoid's "BRO" plan.
Click the login button and approve in your browser. After this, you should be logged in.

This feature is new, so bugs can happen. If you find any, please report them.

## Credits and info
HEAVILY inspired by the (now inactive) project here: https://github.com/200Tigersbloxed/HRtoVRChat_OSC/

This project does NOT use the same parameters as the one by 200Tigersbloxed. It does use less though.
This is both because they're not meant to be the same, nor compatible, and also becuase everything in that project is outdated and the Unity files doesn't really work properly anymore.
*Feel free to use mine as a (semi-)direct replacement.*

PC only prefab uses the [Simple Counter Shader](https://www.patreon.com/posts/simple-counter-62864361) from [RED_SIM](https://www.patreon.com/red_sim).

#### Parameter configuration may come in the future, though is not currently a priority. 

The heart and text uses Poiyomi Toon, which you can get from Poi's Discord. https://discord.gg/poiyomi