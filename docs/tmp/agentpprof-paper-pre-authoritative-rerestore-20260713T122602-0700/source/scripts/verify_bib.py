#!/usr/bin/env python3
"""Verify bib entries against CrossRef, arXiv, and Semantic Scholar.

Usage: python3 verify_bib.py references.bib

For each entry:
1. If it has a DOI → query CrossRef, compare title/authors/year
2. If it has an arxiv ID → query arXiv API, compare title/authors/year
3. If neither → query Semantic Scholar by title, compare
4. Flag mismatches between bib and ground truth
5. Refuse to mark VERIFIED unless all fields match

Exits non-zero if any entry tagged VERIFIED has a mismatch.
Can be used as a pre-commit hook or CI check.
"""

import re
import sys
import time
import json
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from pathlib import Path


def parse_bib_entries(bib_text):
    """Extract bib entries with their comment blocks."""
    entries = []
    lines = bib_text.split('\n')
    i = 0
    while i < len(lines):
        if lines[i].strip().startswith('@') and not lines[i].strip().startswith('%'):
            comment_block = []
            j = i - 1
            while j >= 0 and lines[j].strip().startswith('%'):
                comment_block.insert(0, lines[j])
                j -= 1

            entry_lines = [lines[i]]
            brace_count = lines[i].count('{') - lines[i].count('}')
            k = i + 1
            while k < len(lines) and brace_count > 0:
                entry_lines.append(lines[k])
                brace_count += lines[k].count('{') - lines[k].count('}')
                k += 1

            entry_text = '\n'.join(entry_lines)
            key_match = re.search(r'@\w+\{([^,]+)', entry_text)
            key = key_match.group(1).strip() if key_match else 'unknown'

            verified = 'unknown'
            for cl in comment_block:
                if 'VERIFIED:' in cl:
                    v = cl.split('VERIFIED:')[1].strip()
                    verified = v

            doi = None
            doi_match = re.search(r'doi\s*=\s*\{([^}]+)\}', entry_text, re.I)
            if doi_match:
                doi = doi_match.group(1)

            arxiv_id = None
            url_match = re.search(r'arxiv\.org/abs/(\d+\.\d+)', entry_text)
            if url_match:
                arxiv_id = url_match.group(1)
            if not arxiv_id:
                arxiv_match = re.search(r'arXiv:(\d+\.\d+)', entry_text)
                if arxiv_match:
                    arxiv_id = arxiv_match.group(1)
            if not arxiv_id and doi and 'arXiv' in doi:
                arxiv_match = re.search(r'(\d+\.\d+)', doi)
                if arxiv_match:
                    arxiv_id = arxiv_match.group(1)

            title_match = re.search(r'title\s*=\s*\{(.+?)\}', entry_text, re.DOTALL)
            bib_title = title_match.group(1) if title_match else ''
            bib_title = re.sub(r'[{}\\]', '', bib_title).strip()

            author_match = re.search(r'author\s*=\s*\{(.+?)\}', entry_text, re.DOTALL)
            bib_authors = author_match.group(1) if author_match else ''

            year_match = re.search(r'year\s*=\s*\{?(\d{4})\}?', entry_text)
            bib_year = year_match.group(1) if year_match else ''

            entries.append({
                'key': key,
                'verified': verified,
                'doi': doi,
                'arxiv_id': arxiv_id,
                'bib_title': bib_title,
                'bib_authors': bib_authors,
                'bib_year': bib_year,
                'comment_block': '\n'.join(comment_block),
                'entry_text': entry_text,
                'line': i + 1,
            })
            i = k
        else:
            i += 1
    return entries


def query_arxiv(arxiv_id):
    """Query arXiv API and return metadata."""
    url = f'http://export.arxiv.org/api/query?id_list={arxiv_id}'
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            data = resp.read().decode()
        ns = {'atom': 'http://www.w3.org/2005/Atom'}
        root = ET.fromstring(data)
        entry = root.find('atom:entry', ns)
        if entry is None:
            return None
        title = entry.find('atom:title', ns).text.strip().replace('\n', ' ')
        authors = [a.find('atom:name', ns).text
                    for a in entry.findall('atom:author', ns)]
        published = entry.find('atom:published', ns).text[:4]
        return {'title': title, 'authors': authors, 'year': published}
    except Exception as e:
        return {'error': str(e)}


def query_crossref(doi):
    """Query CrossRef API and return metadata."""
    url = f'https://api.crossref.org/works/{urllib.parse.quote(doi, safe="")}'
    req = urllib.request.Request(url)
    req.add_header('User-Agent', 'verify_bib/1.0 (mailto:check@example.com)')
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
        item = data['message']
        title = item.get('title', [''])[0]
        authors = []
        for a in item.get('author', []):
            name = f"{a.get('family', '')}, {a.get('given', '')}"
            authors.append(name.strip(', '))
        year = str(item.get('published-print', item.get('published-online', {}))
                     .get('date-parts', [['']])[0][0])
        return {'title': title, 'authors': authors, 'year': year}
    except Exception as e:
        return {'error': str(e)}


