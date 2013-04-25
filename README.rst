Shell Grunt
===========

This is a thin wrapper around the excellent watchdog__ library.

__ https://github.com/gorakhargosh/watchdog

Installation
------------

   pip install git+git://github.com/sirver/shell_grunt.git

Usage
-----

This is a script that I use to build one of my projects.

.. code-block:: python

   #!/usr/bin/env python
   # encoding: utf-8

   import os.path

   # Import the main stuff from shell_grunt.
   from shell_grunt import WorkItem, Executor


   # A work item that runs ctags on my code
   class Ctags(WorkItem):
       name = "ctags"

       # command is a method returning what shell command to run.
       command = lambda self, paths: ["ctags", "-R", "src"]

       # How long to wait till the Item is run. This is to consolidate - when
       # many files change quickly, we only want ctags to run once.
       start_delay = 0.9

       # A static method that must return True if this work item should be run
       # given a path of a changed file. We want to run it for all .cc and .h
       # files.
       path_matcher = staticmethod(lambda fn: any(ext in fn for ext in ['.cc', '.h']))

       # Be quiet and do not print any output for this WorkItem.
       report_launch = lambda self: True
       report_finish = lambda self: True

   # A work item that builds my Project.
   class BuildWidelands(WorkItem):
       name = "Building widelands"
       command = lambda selp, paths: ["make", "-j5", "-k"]

       # The stdout and stderr can be found in this file, when the WorkItem is
       # done running.
       output_file = "/tmp/wl_errors.log"

       # This file will gets stdout and stderr of this work item streamed.
       # Useful for tail -f.
       output_stream = "/tmp/wl_errors_stream.log"

       # The working directory for this WorkItem.
       cwd="../widelands.build"
       start_delay = 0.8

       @staticmethod
       def path_matcher(fn):
           extension = os.path.splitext(fn)[-1].lower()
           return extension in [".cc", ".h", ".pyx"]

   if __name__ == "__main__":
       # Main Task: create an Executor, register WorkItems and run it.
       executor = Executor()
       executor.add_item(Ctags)
       executor.add_item(BuildWidelands)
       executor.run()





