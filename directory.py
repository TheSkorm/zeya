# -*- coding: utf-8 -*-
#
# Copyright (C) 2009 Samson Yeung, Phil Sung
#
# This file is part of Zeya.
#
# Zeya is free software: you can redistribute it and/or modify it under the
# terms of the GNU Affero General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option) any
# later version.
#
# Zeya is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE. See the GNU Affero General Public License for more
# details.
#
# You should have received a copy of the GNU Affero General Public License
# along with Zeya. If not, see <http://www.gnu.org/licenses/>.


# Directory backend. (Experimental)
#
# Files in the specified directory are read for artist/title/album tag which is
# then saved in a database. The
#
# This is very much work in progress.
#
# Fundamental questions regarding database handling and how to store db info
# have yet to be handled. Also, how to handle new files if the database is
# being reloaded is completely unaddressed.

import os
import tagpy
import pickle

from backend import LibraryBackend

KEY = 'key'
TITLE = 'title'
ARTIST = 'artist'
ALBUM = 'album'

DB = 'db'
KEY_FILENAME = 'key_filename'
MTIMES = 'mtimes'

class DirectoryBackend(LibraryBackend):
    """
    Object that controls access to music in a given directory.
    """
    def __init__(self, media_path, save_db=True):
        self._media_path = media_path
        self._save_db = save_db
        self.db = []
        self.key_filename = {}
        self.mtimes = {}

        self.setup_db()

    def get_db_filename(self):
        return os.path.join(self._media_path, 'zeya.db')

    def setup_db(self):
        if os.path.exists(self.get_db_filename()):
            self.read_db_from_disk()
        self.fill_db()
        if self._save_db:
            self.save_db()

    def read_db_from_disk(self):
        self.info = pickle.load(open(self.get_db_filename(), 'r'))
        self.db = self.info[DB]
        self.key_filename = self.info[KEY_FILENAME]
        self.mtimes = self.info[MTIMES]

        #for path, dirs, files in os.walk(self._media_path):

    def save_db(self):
        self.info = {DB: self.db,
                     MTIMES: self.mtimes,
                     KEY_FILENAME: self.key_filename}
        pickle.dump(self.info, open(self.get_db_filename(), 'wb+'))

    def fill_db(self):
        for path, dirs, files in os.walk(self._media_path):
            for filename in [os.path.abspath(os.path.join(path, filename)) for
                         filename in files]:
                file_mtime = os.stat(filename).st_mtime
                rec_mtime = self.mtimes.get(filename, 0)

                if rec_mtime <= file_mtime:
                    try:
                        tag = tagpy.FileRef(filename).tag()
                    except:
                        # If there was any exception, then ignore the file and
                        # continue. Catching ValueError is sufficient to catch
                        # non-audio but we want to not abort from this.
                        continue

                    # Use simple int as key (sub-optimal, but better than
                    # sending entire path across wire for small db's)
                    next_key = len(self.key_filename)
                    data = {KEY: next_key,
                            ARTIST: tag.artist,
                            TITLE: tag.title,
                            ALBUM: tag.album,
                           }
                    self.db.append(data)
                    self.key_filename[next_key] = filename
                    self.mtimes[filename] = file_mtime

    def get_library_contents(self):
        return self.db

    def get_filename_from_key(self, key):
        return self.key_filename[int(key)]
