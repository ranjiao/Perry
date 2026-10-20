"""Native anchor invariants after the second, legacy resolver retires.

Replaces migration-time agreement with bin/lib. All anchors are temporary;
no project registers or retired fixture corpus are used.
"""
import unittest
from support import mkdtemp
from perry_kernel.errors import KernelError
from perry_kernel.paths import resolve_anchor


class TestAnchorContract(unittest.TestCase):
    def setUp(self):
        self.tmp = mkdtemp(self)
        self.outer = self.project(self.tmp / "outer")
        self.inner = self.project(self.outer / "packages" / "inner")
        self.deep = self.inner / "src" / "nested"
        self.deep.mkdir(parents=True)
        self.elsewhere = self.tmp / "elsewhere"
        self.elsewhere.mkdir()

    def project(self, path):
        (path / ".perry").mkdir(parents=True)
        return path.resolve()

    def test_flag_then_environment_then_nearest_walk(self):
        for flag, env, expected in [
            (str(self.outer), {"PERRY_PROJECT": str(self.inner)}, self.outer),
            (None, {"PERRY_PROJECT": str(self.outer)}, self.outer),
            (None, {}, self.inner),
            (None, {"PERRY_PROJECT": ""}, self.inner),
            ("../..", {}, self.inner),
        ]:
            with self.subTest(flag=flag, env=env):
                self.assertEqual(resolve_anchor(flag, env, self.deep), expected)

    def test_empty_anchor_and_symlinks(self):
        link = self.tmp / "link"
        link.symlink_to(self.inner, target_is_directory=True)
        self.assertEqual(resolve_anchor(str(link), {}, self.elsewhere), self.inner)
        self.assertEqual(resolve_anchor(None, {}, link / "src"), self.inner)

    def test_missing_anchor_refuses_without_fallback(self):
        for flag, env, cwd in [
            (None, {}, self.elsewhere),
            (str(self.elsewhere), {}, self.outer),
            (None, {"PERRY_PROJECT": str(self.elsewhere)}, self.outer),
        ]:
            with self.subTest(flag=flag, env=env):
                with self.assertRaises(KernelError) as refused:
                    resolve_anchor(flag, env, cwd)
                self.assertEqual(refused.exception.code, "anchor_not_found")


if __name__ == "__main__":
    unittest.main()
