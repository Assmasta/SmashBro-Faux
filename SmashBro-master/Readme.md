# SmashBro
###### The following instructions have been copied from SmashBot
## The original can be found at https://github.com/altf4/SmashBot
#### libmelee can be found at https://github.com/altf4/libmelee

### FAQ

1. **What character does SmashBro-Faux play?**

    Fox.

2. **Does SmashBro work with Slippi?**

    Works on the regular Slippi Dolphin install.

3. **Can I run SmashBro online?**

    It would be a lot cooler if you didn't.

4. **Does SmashBro cheat?**

    No, it plays the game just as Sakurai intended /s. It presses buttons to play as a regular player would, just faster.
    
5. **How is SmashBro designed?**

    SmashBro makes decisions on a tiered hierarchy of objectives: Strategies, Tactics, and Chains. Each objective inspects the current game state and decides which lower level objective will be best to achieve it.

    **Strategies** are the highest level means that the AI will use to accomplish the overall goal. For instance, the SmashBro will typically take the strategy of baiting the opponent into a poor move.

    **Tactics** are lowish level series of predictable circumstances that we can realistically flowchart our way through. For instance, if the enemy is off the stage we may choose to edge guard them to keep them from getting back on.

    **Chains** are the lowest level of objective that consists of a "chain" of button presses that Smashers will recognize, such as Wavedash, Jump-canceled Upsmash, etc...

6. **Can I play SmashBro on a regular GameCube or hacked Wii?**

    No.

7. **What operating systems does it play on?**

    SmashBro runs on Linux, OSX, and Windows.

8. **I found a bug. How can I help?**

    If you can reliably reproduce the bug, please make an Issue on GitHub at https://github.com/Assmasta/SmashBro-Faux/issues. It would be even cooler if you run the AI with the "--debug" flag and upload the CSV file it gives you along with the issue. That CSV contains a full breakdown of the AI's state at each frame, so we can find the issue more easily.


## Setup Steps:
Exactly the same as SmashBot's

1. Install libmelee, a Python 3 API for interacting with Dolphin and Melee. `pip3 install melee`
Also make sure to stay updated on libmelee with `pip3 install --upgrade melee`

2. Install and configure Slippi, just like you would for rollback netplay. Full instructions here: https://slippi.gg

3. You'll probably want a GameCube Adapter, available on Amazon here: https://www.amazon.com/Super-Smash-GameCube-Adapter-Wii-U/dp/B00L3LQ1FI. Or alternatively the HitBox adapter works well too: https://www.hitboxarcade.com/products/gamecube-controller-adapter

4. Install some custom Slippi Gecko Codes. You can find them here: https://github.com/altf4/slippi-ssbm-asm/blob/libmelee/Output/Netplay/GALE01r2.ini Simply replace your existing `GALE01r2.ini` file with this one.

5. Make sure you have all the `Required` and `Recommended` Gecko Codes enabled.

6. Disable the `Apply Delay to all In-Game Screens` Gecko Code.

7. Run `SmashBro.py -e PATH_TO_SLIPPI_FOLDER` (Not the actual exe itself, just the directory where it is)

8. By default, SmashBro takes controller 2, and assumes you're on controller 1. You can change this with the `--port N`  option to change SmashBro's port, and `--opponent N` to change the human player's port.
