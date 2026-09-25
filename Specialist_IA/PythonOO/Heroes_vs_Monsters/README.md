Recap Exercise: Heroes vs Monsters

Welcome to the forest of “Shorewood”, an enchanted forest in the land of “Stormwall.” In this forest, a fierce battle takes place between heroes on one side and monsters on the other.

Our role is to bring this forest to life through a console program using all the object-oriented concepts seen during the course.

Let us describe this world a little. There are two families of characters:

Heroes: Human or Dwarf
Monsters: Wolf, Orc or Young Dragon

Each character has different characteristics:

Endurance (End)
Strength (For)
Health Points (HP / PV)

Strength and endurance are calculated when the character is created by rolling, for each characteristic, four six-sided dice and keeping only the best three.

Health points are determined by adding the endurance value and the modifier¹ based on endurance.

Characters have an action called Strike. When a character strikes another character, the damage is determined by rolling a four-sided die, to which a modifier¹ based on Strength is added. Once calculated, the damage is removed from the target’s health points.

When heroes kill monsters, they loot their wealth — gold and/or leather² — which they can store without limit.

After each fight, heroes rest, restore their health points, and face the next monster until they die³.
Hero types

There are two types of heroes:

Humans
+1 to Strength
+1 to Endurance
Dwarves
+2 to Endurance
Monster types
Wolves
They can be skinned.
They give leather.
Orcs
They have +1 Strength.
They have gold.
Young Dragons
They have +1 Endurance.
They have gold.
They can be skinned.
They give leather.
Constraints
Strength and Endurance are read-only properties.
The PV / health-points property is read-only.
The endurance and strength bonuses given by the classes Human, Dwarf, Orc, and Young Dragon must not modify the character’s base characteristic.
The Die class contains two read-only properties:
Minimum
Maximum
The Die class also contains a method Roll, which returns a random integer⁴.
Additional Exercise

Create a 15 × 15 game area containing around 10 monsters, spaced at least 2 squares apart, horizontally and vertically, from each other.

To do this, add two properties to the characters:

X
Y

These determine each character’s position on the board. Their position is known when they are created.

The monsters are hidden and appear only once the fight begins.

The fight starts automatically when the hero moves next to a monster, either horizontally or vertically.

The hero must be displayed with:

H

The monsters must be displayed with:

L = Wolf
O = Orc
D = Young Dragon

The game stops when:

there are no monsters left on the map;
or the hero dies.
Notes

¹ The modifier is based on the characteristic score and adds a bonus or penalty according to these rules:

Characteristic score	Modifier
less than 5	-1
less than 10	0
less than 15	+1
15 or more	+2

² Gold and leather are calculated when the monster is created:

Resource	Calculation
Gold	roll of a six-sided die
Leather	roll of a four-sided die

³ Any character dies when their health points are <= 0.

⁴ The Random class should help you.

Objectives: 
1. Understand the object.
2. Decide its state.
3. Decide its behavior.
4. Write the smallest class.
5. Test immediately.
6. Only then add inheritance or abstraction.

HeroesVsMonsters/
│
├── de.py
├── outils.py
├── personnage.py
├── hero.py
├── humain.py
├── nain.py
├── monstre.py
├── loup.py
├── orque.py
├── dragonnet.py
└── main.py

Minimum target:

A hero can fight one monster in console.
The monster loses PV.
The hero can die.
The code is split into files.
You understand every line.

Finalised: 
15x15 map
hidden monsters
10 monsters
movement
interfaces
perfect architecture

Rule of progression

We will build in this order:

1. De
2. modifier(characteristic)
3. generate characteristic
4. Personnage
5. frappe()
6. Humain / Nain
7. Monstre
8. Loup / Orque / Dragonnet
9. loot system
10. combat loop
11. map 15x15