# custom-platformer-DaFluffyPotatoTutorial

## Getting Started

This is heavily based off of DaFluffyPotato's Pygame Platformer course, which can be found <a href="https://www.youtube.com/watch?v=2gABYM5M0ww&t=1021s">here</a>, but is also a very big customization, with custom pixel art, heavy refactoring and physics tweaks to the original game. As well as some additional features, such as bullets are fired at your last known position using unit vectors.

In order to run the game, install dependencies from the GAME directory's requirements.txt file. Then run game.py. Certain debugging prints may still be in effect from development tracking collisions and player position. 

In order to change levels you need to adjust the ```self.starting_level``` variable in the Game class. This can correspond to any of the string filenames contained within the maps folder. 

Controls for the game are typical WAD for up, left and right. You can dash using P to kill enemies and you can jump with the space bar. As in the tutorial, you can wall jump as well. Additional characters may spawn in because this program was primarily used to shoot scenes for a video which was used for a large kids event. The video was then edited with voice over parts and different visual effects, so while it can be a fully functional game, it was never designed to be as it was primarily for setting up scenes for screen recording.

The character pixel art is all custom, tiles such as dirt, clouds in the background, stone and other environmental tiles such as trees and flowers are from DaFluffyPotato. Pixel art of the Castle, its various furniture pieces and flags are all custom. I hope you enjoy this neat take at customizing this tutorial!

An Editor is also available to create your own levels which is editor.py. Using left and right click you can place tiles and delete them respectively. Scrolling with the mouse wheel will enable you to rotate through different tile categories for placement, while holding shift while you scroll through the tiles in that category. Pressing the O key will output your map as a json file which can be loaded by game.py. These are all features straight from DaFluffyPotato's tutorial.

Author:

- Michael Levins
    - GitHub: [@mclevins](https://github.com/mclevins)
    - LinkedIn: [in/michaelclevins](https://www.linkedin.com/in/michaelclevins/)

