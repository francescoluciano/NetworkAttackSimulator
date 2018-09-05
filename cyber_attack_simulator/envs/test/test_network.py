import unittest
import numpy as np
from cyber_attack_simulator.envs.network import Network
from cyber_attack_simulator.envs.network import min_subnet_depth
from cyber_attack_simulator.envs.loader import R_SENSITIVE
from cyber_attack_simulator.envs.loader import R_USER
from cyber_attack_simulator.envs.loader import generate_config
from cyber_attack_simulator.envs.action import Action


class NetworkTestCase(unittest.TestCase):

    def setUp(self):
        self.M = 3
        self.S = 3
        self.config = generate_config(self.M, self.S)
        self.network = Network(self.config)

    def find_exploit(self, network, address, valid):
        services = network.machines[address]._services
        for i in range(len(services)):
            if services[i] == valid:
                return i

    def get_network(self, nM, nS):
        config = generate_config(nM, nS)
        network = Network(config)
        return network

    def test_generate_network_small(self):
        M = 3
        S = 3
        network = self.get_network(M, S)
        subnets = network.subnets
        self.assertEqual(len(subnets), 3)
        for s in range(3):
            self.assertEqual(subnets[s], 1)
            self.assertTrue(network.machines[(s, 0)].address, (s, 0))

    def test_generate_network_consistency(self):
        M = [3, 6]
        S = [3, 6]
        results1 = []
        machines1 = []
        for m in M:
            for s in S:
                network = self.get_network(m, s)
                results1.append(network.subnets)
                machines1.append(network.machines)
        results2 = []
        machines2 = []
        for m in M:
            for s in S:
                network = self.get_network(m, s)
                results2.append(network.subnets)
                machines2.append(network.machines)
        self.assertEqual(results1, results2)
        self.assertEqual(machines1, machines2)

    def test_successful_exploit(self):
        rewards = [0, R_SENSITIVE, R_USER]
        for i in range(3):
            subnet = i
            e = self.find_exploit(self.network, (subnet, 0), True)
            exploit = Action((subnet, 0), "exploit", e)
            outcome, reward, services = self.network.perform_action(exploit)
            self.assertTrue(outcome)
            self.assertEqual(reward, rewards[i])

    def test_unsuccessful_exploit(self):
        rewards = [0, 0, 0]
        exp_services = np.asarray([])
        for i in range(3):
            subnet = i
            e = self.find_exploit(self.network, (subnet, 0), False)
            exploit = Action((subnet, 0), "exploit", e)
            outcome, reward, services = self.network.perform_action(exploit)
            self.assertFalse(outcome)
            self.assertEqual(reward, rewards[i])
            self.assertTrue((services == exp_services).all())

    def test_scan(self):
        rewards = [0, 0, 0]
        for i in range(3):
            subnet = i
            exp_services = self.network.machines[(subnet, 0)]._services
            exploit = Action((subnet, 0), "scan", None)
            outcome, reward, services = self.network.perform_action(exploit)
            self.assertTrue(outcome)
            self.assertEqual(reward, rewards[i])
            self.assertTrue((services == exp_services).all())

    def test_invalid_action(self):
        # invalid subnet
        exploit = Action((3, 0), "scan", None)
        with self.assertRaises(AssertionError):
            self.network.perform_action(exploit)
        # invalid machine ID
        exploit = Action((0, 2), "scan", None)
        with self.assertRaises(AssertionError):
            self.network.perform_action(exploit)
        # invalid service
        exploit = Action((0, 0), "exploit", self.S + 1)
        with self.assertRaises(AssertionError):
            self.network.perform_action(exploit)

    def test_topology(self):
        m = 20
        s = 1
        network = self.get_network(m, s)
        # test public explosure of subnet 0
        self.assertTrue(network.subnet_exposed(0))
        # test full connectivity of first 3 subnets
        for i in range(3):
            for j in range(3):
                self.assertTrue(network.subnets_connected(i, j))

        # test exposed and sensitive subnets not connected to sub use subnets
        for i in range(2):
            for j in range(3, 6):
                self.assertFalse(network.subnets_connected(i, j))
                self.assertFalse(network.subnets_connected(j, i))

        # test user subnet connections
        # 2 & 3 connected
        self.assertTrue(network.subnets_connected(2, 3))
        self.assertTrue(network.subnets_connected(3, 2))
        self.assertTrue(network.subnets_connected(3, 3))
        # 2 & 4 connected
        self.assertTrue(network.subnets_connected(2, 4))
        self.assertTrue(network.subnets_connected(4, 2))
        self.assertTrue(network.subnets_connected(4, 4))
        # 3 & 4 not connected
        self.assertFalse(network.subnets_connected(3, 4))
        self.assertFalse(network.subnets_connected(4, 3))
        # 3 & 5 connected
        self.assertTrue(network.subnets_connected(3, 5))
        self.assertTrue(network.subnets_connected(5, 3))
        self.assertTrue(network.subnets_connected(5, 5))
        # 4 & 5 not connected
        self.assertFalse(network.subnets_connected(4, 5))
        self.assertFalse(network.subnets_connected(5, 4))

    def min_subnet_depth(self):
        topology = [[1, 1, 1, 1, 0, 0, 0, 0],
                    [0, 1, 1, 1, 0, 0, 0, 0],
                    [0, 1, 1, 1, 1, 0, 0, 1],
                    [0, 0, 0, 1, 1, 1, 1, 1],
                    [1, 0, 0, 0, 1, 1, 0, 0],
                    [0, 0, 0, 0, 1, 0, 1, 0],
                    [0, 0, 0, 1, 0, 0, 0, 1]]

        expected_depths = [0, 1, 1, 1, 0, 2, 2]
        actual_depths = min_subnet_depth(topology)
        self.assertEqual(actual_depths, expected_depths)

    def test_print(self):
        m = 20
        s = 1
        network = self.get_network(m, s)
        print()
        print(network)


if __name__ == "__main__":
    unittest.main()
