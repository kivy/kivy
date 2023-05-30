"""
Changelog parser
================

This generates a changelog from a json file of the PRs of a given milestone,
dumped to json, using the [GitHub CLI](https://github.com/cli/cli).

First, in the command line, create the following alias::

    gh alias set --shell viewMilestone "gh api graphql -F owner='kivy' \
-F name='kivy' -F number=\\$1 -f query='
        query GetMilestones(\\$name: String!, \\$owner: String!, \\$number: \
Int!) {
            repository(owner: \\$owner, name: \\$name) {
                milestone(number: \\$number) {
                    pullRequests(states: MERGED, first: 1000) {
                        nodes {
                            number
                            title
                            labels (first: 25) {
                                nodes {
                                    name
                                }
                            }
                        }
                    }
                }
            }
        }
    '"

Then, log in using ``gh`` and run::

    gh viewMilestone 26 > prs.json

This will generate ``prs.json``. Then, to generate the changelog, run::

    python -m kivy.tools.changelog_parser prs.json changelog.md

to generate a markdown changelog at ``changelog.md``. Then, edit as desired
and paste into the
[changelog here](https://github.com/kivy/kivy/blob/master/doc/sources\
/changelog.rst).
"""
from os.path import exists
import sys
from collections import defaultdict
import json

__all__ = ('process_changelog', )


def write_special_section(fh, items, header):
    items = sorted(items, key=lambda x: x[0])
    if items:
        fh.write(f'{header}\n{"-" * len(header)}\n\n')
        for n, title in items:
            fh.write(f'- [:repo:`{n}`]: {title}\n')
        fh.write('\n')


def process_changelog(filename_in, filename_out):
    if exists(filename_out):
        raise ValueError(
            '{} already exists and would be overwritten'.format(filename_out))

    with open(filename_in, 'r') as fh:
        data = json.load(fh)
    prs = data["data"]["repository"]["milestone"]["pullRequests"]["nodes"]

    bad_pr = False
    grouped = defaultdict(list)
    highlighted = []
    api_breaks = []
    deprecates = []
    for item in prs:
        n = item['number']
        title = item['title']
        labels = [label['name'] for label in item['labels']['nodes']]
        api_break = 'Notes: API-break' in labels
        highlight = 'Notes: Release-highlight' in labels
        deprecated = 'Notes: API-deprecation' in labels
        component_str = 'Component: '
        components = [
            label[len(component_str):]
            for label in labels if label.startswith(component_str)
        ]

        if not components:
            print(f'Found no component label for #{n}')
            bad_pr = True
            continue
        if len(components) > 1:
            print(f'Found more than one component label for #{n}')
            bad_pr = True
            continue

        grouped[components[0]].append((n, title))
        if highlight:
            highlighted.append((n, title))
        if api_break:
            api_breaks.append((n, title))
        if deprecated:
            deprecates.append((n, title))

    if bad_pr:
        raise ValueError(
            'One or more PRs have no, or more than one component label')

    with open(filename_out, 'w') as fh:
        write_special_section(fh, highlighted, 'Highlights')
        write_special_section(fh, deprecates, 'Deprecated')
        write_special_section(fh, api_breaks, 'Breaking changes')

        for group, items in sorted(grouped.items(), key=lambda x: x[0]):
            write_special_section(fh, items, group.capitalize())


if __name__ == '__main__':
    process_changelog(*sys.argv[1:])
