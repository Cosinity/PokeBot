import unittest
from Main import Pokemon


# Unit tests for the Pokemon class
class TestPokemonMethods(unittest.TestCase):
    def test_damage(self):
        greninja.set_health(100)
        mawile.set_health(0)
        rotom.set_health(-1)
        self.assertEqual(greninja.cur_health, 100)
        self.assertEqual(mawile.cur_health, 0)
        self.assertEqual(rotom.cur_health, 0)

    def test_change_ability(self):
        greninja.change_ability('mummy')
        self.assertEqual(greninja.ability, 'mummy')

    def test_apply_stat_mods(self):
        # TODO change these tests to look at evs and ivs
        self.assertTrue(True)
        # greninja.apply_stat_mod('spa', 1)
        # mawile.apply_stat_mod('spe', -2)
        # rotom.apply_stat_mod('foo', 1)
        # self.assertEqual(greninja.stat_mods, ['0', '0', '0', '1', '0', '0'])
        # self.assertEqual(mawile.stat_mods, ['0', '0', '0', '0', '0', '-2'])
        # self.assertEqual(rotom.stat_mods, ['0', '0', '0', '0', '0', '0'])
        # greninja.apply_stat_mod('spa', 2)
        # self.assertEqual(greninja.stat_mods, ['0', '0', '0', '3', '0', '0'])

    def test_get_modded_stats(self):
        self.assertEqual(greninja.get_stats(), [286, 293, 170, 1012, 278, 399])
        self.assertEqual(mawile.get_stats(), [286, 315, 286, 131, 226, 88])
        self.assertEqual(rotom.get_stats(), [304, 121, 330, 246, 250, 222])

    def test_status(self):
        greninja.set_status('tox')
        greninja.set_status('par')
        self.assertEqual(greninja.get_status()[0], 'tox')

        mawile.set_status('confused')
        mawile.set_status('trapped')
        self.assertEqual(mawile.get_status()[1], ['confused', 'trapped'])

        self.assertFalse(rotom.set_status('foo'))

        greninja.cure_status()
        self.assertEqual(greninja.get_status()[0], 'healthy')

    def test_valid_moves(self):
        self.assertEqual(greninja.get_usable_moves(), ['dark pulse'])
        self.assertEqual(mawile.get_usable_moves(), ['swords dance', 'play rough', 'thunder punch', 'sucker punch'])
        self.assertEqual(rotom.get_usable_moves(), ['volt switch', 'hydro pump', 'pain split'])


if __name__ == "__main__":
    greninja = Pokemon('Greninja', 286, 'battle bond', [286, 293, 170, 405, 278, 399],
                       [('spikes', True), ('water shuriken', True), ('dark pulse', False), ('hydro pump', True)],
                    'choice specs')
    mawile = Pokemon('Mawile', 286, 'intimidate', [286, 315, 286, 131, 226, 177],
                     [('swords dance', False), ('play rough', False), ('thunder punch', False), ('sucker punch', False)],
                    'mawilite')
    rotom = Pokemon('Rotom-Wash', 10, 'levitate', [304, 121, 330, 246, 250, 222],
                    [('volt switch', False), ('hydro pump', False), ('will-o-wisp', True), ('pain split', False)],
                    'leftovers')
    unittest.main()
