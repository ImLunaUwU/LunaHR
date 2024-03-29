# LunaHR - Heart rate to VRChat through OSC 

If you like my project, please star it as it shows you're interested! <3

*Important: DO NOT run the scripts as administrator, or the modules will be installed wrongly.*

At this moment, its unsure if an H9 or other Polar devices would work with the PolarH10 script.

H10 and devices used with Pulsoid are the only confirmed to work at the current moment.
If you have another Polar monitor, please test my script with your device and let me know if it works! <3

#### Please direct issues to me, I'd love to fix any.

## Setup:

### Avatar
This project only uses 5 parameters (Using 33 just memory)!

The needed prefabs is in LunaHR.unitypackage. Avatar setup is as simple as any other VRCFury asset, and should be drag and drop onto your avatar.

Before importing LunaHR.unitypackage, please make sure you already have Poiyomi Toon (or Poi Pro) installed.
Alternatively, if you do not want to use Poi, you'd lack the BPM effect unless you set it up yourself.
This is slightly time consuming, but overall worth it.

*HR Prefab should be dragged onto the avatar root itself.*

When adding to the avatar, the display defaults to be on your wrist/left lower arm bone. This can be changed by unpacking the prefab and changing armature link settings.

VRCFury should take care of all setup from this point. If not, please contact me because then I'd need to fix some things.

*The "Display" part of the prefab should be unchecked before uploading.* The default state is off, and it'll become visible when toggled through the menu.



### Polar H10
The only thing you should need to change is "POLAR_H10_NAME" within the script.

This can be found by using your phone's bluetooth pairing screen, BLE devices SHOULD show up.
If they dont

### Pulsoid
Replace "YOUR_ACCESS_TOKEN_HERE" in the pulsoidHROSC script with your token. A token requires Pulsoid's "BRO" plan and can be found at https://pulsoid.net/ui/keys

## Credits and info
HEAVILY inspired by the (now inactive) project here: https://github.com/200Tigersbloxed/HRtoVRChat_OSC/

This project does NOT use the same parameters as the one by 200Tigersbloxed. It does use less though.
This is both because they're not meant to be the same, nor compatible, and also becuase everything in that project is outdated and the Unity files doesn't really work properly anymore.
*Feel free to use mine as a (semi-)direct replacement.*

The heart and text uses Poiyomi Toon, which you can get from Poi's Discord. https://discord.gg/poiyomi

OSC port (AND VRCHAT IP) can be changed in the scripts as well.