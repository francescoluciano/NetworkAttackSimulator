import unittest
from collections import OrderedDict
import numpy as np
from cyber_attack_simulator.envs.environment import CyberAttackSimulatorEnv
import cyber_attack_simulator.envs.environment as Environment
from cyber_attack_simulator.envs.environment import Service
from cyber_attack_simulator.envs.action import Action
from cyber_attack_simulator.envs.state import State


class EnvironmentTestCase(unittest.TestCase):

    def setUp(self):
        self.E = 1
        self.M = 3
        self.env = self.get_env(self.M, self.E)
        self.network = self.env.network
        self.ads_space = self.network.get_address_space()

    def get_env(self, nM, nS):
        env = CyberAttackSimulatorEnv.from_params(nM, nS)
        return env

    def test_reset1(self):
        actual_obs = self.env.reset()
        expected_obs = self.get_initial_expected_obs()
        self.assertEqual(actual_obs, expected_obs)

    def test_reset2(self):
        t_action = Action(self.ads_space[0], "scan")
        o, _, _ = self.env.step(t_action)
        self.env.reset()
        actual_obs = self.env.reset()
        expected_obs = self.get_initial_expected_obs()
        self.assertEqual(actual_obs, expected_obs)

    def test_step_not_reachable(self):
        t_action = Action(self.ads_space[1], "scan")
        expected_obs = self.env.reset()
        o, r, d = self.env.step(t_action)
        self.assertEqual(r, -t_action.cost)
        self.assertFalse(d)
        self.assertEqual(o, expected_obs)

    def test_step_scan_reachable(self):
        t_action = Action(self.ads_space[0], "scan")
        expected_obs = self.env.reset()
        o, r, d = self.env.step(t_action)
        self.update_obs(t_action, expected_obs, True)
        self.assertEqual(r, -t_action.cost)
        self.assertFalse(d)
        self.assertEqual(o, expected_obs)

    def test_step_exploit_reachable(self):
        t_action = Action(self.ads_space[0], "exploit", 0)
        expected_obs = self.env.reset()
        o, r, d = self.env.step(t_action)
        self.update_obs(t_action, expected_obs, True)
        self.assertEqual(r, -t_action.cost)
        self.assertFalse(d)
        self.assertEqual(o, expected_obs)

    def test_step_exploit_sensitive(self):
        t_action = Action(self.ads_space[0], "exploit", 0)
        expected_obs = self.env.reset()
        self.env.step(t_action)
        self.update_obs(t_action, expected_obs, True)

        t_action2 = Action(self.ads_space[1], "exploit", 0)
        o, r, d = self.env.step(t_action2)
        self.update_obs(t_action2, expected_obs, True)

        self.assertEqual(r, Environment.R_SENSITIVE - t_action.cost)
        self.assertFalse(d)
        self.assertEqual(o, expected_obs)

    def test_step_exploit_user(self):
        t_action = Action(self.ads_space[0], "exploit", 0)
        expected_obs = self.env.reset()
        self.env.step(t_action)
        self.update_obs(t_action, expected_obs, True)

        t_action2 = Action(self.ads_space[2], "exploit", 0)
        o, r, d = self.env.step(t_action2)
        self.update_obs(t_action2, expected_obs, True)

        self.assertEqual(r, Environment.R_USER - t_action.cost)
        self.assertFalse(d)
        self.assertEqual(o, expected_obs)

    def test_step_done(self):
        t_action = Action(self.ads_space[0], "exploit", 0)
        expected_obs = self.env.reset()
        self.env.step(t_action)
        self.update_obs(t_action, expected_obs, True)

        t_action1 = Action(self.ads_space[1], "exploit", 0)
        o, r, d = self.env.step(t_action1)
        self.update_obs(t_action1, expected_obs, True)

        t_action2 = Action(self.ads_space[2], "exploit", 0)
        o, r, d = self.env.step(t_action2)
        self.update_obs(t_action2, expected_obs, True)

        self.assertTrue(d)
        self.assertEqual(o, expected_obs)

    def test_already_rewarded(self):
        t_action = Action(self.ads_space[0], "exploit", 0)
        expected_obs = self.env.reset()
        self.env.step(t_action)
        self.update_obs(t_action, expected_obs, True)

        t_action2 = Action(self.ads_space[2], "exploit", 0)
        o, r, d = self.env.step(t_action2)
        self.update_obs(t_action2, expected_obs, True)

        o, r, d = self.env.step(t_action2)
        self.update_obs(t_action2, expected_obs, True)

        self.assertEqual(r, 0 - t_action.cost)
        self.assertFalse(d)
        self.assertEqual(o, expected_obs)

    def get_initial_expected_obs(self):
        t_obs = OrderedDict()
        for m in self.ads_space:
            t_service_info = np.full(self.E, Service.unknown, Service)
            t_compromised = False
            t_reachable = False
            if self.network.subnet_exposed(m[0]):
                t_reachable = True
            t_obs[m] = [t_compromised, t_reachable, t_service_info]
        return State(t_obs)

    def update_obs(self, action, obs, success):
        """ Valid for test where E = 1 """
        target = action.target
        if success:
            for s in range(self.E):
                obs.update_service(target, s, Service.present)
        if not action.is_scan() and success:
            obs.set_compromised(target)
            for m in self.ads_space:
                if obs.reachable(m):
                    continue
                if self.network.subnets_connected(target[0], m[0]):
                    obs.set_reachable(m)
        elif not action.is_scan() and not success:
            obs.update_service(target, action.service, Service.absent)
        return obs


if __name__ == "__main__":
    unittest.main()
