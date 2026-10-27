"""Read-only checks for a caller-selected YearLens report; no export is opened."""
import argparse
from collections import Counter
import json
import math
from pathlib import Path
import sys
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

FILES = ('report.md', 'normalized.json', 'stats.json', 'timeline.json', 'audit.json')
MAX_FILE_BYTES = 16 * 1024 * 1024
MAX_TOTAL_BYTES = 48 * 1024 * 1024
SCOPES = ['five_files_readable', 'json_metadata_agrees', 'total_message_and_role_counts']


class CheckFailure(Exception):
    """Only fixed diagnostic codes, never values from a report."""


def fail(code):
    raise CheckFailure(code)


def emit(result):
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))


class QuietParser(argparse.ArgumentParser):
    def error(self, message):
        emit({'status': 'internal_checks_failed', 'error': 'invalid_arguments'})
        self.exit(2)


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            fail('duplicate_json_key')
        result[key] = value
    return result


def invalid_constant(value):
    fail('nonfinite_json_number')


def finite_float(value):
    number = float(value)
    if not math.isfinite(number):
        fail('nonfinite_json_number')
    return number


def natural(value):
    return type(value) is int and value >= 0


def valid_timezone(value):
    if not isinstance(value, str) or not value or len(value) > 128:
        return False
    try:
        ZoneInfo(value)
        return True
    except (ValueError, ZoneInfoNotFoundError):
        return False


def check_report(directory, expected_year=None, expected_timezone=None, expected_branches=None):
    if directory.is_symlink() or not directory.is_dir():
        fail('report_directory_unavailable')
    total = 0
    for name in FILES:
        path = directory / name
        if path.is_symlink() or not path.is_file():
            fail('missing_or_nonregular_report_file')
        size = path.stat().st_size
        if size == 0:
            fail('empty_report_file')
        if size > MAX_FILE_BYTES:
            fail('report_file_over_budget')
        total += size
    if total > MAX_TOTAL_BYTES:
        fail('report_directory_over_budget')
    documents = []
    total_read = 0
    for name in FILES:
        with (directory / name).open('rb') as stream:
            raw = stream.read(MAX_FILE_BYTES + 1)
        total_read += len(raw)
        if len(raw) > MAX_FILE_BYTES or total_read > MAX_TOTAL_BYTES:
            fail('report_read_over_budget')
        try:
            text = raw.decode('utf-8-sig')
        except UnicodeError:
            fail('report_encoding_invalid')
        if name != 'report.md':
            try:
                document = json.loads(text, object_pairs_hook=unique_object,
                                      parse_float=finite_float,
                                      parse_constant=invalid_constant)
            except (ValueError, RecursionError):
                fail('report_json_invalid')
            if not isinstance(document, dict):
                fail('report_json_not_object')
            documents.append(document)
    normalized, stats, timeline, audit = documents
    for document in documents:
        if document.get('schema_version') != 'yearlens/0.1':
            fail('schema_version_unsupported')
        year = document.get('year')
        if type(year) is not int or not 1 <= year <= 9999:
            fail('report_year_invalid')
        if not valid_timezone(document.get('timezone')):
            fail('report_timezone_invalid')
        if document.get('branches') not in ('current', 'all'):
            fail('report_branches_invalid')
    for key in ('year', 'timezone', 'branches'):
        if any(document[key] != normalized[key] for document in documents[1:]):
            fail('report_settings_disagree')
    for key, expected in (('year', expected_year), ('timezone', expected_timezone),
                          ('branches', expected_branches)):
        if expected is not None and normalized[key] != expected:
            fail('report_settings_differ_from_expected')
    messages = normalized.get('messages')
    totals = stats.get('totals')
    counts = audit.get('counts')
    if not isinstance(messages, list) or not isinstance(totals, dict) or not isinstance(counts, dict):
        fail('message_count_structure_invalid')
    roles = Counter()
    for message in messages:
        if not isinstance(message, dict) or message.get('role') not in ('user', 'assistant'):
            fail('normalized_role_invalid')
        roles[message['role']] += 1
    required = [totals.get(key) for key in ('messages', 'user_messages', 'assistant_messages')]
    if not all(natural(value) for value in required):
        fail('message_count_value_invalid')
    included = counts.get('included_messages', 0)
    if not natural(included):
        fail('audit_included_count_invalid')
    if len(messages) != totals['messages'] or len(messages) != included:
        fail('message_totals_disagree')
    if roles['user'] != totals['user_messages'] or roles['assistant'] != totals['assistant_messages']:
        fail('message_role_counts_disagree')
    return {'status': 'internal_checks_passed', 'checks': SCOPES,
            'counts': {'messages': len(messages), 'user': roles['user'], 'assistant': roles['assistant']},
            'expected_settings_supplied': {'year': expected_year is not None,
                                          'timezone': expected_timezone is not None,
                                          'branches': expected_branches is not None},
            'not_checked': ['raw_export_integrity', 'monthly_counts_and_timeline', 'markdown_semantics',
                            'dates_and_branches_against_export', 'permissions', 'real_world_meaning'],
            'real_export_compatibility': 'not_assessed', 'human_review': 'still_required'}


def main():
    parser = QuietParser(prog='yearlens-report-check', description=__doc__)
    parser.add_argument('--report-dir', required=True, type=Path)
    parser.add_argument('--expect-year', type=int)
    parser.add_argument('--expect-timezone')
    parser.add_argument('--expect-branches', choices=('current', 'all'))
    args = parser.parse_args()
    try:
        result = check_report(args.report_dir, args.expect_year, args.expect_timezone, args.expect_branches)
    except CheckFailure as error:
        emit({'status': 'internal_checks_failed', 'error': str(error)})
        return 2
    except (OSError, UnicodeError):
        emit({'status': 'internal_checks_failed', 'error': 'report_io_failed'})
        return 2
    emit(result)
    return 0


if __name__ == '__main__':
    sys.exit(main())
