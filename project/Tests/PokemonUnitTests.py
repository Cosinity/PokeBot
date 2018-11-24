import unittest
from Main import Pokemon


# Unit tests for the Pokemon class
class TestPokemonMethods(unittest.TestCase):
    def test_damage(self):
        mon_1.set_health(100)
        mon_2.set_health(0)
        mon_3.set_health(-1)
        self.assertEqual(mon_1.cur_health, 186)
        self.assertEqual(mon_2.cur_health, 0)
        self.assertEqual(mon_3.cur_health, 0)

    def test_change_ability(self):
        mon_1.change_ability('mummy')
        self.assertEqual(mon_1.ability, 'mummy')

    def test_apply_stat_mods(self):
        mon_1.apply_stat_mod('spa', 1)
        mon_2.apply_stat_mod('spe', -2)
        mon_3.apply_stat_mod('foo', 1)
        self.assertEqual(mon_1.stat_mods, ['0', '0', '0', '1', '0', '0'])
        self.assertEqual(mon_2.stat_mods, ['0', '0', '0', '0', '0', '-2'])
        self.assertEqual(mon_3.stat_mods, ['0', '0', '0', '0', '0', '0'])
        mon_1.apply_stat_mod('spa', 2)
        self.assertEqual(mon_1.stat_mods, ['0', '0', '0', '3', '0', '0'])

    def test_get_modded_stats(self):
        self.assertEqual(mon_1.get_stats(), [286, 293, 170, 1012, 278, 399])
        self.assertEqual(mon_2.get_stats(), [286, 315, 286, 131, 226, 88])
        self.assertEqual(mon_3.get_stats(), [304, 121, 330, 246, 250, 222])

    def test_status(self):



if __name__ == "__main__":
    mon_1 = Pokemon(286, 'battle bond', [286, 293, 170, 405, 278, 399],
                    ['spikes', 'water shuriken', 'dark pulse', 'hydro pump'], 'choice specs')
    mon_2 = Pokemon(286, 'initimidate', [286, 315, 286, 131, 226, 177],
                    ['swords dance', 'play rough', 'thunder punch', 'sucker punch'], 'mawilite')
    mon_3 = Pokemon(10, 'levitate', [304, 121, 330, 246, 250, 222],
                    ['volt switch', 'hydro pump', 'will-o-wisp', 'pain split'], 'leftovers')
    unittest.main()
