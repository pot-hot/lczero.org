#!/usr/bin/env python3

import click
import os
import os.path
import re
import json

SCRIPT_DIR = os.path.dirname(__file__)
FILELIST = os.path.join(SCRIPT_DIR, 'wikifiles.txt')
CONTENT_DIR = os.path.realpath(os.path.join(SCRIPT_DIR, '../content'))
WIKI_PATH = os.path.join(SCRIPT_DIR, 'wiki')
DESTINATION_DIR = os.path.join(CONTENT_DIR, 'dev/wiki')


class WikiUpdater:
    def __init__(self, quiet):
        self.quiet = quiet

    def Info(self, text):
        if not self.quiet:
            click.secho(text, fg='yellow')

    def ReadFilelist(self):
        f = open(FILELIST)
        with open(FILELIST, 'r') as f:
            return f.read().splitlines()

    def ReadWikiFiles(self):
        name_to_content = {}
        for file in os.listdir(WIKI_PATH):
            name, ext = os.path.splitext(file)
            if ext != '.md':
                continue
            with open(os.path.join(WIKI_PATH, file)) as f:
                name_to_content[name] = f.read()
        return name_to_content

    def ReadHugoFile(self, filename):
        with open(filename) as f:
            filedata = f.read()
        s = filedata.split('---\n', 2)
        if len(s) != 3:
            return None
        (preheader, header, content) = s
        if preheader != '' or content == 0:
            return None
        WIKINAME_RE = re.compile('(?m)^wikiname: (.*)$')
        m = WIKINAME_RE.search(header)
        if not m:
            return None
        return {
            'wikiname': json.loads(m.group(1)),
            'content': content,
            'header': header
        }

    def Run(self):
        self.Info("Opening config file: %s" %
                  click.style(click.format_filename(FILELIST), fg='green'))

        wiki_pages = self.ReadWikiFiles()
        self.Info("%d files read" % len(wiki_pages))

        files_considered = 0
        for root, dirs, files in os.walk(CONTENT_DIR):
            for file in files:
                if os.path.splitext(file)[1] != '.md':
                    continue
                filename = os.path.join(root, file)
                hugo_file = self.ReadHugoFile(filename)
                files_considered += 1
                if not hugo_file:
                    continue
                wikiname = hugo_file['wikiname']
                if wikiname not in wiki_pages:
                    self.Info("Skipping unknown wiki file %s" % wikiname)
                    continue
                if hugo_file['content'] == wiki_pages[wikiname]:
                    self.Info("File %s not changed" % filename)
                    continue
                click.secho("Updating %s with new content." % filename)
                with open(filename, "w") as f:
                    f.write('---\n%s---\n%s' %
                            (hugo_file['header'], wiki_pages[wikiname]))

        self.Info("%d files considered" % files_considered)

        known_pages = set(self.ReadFilelist())
        self.Info("%d known pages" % len(known_pages))
        new_files = set(wiki_pages.keys()) - known_pages
        self.Info("%d new pages" % len(new_files))

        if len(new_files) == 0:
            return

        for file in new_files:
            click.secho("Creating %s." % file)
            title = os.path.splitext(file)[0].replace('-', ' ')
            filename = file + '.md'
            with open(os.path.join(DESTINATION_DIR, filename), 'w') as f:
                f.write('''---
title: %s
wikiname: %s
---
%s''' % (json.dumps(title), json.dumps(file), wiki_pages[file]))

        with open(FILELIST, "w") as f:
            f.write('\n'.join(list(sorted(new_files or known_pages))))


@click.group()
def cli():
    pass


@cli.command()
@click.option('--quiet/--loud',
              default=False,
              help="Don't output anything when nothing happens.")
def updatewiki(quiet):
    WikiUpdater(quiet).Run()


if __name__ == '__main__':
    cli()