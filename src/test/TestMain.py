import unittest
from unittest.mock import patch, MagicMock

from src.main.python.__main__ import ClientHandler


class TestClientHandler(unittest.TestCase):

    def test_handleClient(self):
        mock_conn = MagicMock()
        mock_guiHandler = MagicMock()
        client_handler = ClientHandler(mock_conn, mock_guiHandler)

        with patch.object(mock_conn, 'recv', side_effect=[b'-opn', b'-als', b'', b'-cls']) as mock_recv:
            with patch.object(mock_guiHandler.openGuiSignal, 'emit') as mock_open:
                with patch.object(mock_guiHandler.closeAllSignal, 'emit') as mock_close:
                    with patch.object(mock_guiHandler.addFileSignal, 'emit') as mock_add_file:
                        client_handler.handleClient()

                        mock_open.assert_called_once()
                        mock_add_file.assert_called_once()

                        mock_recv.assert_called_with(4)
                        self.assertEqual(mock_recv.call_count, 4)

                        mock_close.assert_called_once()


if __name__ == '__main__':
    unittest.main()
