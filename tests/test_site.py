"""Offline checks: python3 -m unittest discover -s tests -v."""
import csv
from html.parser import HTMLParser
from pathlib import Path
import unittest
from urllib.parse import urlsplit, unquote
ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / 'site'
class Document(HTMLParser):
    def __init__(self, text):
        super().__init__(); self.links=[]; self.rows=[]; self.ids=[]; self.feed(text)
    def handle_starttag(self, tag, attrs):
        a=dict(attrs)
        if 'id' in a: self.ids.append(a['id'])
        if tag=='a' and 'href' in a: self.links.append(a)
        if tag=='tr' and 'data-source' in a: self.rows.append(a)
class SiteTests(unittest.TestCase):
    def test_dataset_unchanged_in_export(self):
        for name in ('benchmarks.csv','boards.csv'):
            self.assertEqual((ROOT/'data'/name).read_bytes(),(SITE/'data'/name).read_bytes())
    def test_source_labels_cover_dataset(self):
        rows=list(csv.DictReader((ROOT/'data/benchmarks.csv').read_text().splitlines()))
        doc=Document((SITE/'index.html').read_text())
        self.assertEqual(len(rows),242);self.assertEqual(len(doc.rows),len(rows))
        self.assertEqual(sorted(r['source_type'] for r in rows),sorted(r['data-source'] for r in doc.rows))
        for r in doc.rows:self.assertTrue(r['data-model'])
    def test_all_internal_links_resolve(self):
        for path in SITE.rglob('*.html'):
            for a in Document(path.read_text()).links:
                u=urlsplit(a['href'])
                if u.scheme or u.netloc or not u.path:continue
                target=(SITE/unquote(u.path.lstrip('/'))) if u.path.startswith('/') else path.parent/unquote(u.path)
                if target.is_dir(): target=target/'index.html'
                self.assertTrue(target.exists(),f'{path}: {a["href"]}')
    def test_all_benchmark_tables_have_conditions(self):
        for path in SITE.rglob('*.html'):
            text=path.read_text(); n=len(Document(text).rows)
            self.assertEqual(text.count('class="run-details"'),n,str(path))
            self.assertEqual(text.count('class="evidence-label"'),n,str(path))
    def test_honest_copy_and_form_privacy(self):
        home=(SITE/'index.html').read_text()
        self.assertIn('not typical performance',home)
        submit=(SITE/'submit/index.html').read_text()
        self.assertIn('will be public in the GitHub issue',submit)
        self.assertNotIn('newsletter address',submit)
        for id in ('f-model','f-source'):self.assertIn(id,Document(home).ids)
if __name__=='__main__':unittest.main()
