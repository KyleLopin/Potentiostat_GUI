
# standard libraries
import unittest
from unittest import mock
from unittest.mock import patch
# local files
from app import amp_gui


class TestUSBHandler(unittest.TestCase):
    @patch('builtins.print')
    def build_up(self, mock_print):
        root = amp_gui.ElectroChemGUI()
        return root, mock_print

    def test_cv_send_params(self):
        # done with app as a hack, fix this when more time
        app, mp = self.build_up()  # type: amp_gui.ElectroChemGUI
        for call in mp.mock_calls:
            print(call)
        app.cv.device.send_cv_parameters()
        app.cv.settings.use_svw = True
        with mock.patch('builtins.print') as test_printer:
            # app.cv.run_button.invoke()
            app.cv.device.send_cv_parameters()

        print('=======')
        for call in test_printer.mock_calls:
            print(call)


if __name__ == "__main__":
    unittest.main()
