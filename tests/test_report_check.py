"""Synthetic CLI acceptance cases for the independent read-only report checker."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
CHECKER = ROOT / 'yearlens/scripts/check_report.py'
GENERATOR = ROOT / 'yearlens/scripts/yearlens.py'
FILES = ('report.md', 'normalized.json', 'stats.json', 'timeline.json', 'audit.json')
MARKER = 'SYNTHETIC_MARKER_DO_NOT_ECHO'


def digest(path):
    value = hashlib.sha256()
    with path.open('rb') as stream:
        for data in iter(lambda: stream.read(1024 * 1024), b''):
            value.update(data)
    return value.hexdigest()


def fingerprints(folder):
    if folder.is_symlink():
        return {'directory_symlink': os.readlink(folder)}
    if not folder.exists():
        return {'missing': True}
    values = {}
    for path in folder.iterdir():
        if path.is_symlink():
            values[path.name] = {'symlink': os.readlink(path)}
        elif path.is_file():
            values[path.name] = {'bytes': path.stat().st_size, 'sha256': digest(path)}
        else:
            values[path.name] = {'mode': path.lstat().st_mode}
    return values


class ReportCheckTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.workspace = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.workspace.cleanup)
        cls.folder = Path(cls.workspace.name)
        cls.references = {}
        for name, input_path in [('reference', ROOT/'examples/conversations.synthetic.json'),
                                 ('empty', cls.folder/'empty.synthetic.json'),
                                 ('many', cls.folder/'many.synthetic.json')]:
            if name == 'empty':
                input_path.write_text('[]\n', encoding='utf-8')
            elif name == 'many':
                nodes = {}
                for i in range(1000):
                    node = f'synthetic-{i}'
                    nodes[node] = {'parent': f'synthetic-{i-1}' if i else None,
                                   'message': {'id': node, 'author': {'role': 'assistant' if i % 2 else 'user'},
                                               'create_time': '2025-06-03T08:00:00Z',
                                               'content': {'content_type': 'text', 'parts': ['Synthetic example']}}}
                input_path.write_text(json.dumps([{'id': 'synthetic-many', 'title': 'Synthetic test',
                                                   'mapping': nodes, 'current_node': 'synthetic-999'}]), encoding='utf-8')
            output = cls.folder/name
            before = digest(input_path)
            result = subprocess.run([sys.executable, '-B', str(GENERATOR), str(input_path), '--year', '2025',
                                     '--timezone', 'Asia/Bangkok', '--output', str(output)],
                                    capture_output=True, text=True, timeout=30)
            if result.returncode != 0 or digest(input_path) != before:
                raise AssertionError('Synthetic generator setup failed')
            cls.references[name] = output

    def setUp(self):
        self.case_workspace = tempfile.TemporaryDirectory()
        self.addCleanup(self.case_workspace.cleanup)
        self.case = Path(self.case_workspace.name)/'report'
        shutil.copytree(self.references['reference'], self.case)

    def edit(self, filename, action):
        path = self.case/filename
        data = json.loads(path.read_text(encoding='utf-8'))
        action(data)
        path.write_text(json.dumps(data, ensure_ascii=False), encoding='utf-8')

    def use(self, name):
        shutil.rmtree(self.case)
        shutil.copytree(self.references[name], self.case)

    def check(self, error=None, messages=None, extra=()):
        before = fingerprints(self.case)
        result = subprocess.run([sys.executable, '-I', '-B', str(CHECKER), '--report-dir', str(self.case), *extra],
                                capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 2 if error else 0)
        self.assertEqual(result.stderr, '')
        self.assertNotIn(MARKER, result.stdout)
        self.assertNotIn(str(self.case), result.stdout)
        data = json.loads(result.stdout)
        if error:
            self.assertEqual(data['error'], error)
            self.assertEqual(data['status'], 'internal_checks_failed')
        else:
            self.assertEqual(data['status'], 'internal_checks_passed')
            self.assertEqual(data['real_export_compatibility'], 'not_assessed')
            self.assertEqual(data['human_review'], 'still_required')
            if messages is not None:
                self.assertEqual(data['counts']['messages'], messages)
        self.assertEqual(fingerprints(self.case), before)

    def test_valid_reference(self):
        self.check(messages=15, extra=('--expect-year', '2025', '--expect-timezone', 'Asia/Bangkok',
                                       '--expect-branches', 'current'))

    def test_valid_thousand(self):
        self.use('many'); self.check(messages=1000)

    def test_missing_file(self):
        (self.case/'report.md').unlink(); self.check('missing_or_nonregular_report_file')

    def test_totals_disagree(self):
        self.edit('stats.json', lambda d: d['totals'].update(messages=99)); self.check('message_totals_disagree')

    def test_roles_disagree(self):
        self.edit('stats.json', lambda d: d['totals'].update(user_messages=9)); self.check('message_role_counts_disagree')

    def test_settings_disagree(self):
        self.edit('audit.json', lambda d: d.update(timezone='UTC')); self.check('report_settings_disagree')

    def test_expected_year(self):
        self.check('report_settings_differ_from_expected', extra=('--expect-year', '2026'))

    def test_malformed_json(self):
        (self.case/'stats.json').write_text('{"'+MARKER+'":', encoding='utf-8'); self.check('report_json_invalid')

    def test_duplicate_key(self):
        path=self.case/'audit.json'; text=path.read_text(encoding='utf-8')
        path.write_text('{"year":2025,'+text[1:], encoding='utf-8'); self.check('duplicate_json_key')

    def test_bool_count(self):
        self.edit('stats.json', lambda d: d['totals'].update(messages=True)); self.check('message_count_value_invalid')

    def numeric_case(self, number, error=None):
        path=self.case/'stats.json'; text=path.read_text(encoding='utf-8').rstrip()
        path.write_text(text[:-1]+',"'+MARKER+'":'+number+'}', encoding='utf-8'); self.check(error)

    def test_nan(self):
        self.numeric_case('NaN', 'nonfinite_json_number')

    def make_link(self, path, target):
        try:
            path.symlink_to(target, target_is_directory=target.is_dir())
        except (OSError, NotImplementedError):
            self.skipTest('Symlink creation unavailable on this platform')

    def test_file_symlink(self):
        (self.case/'stats.json').unlink(); self.make_link(self.case/'stats.json', self.references['reference']/'stats.json')
        self.check('missing_or_nonregular_report_file')

    def test_file_over_budget(self):
        with (self.case/'report.md').open('wb') as stream:
            stream.truncate(16*1024*1024+1)
        self.check('report_file_over_budget')

    def test_bad_arguments(self):
        self.check('invalid_arguments', extra=('--unknown', MARKER))

    def test_valid_empty(self):
        self.use('empty'); self.check(messages=0)

    def test_explicit_zero(self):
        self.use('empty'); self.edit('audit.json', lambda d: d['counts'].update(included_messages=0)); self.check(messages=0)

    def test_missing_included_nonempty(self):
        self.edit('audit.json', lambda d: d['counts'].pop('included_messages')); self.check('message_totals_disagree')

    def test_top_array(self):
        (self.case/'stats.json').write_text('[]', encoding='utf-8'); self.check('report_json_not_object')

    def test_top_null(self):
        (self.case/'audit.json').write_text('null', encoding='utf-8'); self.check('report_json_not_object')

    def test_missing_messages(self):
        self.edit('normalized.json', lambda d: d.pop('messages')); self.check('message_count_structure_invalid')

    def test_totals_array(self):
        self.edit('stats.json', lambda d: d.update(totals=[])); self.check('message_count_structure_invalid')

    def test_counts_null(self):
        self.edit('audit.json', lambda d: d.update(counts=None)); self.check('message_count_structure_invalid')

    def test_message_null(self):
        self.edit('normalized.json', lambda d: d['messages'].__setitem__(0,None)); self.check('normalized_role_invalid')

    def test_role_array(self):
        self.edit('normalized.json', lambda d: d['messages'][0].update(role=[])); self.check('normalized_role_invalid')

    def test_year_bool(self):
        self.edit('timeline.json', lambda d: d.update(year=True)); self.check('report_year_invalid')

    def test_timezone_path(self):
        self.edit('audit.json', lambda d: d.update(timezone='../'+MARKER)); self.check('report_timezone_invalid')

    def test_branches_object(self):
        self.edit('normalized.json', lambda d: d.update(branches={MARKER:1})); self.check('report_branches_invalid')

    def test_audit_negative(self):
        self.edit('audit.json', lambda d: d['counts'].update(included_messages=-1)); self.check('audit_included_count_invalid')

    def test_positive_exponent_overflow(self):
        self.numeric_case('1e10000', 'nonfinite_json_number')

    def test_negative_exponent_overflow(self):
        self.numeric_case('-1e10000', 'nonfinite_json_number')

    def test_finite_exponent(self):
        self.numeric_case('1.25e2')

    def test_invalid_utf8(self):
        (self.case/'report.md').write_bytes(b'\xff'+MARKER.encode()); self.check('report_encoding_invalid')

    def test_zero_file(self):
        (self.case/'report.md').write_bytes(b''); self.check('empty_report_file')

    def test_missing_directory(self):
        shutil.rmtree(self.case); self.check('report_directory_unavailable')

    def test_directory_symlink(self):
        shutil.rmtree(self.case); self.make_link(self.case, self.references['reference']); self.check('report_directory_unavailable')

    @unittest.skipUnless(hasattr(os,'mkfifo'), 'FIFO creation unavailable on this platform')
    def test_fifo(self):
        (self.case/'stats.json').unlink(); os.mkfifo(self.case/'stats.json'); self.check('missing_or_nonregular_report_file')

    def test_extra_file_ignored(self):
        (self.case/'extra.json').write_bytes(b'\xff'+MARKER.encode()); self.check(messages=15)

    def pad_total_budget(self):
        for name in FILES:
            limit=16*1024*1024 if name=='report.md' else 8*1024*1024
            path=self.case/name
            with path.open('ab') as stream:
                stream.write(b' '*(limit-path.stat().st_size))
        self.assertEqual(sum((self.case/name).stat().st_size for name in FILES),48*1024*1024)

    def test_exact_total_budget(self):
        self.pad_total_budget(); self.check(messages=15)

    def test_over_total_budget(self):
        self.pad_total_budget()
        with (self.case/'audit.json').open('ab') as stream:
            stream.write(b' ')
        self.check('report_directory_over_budget')


if __name__ == '__main__':
    unittest.main()
