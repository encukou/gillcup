#! /usr/bin/env python

from __future__ import division

import os

import pyglet
import gillcup

from gillcup_graphics import Window, run, RealtimeClock, Layer, Text, Sprite

clock = RealtimeClock()


def hello():
    """Show a simple message"""
    root_layer = Layer(scale=(1, 16 / 8))
    hi_world = Text(root_layer, 'Hello, World!',
            relative_anchor=(0.5, 0),
            position=(0.5, 0.5),
            scale=(0.001, 0.001),
        )

    Window(root_layer, width=400, height=400)

    answer(root_layer, hi_world)

    run()


def answer(root_layer, hi_world):
    """This one's more advanced"""
    def load_texture(path):
        full_path = os.path.join(
            os.path.dirname(__file__),
            'gillcup_graphics',
            'test',
            'images',
            'resource',
            path)
        return pyglet.image.load(full_path)
    hi_world.characters_displayed = 0
    text_anim = gillcup.Animation(hi_world, 'characters_displayed',
        len(hi_world.text), time=0.5)
    world = Sprite(root_layer,
            load_texture('northpole.png'),
            position=(0.5, -0.5),
            size=0.5,
            relative_anchor=(0.5, 0.5),
        )
    hi = Sprite(root_layer,
            load_texture('hi.png'),
            position=(0.7, 0.45),
            scale=(0, 1 / 1000),
            anchor=(10, 0),
        )
    answer_anim = (
            gillcup.Animation(world, 'rotation', 45, time=1,
                timing='infinite') |
            gillcup.Animation(hi_world, 'y', 0.75, time=1, easing='sine') |
            gillcup.Animation(world, 'y', 0.3, time=1) |
            (2 + gillcup.Animation(hi, 'scale', 1 / 400, 1 / 400, time=0.5,
                easing=gillcup.easing.overshoot(2).out)))
    clock.schedule(0.25 + text_anim + 2 + answer_anim)
    return answer

hello()
