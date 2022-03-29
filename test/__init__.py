from jupyter_kernel_test import KernelTests
import utils
from random import random
import unittest


class SardanaKernelTest(KernelTests):
    # As define in sardana_kernel/kernel.json
    kernel_name = "sardana_kernel"
    language_name = "python"

    def test_sar_demo(self):
        """
        Creates a basic demo
        """
        self.flush_channels()

        self.execute_helper(code="sar_demo")

    def test_sardana_lsm(self):
        """
        Make sure the macro `lsm` prints the list of motors
        """
        self.flush_channels()

        _, output_msgs = self.execute_helper(code="lsm")

        def any_motor():
            """
            Returns True if any motor is found, or False otherwise
            """
            for mot_n in range(4, len(output_msgs)):
                mot = output_msgs[mot_n]
                if "mot" in str(mot["content"]["text"]):
                    return True
            return False

        self.assertTrue(any_motor())

    def test_sardana_env(self):
        """
        Make sure that the macros `senv` and `genv` work
        """
        self.flush_channels()

        number = str(random())
        test_key = "test_sardana_jupyter_val"

        self.execute_helper(code="senv {} {}".format(test_key, number))

        _, output_msgs = self.execute_helper(
            code="genv {} {}".format(test_key, number)
        )

        result = output_msgs[4]["content"]["text"]
        result_number = result.split("=")[1].strip()

        self.assertEqual(number, result_number)

    def test_sardana_error(self):
        """
        Make sure an error is printed when there is one
        """
        self.flush_channels()

        _, output_msgs = self.execute_helper(code="HelloStranger")

        self.assertEqual(output_msgs[0]["header"]["msg_type"], "error")
        self.assertEqual(
            output_msgs[0]["content"]["evalue"],
            "name 'HelloStranger' is not defined",
        )


if __name__ == "__main__":
    utils.main()
    unittest.main()