def query_semantic_scholar(title):
    """Query Semantic Scholar API by title."""
    url = 'https://api.semanticscholar.org/graph/v1/paper/search'
    params = urllib.parse.urlencode({'query': title[:200], 'limit': 1,
                                      'fields': 'title,authors,year'})
    try:
        with urllib.request.urlopen(f'{url}?{params}', timeout=10) as resp:
            data = json.loads(resp.read().decode())
        if not data.get('data'):
            return None
        paper = data['data'][0]
        authors = [a['name'] for a in paper.get('authors', [])]
        return {'title': paper.get('title', ''),
                'authors': authors,
                'year': str(paper.get('year', ''))}
    except Exception as e:
        return {'error': str(e)}


def normalize(s):
    """Normalize string for comparison."""
    return re.sub(r'\s+', ' ', re.sub(r'[^a-z0-9 ]', '', s.lower())).strip()


def compare_titles(bib_title, api_title):
    """Check if titles match (fuzzy). Handles bib stripping braces."""
    nb = normalize(bib_title)
    na = normalize(api_title)
    if nb[:40] == na[:40]:
        return True
    if nb in na or na in nb:
        return True
    return False


def main():
    if len(sys.argv) < 2:
        print('Usage: verify_bib.py <references.bib>')
        sys.exit(1)

    bib_path = Path(sys.argv[1])
    bib_text = bib_path.read_text()
    entries = parse_bib_entries(bib_text)

    print(f'Found {len(entries)} bib entries\n')

    issues = []
    verified_mismatches = []

    for entry in entries:
        key = entry['key']
        if 'STATUS: unused' in entry['comment_block']:
            continue

        print(f'--- {key} (line {entry["line"]}) ---')
        print(f'  Verified: {entry["verified"]}')

        api_result = None

        if entry['arxiv_id']:
            print(f'  Querying arXiv: {entry["arxiv_id"]}')
            api_result = query_arxiv(entry['arxiv_id'])
            time.sleep(0.5)
        elif entry['doi'] and 'arXiv' not in entry.get('doi', ''):
            print(f'  Querying CrossRef: {entry["doi"]}')
            api_result = query_crossref(entry['doi'])
            time.sleep(0.5)

        if not api_result or 'error' in (api_result or {}):
            print(f'  Querying Semantic Scholar by title')
            api_result = query_semantic_scholar(entry['bib_title'])
            time.sleep(1)

        if not api_result or 'error' in (api_result or {}):
            msg = f'  WARN: Could not verify {key} via any API'
            print(msg)
            issues.append(msg)
            continue

        # Compare title
        if not compare_titles(entry['bib_title'], api_result['title']):
            msg = f'  MISMATCH title: bib="{entry["bib_title"][:60]}" api="{api_result["title"][:60]}"'
            print(msg)
            issues.append(f'{key}: {msg}')
        else:
            print(f'  OK title')

        # Compare year
        if entry['bib_year'] and api_result['year'] and entry['bib_year'] != api_result['year']:
            msg = f'  MISMATCH year: bib={entry["bib_year"]} api={api_result["year"]}'
            print(msg)
            issues.append(f'{key}: {msg}')
        else:
            print(f'  OK year')

        # Compare author count
        bib_author_count = len(entry['bib_authors'].split(' and '))
        api_author_count = len(api_result.get('authors', []))
        if 'others' in entry['bib_authors']:
            print(f'  INFO: bib uses "and others", api has {api_author_count} authors')
        elif abs(bib_author_count - api_author_count) > 1:
            msg = f'  MISMATCH author count: bib={bib_author_count} api={api_author_count}'
            print(msg)
            issues.append(f'{key}: {msg}')
            if api_result.get('authors'):
                print(f'  API authors: {", ".join(api_result["authors"][:5])}...')
        else:
            print(f'  OK author count ({bib_author_count} vs {api_author_count})')

        # Check if VERIFIED entry has mismatches
        if entry['verified'] not in ('unknown', 'unverified') and any(
                key in i for i in issues):
            verified_mismatches.append(key)

        print()

    print(f'\n=== Summary ===')
    print(f'Total entries checked: {len([e for e in entries if "STATUS: unused" not in e["comment_block"]])}')
    print(f'Issues found: {len(issues)}')
    for i in issues:
        print(f'  - {i}')

    if verified_mismatches:
        print(f'\nFAIL: {len(verified_mismatches)} VERIFIED entries have mismatches:')
        for k in verified_mismatches:
            print(f'  - {k}')
        sys.exit(1)

    if issues:
        print(f'\nWARN: {len(issues)} issues found but none in VERIFIED entries')
        sys.exit(0)
    else:
        print('\nOK: All entries verified')
        sys.exit(0)


if __name__ == '__main__':
    main()
