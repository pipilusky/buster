"""Ghost Buster. Static site generator for Ghost.

Usage:
  buster.py setup [--gh-repo=<repo-url>] [--dir=<path>]
  buster.py generate [--domain=<local-address>] [--dir=<path>]
  buster.py preview [--dir=<path>]
  buster.py deploy [--dir=<path>]
  buster.py add-domain <domain-name> [--dir=<path>]
  buster.py (-h | --help)
  buster.py --version

Options:
  -h --help                 Show this screen.
  --version                 Show version.
  --dir=<path>              Path of directory to store static pages.
  --domain=<local-address>  Address of local ghost installation [default: local.tryghost.org].
  --gh-repo=<repo-url>      URL of your gh-pages repository.
"""

import os
import re
import shutil
import SocketServer
import SimpleHTTPServer
from docopt import docopt
from time import gmtime, strftime
from git import Repo


def main():
    arguments = docopt(__doc__, version='0.1')
    static_path = arguments.get('dir',
                                os.path.join(os.getcwd(), 'static'))

    if arguments['generate']:
        command = ("wget \\"
                   "--recursive \\"             # follow links to download entire site
                   "--page-requisites \\"       # grab everything: css / inlined images
                   "--domains {0} \\"           # don't grab anything outside ghost
                   "--no-parent \\"             # don't go to parent level
                   "--directory-prefix {1} \\"  # download contents to static/ folder
                   "--no-host-directories \\"   # don't create domain named folder
                   "{0}").format(arguments['--domain'], static_path)

        os.system(command)

    elif arguments['preview']:
        os.chdir(static_path)

        Handler = SimpleHTTPServer.SimpleHTTPRequestHandler
        httpd = SocketServer.TCPServer(("", 9000), Handler)

        print "Serving at port 9000"
        # gracefully handle interrupt here
        httpd.serve_forever()

    elif arguments['setup']:
        if arguments['--gh-repo']:
            repo_url = arguments['--gh-repo']
        else:
            repo_url = raw_input("Enter the Github repository URL:\n").strip()

        # Create a fresh new static files directory
        if os.path.isdir(static_path):
            confirm = raw_input("This will destroy everything inside static/."
                                " Are you sure you want to continue? (y/N)").strip()
            if confirm != 'y' or confirm != 'Y':
                sys.exit(0)
            shutil.rmtree(static_path)

        # User/Organization page -> master branch
        # Project page -> gh-pages branch
        branch = 'gh-pages'
        regex = re.compile(".*[\w-]+\.github\.(?:io|com).*")
        if regex.match(repo_url):
            branch = 'master'

        # Prepare git repository
        repo = Repo.init(static_path)
        git = repo.git

        if branch == 'gh-pages':
            git.checkout(b='gh-pages')
        repo.create_remote('origin', repo_url)

        print "All set! You can generate and deploy now."

    elif arguments['deploy']:
        repo = Repo(static_path)
        repo.git.add('.')

        current_time = strftime("%Y-%m-%d %H:%M:%S", gmtime())
        repo.index.commit('Blog update at {}'.format(current_time))

        origin = repo.remotes.origin
        repo.git.execute(['git', 'push', '-u', origin.name,
                         repo.active_branch.name])
        print "Good job! Deployed to Github Pages."

    elif arguments['add-domain']:
        repo = Repo(static_path)
        custom_domain = arguments['<domain-name>']

        file_path = os.path.join(static_path, 'CNAME')
        with open(file_path, 'w') as f:
            f.write(custom_domain)

        print "Added CNAME file to repo. Use `deploy` to deploy"

if __name__ == '__main__':
    main()
