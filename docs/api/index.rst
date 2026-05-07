JustDoIt API Reference
======================

Zero-dependency Python 3 ASCII art CLI with multi-line ANSI-colorized terminal output.

Overview
--------

**JustDoIt** renders text as ASCII art using:

* Built-in fonts (block, slim)
* FIGlet fonts (banner, big, bubble, digital, slant)
* TTF/OTF system fonts (requires Pillow)

Features:

* Zero required dependencies - pure Python 3 stdlib core
* Optional Pillow for TTF/OTF fonts and image export
* Optional numpy + sounddevice for audio synthesis
* ANSI color effects and rainbow mode
* Animation engine with typewriter, scanline, glitch effects
* Size/scale/resolution-aware rendering for physical media

API Documentation
-----------------

.. toctree::
   :maxdepth: 2
   :caption: Modules:

   modules

Core Modules
~~~~~~~~~~~~

.. toctree::
   :maxdepth: 1

   justdoit.cli
   justdoit.core
   justdoit.layout

Font System
~~~~~~~~~~~

.. toctree::
   :maxdepth: 1

   justdoit.fonts
   justdoit.fonts.builtin
   justdoit.fonts.figlet
   justdoit.fonts.ttf

Effects
~~~~~~~

.. toctree::
   :maxdepth: 1

   justdoit.effects.color
   justdoit.effects.fill
   justdoit.effects.gradient
   justdoit.effects.bloom
   justdoit.effects.isometric

Output
~~~~~~

.. toctree::
   :maxdepth: 1

   justdoit.output.terminal
   justdoit.output.html
   justdoit.output.svg
   justdoit.output.image

Animation
~~~~~~~~~

.. toctree::
   :maxdepth: 1

   justdoit.animate

Sound (Optional)
~~~~~~~~~~~~~~~~

.. toctree::
   :maxdepth: 1

   justdoit.sound

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
