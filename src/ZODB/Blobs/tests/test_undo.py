##############################################################################
#
# Copyright (c) 2004 Zope Corporation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
import unittest
import tempfile
import os
import shutil
import base64

from ZODB.FileStorage import FileStorage
from ZODB.Blobs.BlobStorage import BlobStorage
from ZODB.Blobs.Blob import Blob
from ZODB.DB import DB
import transaction
from ZODB.Blobs.Blob import Blob

class BlobUndoTests(unittest.TestCase):

    def setUp(self):
        self.storagefile = tempfile.mktemp()
        self.blob_dir = tempfile.mkdtemp()

    def tearDown(self):
        try:
            os.unlink(self.storagefile)
        except (OSError, IOError):
            pass
        shutil.rmtree(self.blob_dir)

    def testUndoWithoutPreviousVersion(self):
        base_storage = FileStorage(self.storagefile)
        blob_storage = BlobStorage(self.blob_dir, base_storage)
        database = DB(blob_storage)
        connection = database.open()
        root = connection.root()
        transaction.begin()
        blob = Blob()
        blob.open('w').write('this is state 1')
        root['blob'] = blob
        transaction.commit()

        serial = base64.encodestring(blob_storage._tid)

        transaction.begin()
        blob_storage.undo(serial, blob_storage._transaction)
        transaction.commit()

        self.assertRaises(KeyError, root.__getitem__, 'blob')

    def testUndo(self):
        base_storage = FileStorage(self.storagefile)
        blob_storage = BlobStorage(self.blob_dir, base_storage)
        database = DB(blob_storage)
        connection = database.open()
        root = connection.root()
        transaction.begin()
        blob = Blob()
        blob.open('w').write('this is state 1')
        root['blob'] = blob
        transaction.commit()

        transaction.begin()
        blob = root['blob']
        blob.open('w').write('this is state 2')
        transaction.commit()

        transaction.begin()
        blob = root['blob']
        self.assertEqual(blob.open('r').read(), 'this is state 2')
        transaction.abort()

        serial = base64.encodestring(blob_storage._tid)

        transaction.begin()
        blob_storage.undo(serial, blob_storage._transaction)
        transaction.commit()

        transaction.begin()
        blob = root['blob']
        self.assertEqual(blob.open('r').read(), 'this is state 1')
        transaction.abort()

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(BlobUndoTests))

    return suite

if __name__ == '__main__':
    unittest.main(defaultTest = 'test_suite')
