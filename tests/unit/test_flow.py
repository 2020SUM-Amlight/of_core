"""Tests for high-level Flow of OpenFlow 1.0 and 1.3."""
from unittest import TestCase
from unittest.mock import MagicMock, patch


from kytos.lib.helpers import get_switch_mock, get_connection_mock
from napps.kytos.of_core.v0x01.flow import Flow as Flow01
from napps.kytos.of_core.v0x04.flow import Flow as Flow04


class TestFlowFactory(TestCase):
    """Test the FlowFactory class."""

    def setUp(self):
        """Execute steps before each tests.
        Set the server_name_url from kytos/of_core
        """
        self.switch_v0x01 = get_switch_mock("00:00:00:00:00:00:00:01")
        self.switch_v0x04 = get_switch_mock("00:00:00:00:00:00:00:02")
        self.switch_v0x01.connection = get_connection_mock(
            0x01, get_switch_mock("00:00:00:00:00:00:00:03"))
        self.switch_v0x04.connection = get_connection_mock(
            0x04, get_switch_mock("00:00:00:00:00:00:00:04"))

        patch('kytos.core.helpers.run_on_thread', lambda x: x).start()
        # pylint: disable=bad-option-value
        from napps.kytos.of_core.flow import FlowFactory
        self.addCleanup(patch.stopall)

        self.napp = FlowFactory()

    @patch('napps.kytos.of_core.flow.v0x01')
    @patch('napps.kytos.of_core.flow.v0x04')
    def test_from_of_flow_stats(self, *args):
        """Test from_of_flow_stats."""
        (mock_flow_v0x04, mock_flow_v0x01) = args
        mock_stats = MagicMock()

        self.napp.from_of_flow_stats(mock_stats, self.switch_v0x01)
        mock_flow_v0x01.flow.Flow.from_of_flow_stats.assert_called()

        self.napp.from_of_flow_stats(mock_stats, self.switch_v0x04)
        mock_flow_v0x04.flow.Flow.from_of_flow_stats.assert_called()


class TestFlow(TestCase):
    """Test OF flow abstraction."""

    mock_switch = get_switch_mock("00:00:00:00:00:00:00:01")
    mock_switch.id = "00:00:00:00:00:00:00:01"
    expected = {'id': 'ca11e386e4bb5b0301b775c4640573e7',
                'switch': mock_switch.id,
                'table_id': 1,
                'match': {
                    'dl_src': '11:22:33:44:55:66'
                },
                'priority': 2,
                'idle_timeout': 3,
                'hard_timeout': 4,
                'cookie': 5,
                'actions': [
                    {'action_type': 'set_vlan',
                     'vlan_id': 6}],
                'stats': {}}

    def test_flow_mod(self):
        """Convert a dict to flow and vice-versa."""
        for flow_class in Flow01, Flow04:
            with self.subTest(flow_class=flow_class):
                flow = flow_class.from_dict(self.expected, self.mock_switch)
                actual = flow.as_dict()
                self.assertDictEqual(self.expected, actual)

    @patch('napps.kytos.of_core.flow.FlowBase._as_of_flow_mod')
    def test_of_flow_mod(self, mock_flow_mod):
        """Test convertion from Flow to OFFlow."""

        for flow_class in Flow01, Flow04:
            with self.subTest(flow_class=flow_class):
                flow = flow_class.from_dict(self.expected, self.mock_switch)
                flow.as_of_add_flow_mod()
                mock_flow_mod.assert_called()

                flow.as_of_delete_flow_mod()
                mock_flow_mod.assert_called()

    # pylint: disable = protected-access
    def test_as_of_flow_mod(self):
        """Test _as_of_flow_mod."""
        mock_command = MagicMock()
        for flow_class in Flow01, Flow04:
            with self.subTest(flow_class=flow_class):
                flow_mod = flow_class.from_dict(self.expected,
                                                self.mock_switch)
                response = flow_mod._as_of_flow_mod(mock_command)
                self.assertEqual(response.cookie, self.expected['cookie'])
                self.assertEqual(response.idle_timeout,
                                 self.expected['idle_timeout'])
                self.assertEqual(response.hard_timeout,
                                 self.expected['hard_timeout'])
