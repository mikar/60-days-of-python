# encoding: utf-8
# TODO: Exclude option
import fnmatch
import logging
import os
import re
import sys
import unicodedata


log = logging.getLogger("fileops")


def configure_logger(loglevel=2, quiet=False):
    "Creates the logger instance and adds handlers and formatting."
    logger = logging.getLogger()

    # Set the loglevel.
    if loglevel > 3:
        loglevel = 3  # Cap at 3 to avoid index errors.
    levels = [logging.ERROR, logging.WARN, logging.INFO, logging.DEBUG]
    logger.setLevel(levels[loglevel])

    logformat = "%(asctime)-14s %(levelname)-8s %(name)-8s %(message)s"

    formatter = logging.Formatter(logformat, "%Y-%m-%d %H:%M:%S")

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    if quiet:
        log.info("Quiet mode: logging disabled.")
        logging.disable(logging.ERROR)


class FileOps(object):

    def __init__(self, quiet=False, verbosity=1,
                 dirsonly=False, filesonly=False, recursive=False,
                 hidden=False, simulate=False, interactive=False, prompt=False,
                 noclobber=False, keepext=False, regex=False, exclude=None,
                 media=False, accents=False, lower=False, upper=False,
                 remdups=False, remext=False, remnonwords=False,
                 ignorecase=False, countpos=None):
        # List of available options.
        self.opts = ("quiet", "verbosity",
                     "dirsonly", "filesonly", "recursive", "hidden",
                     "simulate", "interactive", "prompt", "noclobber",
                     "keepext", "regex", "exclude", "media", "accents",
                     "lower", "upper", "remdups", "remext", "remnonwords",
                     "ignorecase", "countpos",
                     "autostop", "mirror", "spacecheck", "spacemode",
                     "capitalizecheck", "capitalizemode",
                     "insertcheck", "insertpos", "insertedit",
                     "countcheck", "countfill", "countbase", "countpreedit",
                     "countsufedit", "varcheck",
                     "deletecheck", "deletestart", "deleteend",
                     "replacecheck", "sourceedit", "targetedit",)
        # Universal options:
        self._dirsonly = dirsonly  # Only edit directory names.
        self._filesonly = False if dirsonly else filesonly  # Only file names.
        self._recursive = recursive  # Look for files recursively
        self._hidden = hidden  # Look at hidden files and directories, too.
        self._simulate = simulate  # Simulate renaming and dump result to stdout.
        self._interactive = interactive  # Confirm before overwriting.
        self._prompt = prompt  # Confirm all rename actions.
        self._noclobber = noclobber  # Don't overwrite anything.
        self._keepext = keepext  # Don't modify remext.
        self._countpos = countpos  # Adds numerical index at position.
        self._regex = regex  # Use regular expressions instead of glob/fnmatch.
        self._exclude = exclude  # List of strings to exclude from targets.
        self._accents = accents  # Normalize accents (ñé becomes ne).
        self._lower = lower  # Convert target to lowercase.
        self._upper = upper  # Convert target to uppercase.
        self._ignorecase = ignorecase  # Case sensitivity.
        self._media = media  # Mode to sanitize NTFS-filenames/dirnames.
        self._remdups = remdups  # Remove remdups.
        self._remnonwords = remnonwords  # Only allow wordchars (\w)
        self._remext = remext  # Remove all remext.
        # Initialize GUI options.
        self._autostop = False  # Automatically stop execution on rename error.
        self._mirror = False  # Mirror manual rename to all targets.
        self._capitalizecheck = False  # Whether to apply the capitalizemode.
        self._capitalizemode = 0  # 0=lc, 1=uc, 2=flfw, 3=flew
        self._spacecheck = False  # Whether to apply the spacemode.
        self._spacemode = 0  # 0=su, 1=sh, 2=sd, 3=ds, 4=hs, 5=us
        self._countcheck = False  # Wehether to add a counter to the targets.
        self._countbase = 1  # Base to start counting from.
        self._countfill = True  # 9->10: 9 becomes 09. 99->100: 99 becomes 099.
        self._countpreedit = ""  # String that is prepended to the counter.
        self._countsufedit = ""  # String that is appended to the counter.
        self._insertcheck = False  # Whether to apply an insertion.
        self._insertpos = 0  # Position/Index to insert at.
        self._insertedit = ""  # The inserted text/string.
        self._deletecheck = False  # Whether to delete a specified range.
        self._deletestart = 0  # Start index of deletion sequence.
        self._deleteend = 1  # End index of deletion sequence.
        self._replacecheck = True  # Whether to apply source/target patterns.
        self._sourceedit = ""  # Pattern to search for in files/dirs.
        self._targetedit = ""  # Pattern to replace above found matches with.
        self._removecheck = False
        self._varcheck = False  # Whether to apply various options (accents).

        # Create the logger.
        configure_logger(verbosity, quiet)
        self.history = []  # History of commited operations, useful to undo.
        self.defaultopts = {i:getattr(self, "_" + i, None) for i in self.opts}

    def get_options(self, *args):
        if args:
            return {i: getattr(self, i, None) for i in args}
        return {i: getattr(self, i, None) for i in self.opts}

    def set_options(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

    def restore_options(self):
        self.set_options(**self.defaultopts)

    def stage(self, srcpat, destpat, path=None):
        """Initialize the rename operation. Returns list of targets and their
        preview."""
        if not path:
            path = os.getcwd()
        log.debug(path)
        if not srcpat:
            srcpat = "*"
        if not destpat:
            destpat = "*"
        targets = self.find_targets(srcpat, path)
        log.debug("targets found: {}".format(targets))
        modtargets = self.modify_targets(targets, srcpat, destpat)
#         matches = self.match_targets(targets, expression)
#         print matches
        # [i for i, j in zip(a, b) if i != j]

    def splitext(self, files, root, srcpat):
        """Splits a list of files into filename and extension."""
        target = []
        for f in files:
            fname, ext = os.path.splitext(f)
            if self.match(srcpat, fname, ext):
                target.append([root, fname, ext])
        return target

    def joinext(self, target):
        """Joins a target tuple of (name, extension) back together."""
        if len(target) > 2:
            target = (target[1], target[2])
        name = target[0]
        if not self.keepext:
            try:
                name += target[1]
            except IndexError:
                pass
        return name

    def match(self, srcpat, *target):
        """Searches target for pattern and returns a bool."""
        name = self.joinext(target)
        if self.regex:
            if re.search(srcpat, name):
                return True
        else:
            if fnmatch.fnmatch(name, srcpat):
                return True

        return False

    def find_targets(self, srcpat, path):
        """Creates a list of files and/or directories to work with."""
        targets = []
        for root, dirs, files in os.walk(path):
            root += "/"
            root = unicode(root, "utf-8")
            dirs = [unicode(d, "utf-8") for d in dirs]
            files = [unicode(f, "utf-8") for f in files]
            if self.dirsonly:
                target = [[root, d] for d in dirs if self.match(srcpat, d)]
            elif self.filesonly:
                self.splitext(files, root, srcpat)
            else:
                target = [[root, d] for d in dirs if self.match(srcpat, d)]
                target += self.splitext(files, root, srcpat)

            if self.hidden:
                targets.extend(target)
            else:
                targets.extend(i for i in target if not i[1].startswith("."))

            # Do not enter the second loop for non-recursive searches.
            if not self.recursive:
                break

        return targets

    def modify_targets(self, targets, srcpat, destpat):
        # TODO: Handle case sensitivity (re.IGNORECASE)
        if not self.regex:
            srcpat = fnmatch.translate(srcpat)
            destpat = fnmatch.translate(destpat)
        for target in targets:
            name = self.joinext(target)
            srcmatch = re.search(srcpat, name)
            print name, srcpat, srcmatch
            if srcmatch:
                print "found src:", srcmatch.group()
            destmatch = re.search(destpat, name)
            if destmatch:
                print "found dest:", destmatch.group()
            # TODO: Two functions: one to convert a glob into a pattern
            # and another to convert one into a replacement.

#         self._dirsonly = dirsonly  # Only edit directory names.
#         self._filesonly = False if dirsonly else filesonly  # Only file names.
#         self._recursive = recursive  # Look for files recursively
#         self._hidden = hidden  # Look at hidden files and directories, too.
#         self._simulate = simulate  # Simulate renaming and dump result to stdout.
#         self._interactive = interactive  # Confirm before overwriting.
#         self._prompt = prompt  # Confirm all rename actions.
#         self._noclobber = noclobber  # Don't overwrite anything.
#         self._keepext = keepext  # Don't modify remext.
#         self._countpos = count  # Adds numerical index at position.
#         self._regex = regex  # Use regular expressions instead of glob/fnmatch.
#         self._exclude = exclude  # List of strings to exclude from targets.
#         self._accents = accents  # Normalize accents (ñé becomes ne).
#         self._lower = lower  # Convert target to lowercase.
#         self._upper = upper  # Convert target to uppercase.
#         self._ignorecase = ignorecase  # Case sensitivity.
#         self._media = media  # Mode to sanitize NTFS-filenames/dirnames.
#         self._remdups = remdups  # Remove remdups.
#         self._remnonwords = remnonwords  # Remove all chars except [A-Za-z0-9_-.].
#         self._remext = remext  # Remove all remext.
#         # Initialize GUI options.
#         self._autostop = False  # Automatically stop execution on rename error.
#         self._mirror = False  # Mirror manual rename to all targets.
#         self._capitalizecheck = False  # Whether to apply the capitalizemode.
#         self._capitalizemode = 0  # 0=lc, 1=uc, 2=flfw, 3=flew
#         self._spacecheck = False  # Whether to apply the spacemode.
#         self._spacemode = 0  # 0=su, 1=sh, 2=sd, 3=ds, 4=hs, 5=us
#         self._countcheck = False  # Wehether to add a counter to the targets.
#         self._countbase = 1  # Base to start counting from.
#         self._countfill = True  # 9->10: 9 becomes 09. 99->100: 99 becomes 099.
#         self._countpreedit = ""  # String that is prepended to the counter.
#         self._countsufedit = ""  # String that is appended to the counter.
#         self._insertcheck = False  # Whether to apply an insertion.
#         self._insertpos = 0  # Position/Index to insert at.
#         self._insertedit = ""  # The inserted text/string.
#         self._deletecheck = False  # Whether to delete a specified range.
#         self._deletestart = 0  # Start index of deletion sequence.
#         self._deleteend = 1  # End index of deletion sequence.
#         self._replacecheck = True  # Whether to apply source/target patterns.
#         self._sourceedit = ""  # Pattern to search for in files/dirs.
#         self._targetedit = ""  # Pattern to replace above found matches with.
#         self._removecheck = False
#         self._varcheck = False

    def commit(self, targets):
        if self.simulate:
            print "{} to {}".format(targets[1], targets[2])
        # clean up self.exclude

    def undo(self, action):
        pass

    def get_new_path(self, name, path):
        """ Remove file from path, so we have only the dir"""
        dirpath = os.path.split(path)[0]
        if dirpath != '/': dirpath += '/'
        return dirpath + name

    def replace_spaces(self, name, path, mode):
        name = unicode(name, "utf-8")
        path = unicode(path, "utf-8")

        if mode == 0:
            newname = name.replace(' ', '_')
        elif mode == 1:
            newname = name.replace('_', ' ')
        elif mode == 2:
            newname = name.replace(' ', '.')
        elif mode == 3:
            newname = name.replace('.', ' ')
        elif mode == 4:
            newname = name.replace(' ', '-')
        elif mode == 5:
            newname = name.replace('-', ' ')

        newpath = self.get_new_path(newname, path)
        return unicode(newname), unicode(newpath)

    def replace_capitalization(self, name, path, mode):
        name = unicode(name)
        path = unicode(path)

        if mode == 0:
            newname = name.upper()
        elif mode == 1:
            newname = name.lower()
        elif mode == 2:
            newname = name.capitalize()
        elif mode == 3:
            # newname = name.title()
            newname = " ".join([x.capitalize() for x in name.split()])

        newpath = self.get_new_path(newname, path)
        return unicode(newname), unicode(newpath)

    def replace_with(self, name, path, orig, new):
        """ Replace all occurences of orig with new """
        newname = name.replace(orig, new)
        newpath = self.get_new_path(newname, path)

        return unicode(newname), unicode(newpath)

    def replace_accents(self, name, path):
        name = unicode(name)
        path = unicode(path)

        newname = ''.join(c for c in unicodedata.normalize('NFD', name)
                           if unicodedata.category(c) != 'Mn')

        newpath = self.get_new_path(newname, path)
        return unicode(newname), unicode(newpath)

    @property
    def dirsonly(self):
        return self._dirsonly

    @dirsonly.setter
    def dirsonly(self, boolean):
        log.debug("dirsonly: {}".format(boolean))
        self._dirsonly = boolean
        if self.dirsonly:
            self.filesonly = False

    @property
    def filesonly(self):
        return self._filesonly

    @filesonly.setter
    def filesonly(self, boolean):
        log.debug("filesonly: {}".format(boolean))
        self._filesonly = boolean
        if self.filesonly:
            self.dirsonly = False

    @property
    def recursive(self):
        return self._recursive

    @recursive.setter
    def recursive(self, boolean):
        log.debug("recursive: {}".format(boolean))
        self._recursive = boolean

    @property
    def hidden(self):
        return self._hidden

    @hidden.setter
    def hidden(self, boolean):
        log.debug("hidden: {}".format(boolean))
        self._hidden = boolean

    @property
    def simulate(self):
        return self._simulate

    @simulate.setter
    def simulate(self, boolean):
        log.debug("simulate: {}".format(boolean))
        self._simulate = boolean

    @property
    def interactive(self):
        return self._interactive

    @interactive.setter
    def interactive(self, boolean):
        log.debug("interactive: {}".format(boolean))
        self._interactive = boolean

    @property
    def prompt(self):
        return self._prompt

    @prompt.setter
    def prompt(self, boolean):
        log.debug("simulate: {}".format(boolean))
        self._prompt = boolean

    @property
    def noclobber(self):
        return self._noclobber

    @noclobber.setter
    def noclobber(self, boolean):
        log.debug("noclobber: {}".format(boolean))
        self._noclobber = boolean

    @property
    def keepext(self):
        return self._keepext

    @keepext.setter
    def keepext(self, boolean):
        log.debug("keepext: {}.".format(boolean))
        self._keepext = boolean

    @property
    def regex(self):
        return self._regex

    @regex.setter
    def regex(self, boolean):
        log.debug("regex: {}.".format(boolean))
        self._regex = boolean

    @property
    def varcheck(self):
        return self._varcheck

    @varcheck.setter
    def varcheck(self, boolean):
        log.debug("varcheck: {}".format(boolean))
        self._varcheck = boolean

    @property
    def accents(self):
        return self._accents

    @accents.setter
    def accents(self, boolean):
        log.debug("accents: {}".format(boolean))
        self._accents = boolean

    @property
    def exclude(self):
        return self._exclude

    @exclude.setter
    def exclude(self, names):
        log.debug("Excluding {}.".format(names))
        self._exclude = names

    @property
    def autostop(self):
        return self._autostop

    @autostop.setter
    def autostop(self, boolean):
        log.debug("autostop: {}".format(boolean))
        self._autostop = boolean

    @property
    def mirror(self):
        return self._mirror

    @mirror.setter
    def mirror(self, boolean):
        log.debug("mirror: {}".format(boolean))
        self._mirror = boolean

    @property
    def removecheck(self):
        return self._removecheck

    @removecheck.setter
    def removecheck(self, boolean):
        log.debug("removecheck: {}".format(boolean))
        self._removecheck = boolean

    @property
    def remnonwords(self):
        return self._remnonwords

    @remnonwords.setter
    def remnonwords(self, boolean):
        log.debug("remnonwords: {}".format(boolean))
        self._remnonwords = boolean

    @property
    def remext(self):
        return self._remext

    @remext.setter
    def remext(self, boolean):
        log.debug("remext: {}".format(boolean))
        self._remext = boolean

    @property
    def remdups(self):
        return self._remdups

    @remdups.setter
    def remdups(self, boolean):
        log.debug("remdups: {}".format(boolean))
        self._remdups = boolean

    @property
    def lower(self):
        return self._lower

    @lower.setter
    def lower(self, boolean):
        log.debug("lower: {}".format(boolean))
        self._lower = boolean

    @property
    def upper(self):
        return self._upper

    @upper.setter
    def upper(self, boolean):
        log.debug("upper: {}".format(boolean))
        self._upper = boolean

    @property
    def ignorecase(self):
        return self._ignorecase

    @ignorecase.setter
    def ignorecase(self, boolean):
        log.debug("ignorecase: {}".format(boolean))
        self._ignorecase = boolean

    @property
    def nowords(self):
        return self._nowords

    @nowords.setter
    def nowords(self, boolean):
        log.debug("nowords: {}".format(boolean))
        self._nowords = boolean

    @property
    def media(self):
        return self._media

    @media.setter
    def media(self, boolean):
        log.debug("media: {}".format(boolean))
        self._media = boolean

    @property
    def countcheck(self):
        return self._countcheck

    @countcheck.setter
    def countcheck(self, boolean):
        log.debug("countcheck: {}".format(boolean))
        self._countcheck = boolean

    @property
    def countfill(self):
        return self._countfill

    @countfill.setter
    def countfill(self, boolean):
        log.debug("countfill: {}".format(boolean))
        self._countfill = boolean

    @property
    def countpos(self):
        return self._countpos

    @countpos.setter
    def countpos(self, index):
        log.debug("countpos: {}".format(index))
        self._countpos = index

    @property
    def countbase(self):
        return self._countbase

    @countbase.setter
    def countbase(self, num):
        log.debug("countbase: {}".format(num))
        self._countbase = num

    @property
    def countstep(self):
        return self._countstep

    @countstep.setter
    def countstep(self, num):
        log.debug("countstep: {}".format(num))
        self._countstep = num

    @property
    def countpreedit(self):
        return self._countpreedit

    @countpreedit.setter
    def countpreedit(self, text):
        log.debug("countpreedit: {}".format(text))
        self._countpreedit = text

    @property
    def countsufedit(self):
        return self._countsufedit

    @countsufedit.setter
    def countsufedit(self, text):
        log.debug("countsufedit: {}".format(text))
        self._countsufedit = text

    @property
    def insertcheck(self):
        return self._insertcheck

    @insertcheck.setter
    def insertcheck(self, boolean):
        log.debug("insertcheck: {}".format(boolean))
        self._insertcheck = boolean

    @property
    def insertpos(self):
        return self._insertpos

    @insertpos.setter
    def insertpos(self, index):
        log.debug("insertpos: {}".format(index))
        self._insertpos = index

    @property
    def insertedit(self):
        return self._insertedit

    @insertedit.setter
    def insertedit(self, text):
        log.debug("insertedit: {}.".format(text))
        self._insertedit = text

    @property
    def deletecheck(self):
        return self._delete

    @deletecheck.setter
    def deletecheck(self, boolean):
        log.debug("deletecheck: {}".format(boolean))
        self._deletecheck = boolean

    @property
    def deletestart(self):
        return self._deletestart

    @deletestart.setter
    def deletestart(self, index):
        log.debug("deletestart: {}".format(index))
        self._deletestart = index

    @property
    def deleteend(self):
        return self._deleteend

    @deleteend.setter
    def deleteend(self, index):
        log.debug("deleteend: {}".format(index))
        self._deleteend = index

    @property
    def replacecheck(self):
        return self._replacecheck

    @replacecheck.setter
    def replacecheck(self, boolean):
        log.debug("replacecheck: {}".format(boolean))
        self._replacecheck = boolean

    @property
    def sourceedit(self):
        return self._sourceedit

    @sourceedit.setter
    def sourceedit(self, text):
        log.debug("sourceedit: {}.".format(text))
        self._sourceedit = text

    @property
    def targetedit(self):
        return self._targetedit

    @targetedit.setter
    def targetedit(self, text):
        log.debug("targetedit: {}.".format(text))
        self._targetedit = text

    @property
    def capitalizecheck(self):
        return self._capitalizecheck

    @capitalizecheck.setter
    def capitalizecheck(self, boolean):
        log.debug("capitalizecheck: {}".format(boolean))
        self._capitalizecheck = boolean

    @property
    def capitalizemode(self):
        return self._capitalizemode

    @capitalizemode.setter
    def capitalizemode(self, num):
        log.debug("capitalizemode: {}".format(num))
        self._capitalizemode = num

    @property
    def spacecheck(self):
        return self._spacecheck

    @spacecheck.setter
    def spacecheck(self, boolean):
        log.debug("spacecheck: {}".format(boolean))
        self._spacecheck = boolean

    @property
    def spacemode(self):
        return self._spacemode

    @spacemode.setter
    def spacemode(self, num):
        log.debug("spacemode: {}".format(num))
        self._spacemode = num


if __name__ == "__main__":
    fileops = FileOps(hidden=True, recursive=True, keepext=False, regex=False)
    fileops.stage("*.txt", "asdf")
