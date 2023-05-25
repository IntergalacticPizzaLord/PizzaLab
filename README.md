PizzaLab
--------
Character Assembler for Blender
This repository contains the Character Assembler addon for Blender 3.5.0 and later. The addon is designed to generate 3D characters based on fRiENDSiES NFTs, a collection of 10,000 unique tokens representing a wide variety of character traits. These traits, designed by FriendsWithYou, include custom heads, bodies, sprouts, tails, and other unique attributes. With this addon, users can create their unique 3D fRiENDSiES, bringing these digital companions to life in Blender​1​​2​.

Installation
--------------
1. Download or clone this repository to your local machine.
2. Open Blender and navigate to Edit > Preferences > Add-ons.
3. Click Install... and navigate to the downloaded directory and select the python file character_assembler.py.
4. Enable the addon by checking the box next to "Character Assembler".

Features
----------
- Display Attributes: This feature provides a visual representation of the attributes associated with a given token number.
- Build Character: This feature generates a 3D character based on the provided token number.
- Save GLB: This feature exports the generated 3D character as a GLB file.
- Batch Import Characters: This feature allows for the bulk import of characters based on a provided JSON file containing token numbers.

Usage
-------
1. After installing and enabling the addon, navigate to the 3D viewport in Blender.
2. In the 3D viewport, navigate to the right panel (press N if not visible), and find the "Character Assembler" tab.
3. Enter a token number from 1 to 10,000 in the "Token Number" field.
4. Click the "Display Attributes" button to display the attributes associated with the entered token number.
5. Click the "Build Character" button to generate a 3D character based on the displayed attributes.
6. To save the generated character as a GLB file, click the "Save GLB" button.
7. To import characters in bulk, click the "Batch Import Characters" button and select a JSON file containing token numbers.

Contributing
--------------
Contributions are welcome! Please read the contributing guidelines before getting started.

License
--------
This project is licensed under the MIT License.
