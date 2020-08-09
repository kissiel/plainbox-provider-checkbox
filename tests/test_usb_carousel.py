import subprocess
import sys
import unittest.mock
import textwrap

import usb_carousel

class TrimLsusbLineTests(unittest.TestCase):
    def test_root_smoke(self):
        orig = ("/:  Bus 02.Port 1: Dev 1, Class=root_hub, "
                "Driver=xhci_hcd/6p, 10000M")
        stuff = usb_carousel.trim_lsusb_line(orig)
        self.assertEqual(
            usb_carousel.trim_lsusb_line(orig),
            "Port 1: Dev 1, Class=root_hub, Driver=xhci_hcd/6p, 10000M"
        )

    def test_device_smoke(self):
        orig = ("|__ Port 5: Dev 2, If 0, Class=Vendor Specific Class, "
                "Driver=, 12M")
        stuff = usb_carousel.trim_lsusb_line(orig)
        self.assertEqual(
            usb_carousel.trim_lsusb_line(orig),
            "Port 5: Dev 2, If 0, Class=Vendor Specific Class, Driver=, 12M"
        )

    def test_invalid_line(self):
        orig = "This is a bad line"
        stuff = usb_carousel.trim_lsusb_line(orig)
        self.assertEqual(usb_carousel.trim_lsusb_line(orig), None)


class ParseLsusbLine(unittest.TestCase):
    def test_smoke(self):
        orig = ("|__ Port 3: Dev 7, If 0, Class=Mass Storage, "
               "Driver=usb-storage, 480M")
        self.assertDictEqual(
            usb_carousel.parse_lsusb_line(orig), {
                'port': '3',
                'dev': '7',
                'if': '0',
                'class': 'Mass Storage',
                'driver': 'usb-storage',
                'speed': '480M'
            })

    def test_missing_driver(self):
        orig = "Port 5: Dev 2, If 0, Class=Vendor Specific Class, Driver=, 12M"
        self.assertDictEqual(
            usb_carousel.parse_lsusb_line(orig), {
                'port': '5',
                'dev': '2',
                'if': '0',
                'class': 'Vendor Specific Class',
                'driver': 'Unknown',
                'speed': '12M'
            })

    def test_empty_record(self):
        self.assertDictEqual(
            usb_carousel.parse_lsusb_line(''), {
                'port': 'Unknown',
                'dev': 'Unknown',
                'if': 'Unknown',
                'class': 'Unknown',
                'driver': 'Unknown',
                'speed': 'Unknown'
            })



class UsbCarouselTests(unittest.TestCase):
    @unittest.mock.patch('subprocess.check_output')
    def test_Scraper_detects_insertion(self, mock_check_output):
        mock_check_output.return_value = NOTHING_INSERTED
        scraper = usb_carousel.LsusbScraper()
        mock_check_output.assert_called()
        mock_check_output.return_value = ONE_DEVICE_INSERTED
        new_stuff = scraper.whats_new()
        self.assertEqual(new_stuff,
            [("Port 3: Dev 7, If 0, Class=Mass Storage, "
            "Driver=usb-storage, 480M")])

    @unittest.mock.patch('subprocess.check_output')
    def test_scraper_sees_no_change(self, mock_check_output):
        mock_check_output.return_value = NOTHING_INSERTED
        scraper = usb_carousel.LsusbScraper()
        mock_check_output.assert_called()
        self.assertEqual(scraper.whats_new(), [])


NOTHING_INSERTED = textwrap.dedent("""
    /:  Bus 02.Port 1: Dev 1, Class=root_hub, Driver=xhci_hcd/6p, 10000M
    /:  Bus 01.Port 1: Dev 1, Class=root_hub, Driver=xhci_hcd/12p, 480M
        |__ Port 5: Dev 2, If 0, Class=Vendor Specific Class, Driver=, 12M
        |__ Port 6: Dev 3, If 0, Class=Video, Driver=uvcvideo, 480M
        |__ Port 6: Dev 3, If 1, Class=Video, Driver=uvcvideo, 480M
        |__ Port 10: Dev 4, If 0, Class=Wireless, Driver=btusb, 12M
        |__ Port 10: Dev 4, If 1, Class=Wireless, Driver=btusb, 12M
    """).encode(sys.stdout.encoding)

ONE_DEVICE_INSERTED = textwrap.dedent("""
    /:  Bus 02.Port 1: Dev 1, Class=root_hub, Driver=xhci_hcd/6p, 10000M
    /:  Bus 01.Port 1: Dev 1, Class=root_hub, Driver=xhci_hcd/12p, 480M
        |__ Port 3: Dev 7, If 0, Class=Mass Storage, Driver=usb-storage, 480M
        |__ Port 5: Dev 2, If 0, Class=Vendor Specific Class, Driver=, 12M
        |__ Port 6: Dev 3, If 0, Class=Video, Driver=uvcvideo, 480M
        |__ Port 6: Dev 3, If 1, Class=Video, Driver=uvcvideo, 480M
        |__ Port 10: Dev 4, If 0, Class=Wireless, Driver=btusb, 12M
        |__ Port 10: Dev 4, If 1, Class=Wireless, Driver=btusb, 12M
    """).encode(sys.stdout.encoding)
