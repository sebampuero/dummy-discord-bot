import unittest
import os
import shutil

from Utils.FileUtils import FileUtils

class TestFileUtils(unittest.TestCase):

    def setUp(self):
        self.test_files_path = "tests_files"
        os.mkdir(self.test_files_path)
        for i in range(10):
            with open(os.path.join(self.test_files_path, f"text{i}.txt"), "w") as f:
                f.write("Test file containing no useful data")

    def tearDown(self):
        shutil.rmtree(self.test_files_path)

    def test_remove_files_in_dir(self):
        """
        Test that files in a directory are successfully deleted
        """
        path = self.test_files_path
        pattern = "(\w)*\.txt"
        FileUtils.remove_files_in_dir(path, pattern)
        files = os.listdir(path)
        self.assertEqual(0, len(files), f"{path} has still files")

    def test_delete_file(self):
        """
        Test that a file can be successfully deleted
        """
        path = self.test_files_path
        t_file = "text1.txt"
        FileUtils.delete_file(os.path.join(path, t_file))
        files = os.listdir(path)
        self.assertEqual(9, len(files), f"{path} has still all its files")
        self.assertTrue(t_file not in files, f"{t_file} still inside the directory")

if __name__ == '__main__':
    unittest.main()

