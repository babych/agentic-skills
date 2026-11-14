import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import code_memory as cm


class TestCodeMemory(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def write_file(self, rel_path, content):
        full = self.root / rel_path
        full.parent.mkdir(parents=True, exist_ok=True)
        full.write_text(content, encoding="utf-8")
        return full

    def test_class_does_not_swallow_nested_methods(self):
        cs_code = """
namespace App.Services;

public class OrderService
{
    private readonly IRepo _repo;

    public int CountOrders() => _repo.Count();

    public async Task<bool> CancelOrderAsync(
        int orderId,
        string reason)
    {
        var order = await _repo.GetAsync(orderId);
        if (order == null) return false;
        order.Status = "Cancelled";
        return true;
    }

    public void ResetCache() {}
}
"""
        path = self.write_file("src/OrderService.cs", cs_code)
        chunks = cm.chunk_single_file(path, "src/OrderService.cs")
        symbols_per_chunk = [set(c["symbols"]) for c in chunks]

        self.assertTrue(any("cancelorderasync" in s for s in symbols_per_chunk))
        self.assertTrue(any("countorders" in s for s in symbols_per_chunk))
        self.assertTrue(any("resetcache" in s for s in symbols_per_chunk))

        cancel_chunk = next(c for c in chunks if "cancelorderasync" in c["symbols"])
        self.assertLessEqual(cancel_chunk["end_line"] - cancel_chunk["start_line"], 12)

    def test_typescript_arrow_and_template_literal_braces(self):
        ts_code = """
export interface TokenPayload {
    sub: string;
    exp: number;
}

export const formatExpiryBanner = (user: string, mins: number): string => {
    const msg = `User { ${user} } expires in { ${mins} } minutes`;
    if (mins <= 5) {
        return msg.toUpperCase();
    }
    return msg;
};

export class SessionHelper {
    isExpired(exp: number) {
        return Date.now() >= exp * 1000;
    }
}
"""
        path = self.write_file("src/session.ts", ts_code)
        chunks = cm.chunk_single_file(path, "src/session.ts")
        banner = next(c for c in chunks if "formatexpirybanner" in c["symbols"])
        self.assertEqual(banner["end_line"], 13)
        self.assertTrue(any("isexpired" in c["symbols"] for c in chunks))

    def test_python_multiline_signature_and_decorators(self):
        py_code = """
@router.post(
    "/tokens/refresh",
    status_code=200,
)
async def refresh_user_token(
    refresh_token: str,
    strict: bool = True,
) -> dict:
    if not refresh_token:
        return {"ok": False}
    return {"ok": True}

def helper_noop(): return 42
"""
        path = self.write_file("app/auth.py", py_code)
        chunks = cm.chunk_single_file(path, "app/auth.py")
        refresh_chunk = next(c for c in chunks if "refresh_user_token" in c["symbols"])
        self.assertEqual(refresh_chunk["start_line"], 2)
        self.assertEqual(refresh_chunk["end_line"], 12)

    def test_nested_local_function_does_not_truncate_outer_method(self):
        cs_code = """
public class Pipeline
{
    public int RunPipeline(int input)
    {
        int step1 = input + 1;
        int step2 = step1 * 2;
        int step3 = step2 + 3;
        int step4 = step3 * 4;
        int step5 = step4 + 5;
        int step6 = step5 * 6;
        int LocalAdjust(int v)
        {
            return v - 1;
        }
        return LocalAdjust(step6);
    }
}
"""
        path = self.write_file("src/Pipeline.cs", cs_code)
        chunks = cm.chunk_single_file(path, "src/Pipeline.cs")
        run_chunk = next(c for c in chunks if "runpipeline" in c["symbols"])
        self.assertEqual(run_chunk["end_line"], 18)

    def test_git_exclude_created_on_fresh_git_repo(self):
        (self.root / ".git").mkdir()
        self.write_file("main.py", "def ping():\n    return 'pong'\n")
        cm.build_or_update_index(self.root, force_full=True, quiet=True)
        exclude_file = self.root / ".git" / "info" / "exclude"
        self.assertTrue(exclude_file.exists())
        self.assertIn(".code_index.json", exclude_file.read_text(encoding="utf-8"))

    def test_word_boundary_refs_and_json_search(self):
        self.write_file("src/user.ts", "export function getUserById(id: string) {\n    const width = 100;\n    return id;\n}\n")
        buf = io.StringIO()
        with redirect_stdout(buf):
            cm.search_references("id", root_dir=self.root)
        out = buf.getvalue()
        self.assertIn("getUserById", out)
        self.assertNotIn("width", out)

        jbuf = io.StringIO()
        with redirect_stdout(jbuf):
            cm.search("getUserById", root_dir=self.root, as_json=True)
        payload = json.loads(jbuf.getvalue())
        self.assertEqual(len(payload["results"]), 1)
        self.assertEqual(payload["results"][0]["lines"][0]["line"], 1)


if __name__ == "__main__":
    unittest.main()
